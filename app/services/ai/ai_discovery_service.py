import json
import re
import time

from google import genai
from config import Config

from app.models import Buyer
from app.services.database.catalogue_profile_repository import (
    CatalogueProfileRepository
)
from app.services.database.buyer_repository import BuyerRepository
from app.services.search.google_search import GoogleSearch
from app.services.search.search_result import SearchResult
from app.services.pipeline.buyer_pipeline import BuyerPipeline
from app.services.filter.relevance_filter import RelevanceFilter


class AIDiscoveryService:
    """
    A second, SEPARATE lead-discovery path from the existing /search
    page - doesn't touch or replace it.

    /search only ever finds a company if it shows up in a search-engine
    result page or a directory listing, which is exactly why it runs dry
    over time (once those sources are exhausted for a keyword, there's
    nothing left to find). This asks Gemini - which this project already
    has wired up and paying for via Config.GEMINI_API_KEY, no new cost -
    to name real, well-known companies it already knows about in the
    target category/buyer-type. That's the actual mechanism behind
    "someone manually asked ChatGPT/Gemini for a list of real buyers" -
    just done through the API instead of by hand.

    Deliberately treats the AI as untrustworthy for email addresses BY
    DEFAULT. Gemini only supplies a candidate COMPANY NAME (and a
    website guess when confident). Every candidate is first run through
    the exact same website-fetch -> real regex email/phone extraction ->
    relevance filter -> dedup-aware save pipeline the rest of the app
    already uses - so the default path for every email that reaches the
    database is that this app actually scraped it off a real, live page.

    The one deliberate exception: some real, major companies (the exact
    kind Gemini confidently names) run bot-blocking on their site that
    this app's fetcher can't get past - that's a live-fetch failure, not
    evidence the company or its published trade email is fake. For
    those cases, a SEPARATE, focused question is asked about that one
    company's known trade email (batch-naming and detailed-recall are
    kept as two different prompts on purpose - bundling them makes the
    model hedge and default to leaving email blank). If it has genuine
    knowledge, that AI-recalled email is used as a fallback - but it is
    saved with email_live_verified=False and a visibly different
    status/source, never silently presented as verified.
    """

    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    # Cheaper/higher-throughput tier, same choice already made for the
    # classification step elsewhere in this project - this task (name
    # some real companies) doesn't need the flagship model.
    MODEL = "gemini-3.5-flash-lite"

    MAX_RETRIES = 3

    RETRYABLE_MARKERS = (
        "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded"
    )

    def __init__(self, catalogue_repo=None, buyer_repo=None):

        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY
        )

        self.catalogue_repo = catalogue_repo or CatalogueProfileRepository()

        self.buyers = buyer_repo or BuyerRepository()

        self.google_search = GoogleSearch()

        self.pipeline = BuyerPipeline()

        self.relevance = RelevanceFilter()

    def discover(self, buyer_type_hint=None, batch_size=12):
        """
        Returns:
        {
            "new_count": int,
            "duplicate_count": int,
            "skipped_count": int,
            "details": [
                {"company", "website", "email", "status", "verified"}, ...
            ]
        }
        status is one of "saved" / "duplicate" / "skipped".
        "verified" is True only when this app fetched the live page
        itself and found the email there; False means it came from
        Gemini's own knowledge because the live fetch failed (usually
        the target site blocking automated requests) - still shown,
        never silently indistinguishable from a confirmed lead.
        """

        profile = self.catalogue_repo.get()

        if not profile or not (profile.products or profile.categories):
            raise ValueError(
                "Upload a catalogue first (Catalogue Analyzer page) so "
                "there's something to base this on."
            )

        prompt = self._build_prompt(profile, buyer_type_hint, batch_size)

        raw_text = self._generate_with_retry(prompt)

        candidates = self._parse_json(raw_text)

        relevance_keywords = self.relevance.get_keywords()

        details = []

        new_count = 0
        duplicate_count = 0
        skipped_count = 0

        for candidate in candidates:

            company_name = (candidate.get("company") or "").strip()

            website = (candidate.get("website") or "").strip()

            ai_email = (candidate.get("email") or "").strip().lower()

            if ai_email and not self.EMAIL_PATTERN.match(ai_email):
                ai_email = ""

            if not company_name:
                continue

            if not website:
                website = self._resolve_website(company_name)

            if not website:

                details.append({
                    "company": company_name,
                    "website": None,
                    "email": None,
                    "status": "skipped",
                    "verified": None
                })

                skipped_count += 1

                continue

            search_result = SearchResult(
                title=company_name,
                url=website,
                snippet=candidate.get("reason", ""),
                source="AI Discovery"
            )

            buyer = self.pipeline.process(
                search_result,
                relevance_keywords=relevance_keywords
            )

            # Live fetch failed (often the site blocking automated
            # requests, not evidence the company/email is fake) - fall
            # back to the AI's own knowledge. First check whether it
            # already volunteered one in the batch response; if not,
            # ask about THIS ONE company specifically - a single,
            # focused question gets a far more confident answer than
            # "also maybe include an email" buried inside a 12-company
            # batch request, where the model tends to hedge and leave
            # it blank by default.
            fallback_email = ai_email

            if not buyer and not fallback_email:
                fallback_email = self._lookup_known_email(
                    company_name, website
                )

            if not buyer and fallback_email:

                buyer = Buyer(
                    company=company_name,
                    email=fallback_email,
                    website=website,
                    snippet=candidate.get("reason", ""),
                    source="AI Discovery (Unverified)",
                    category="AI Discovery",
                    email_live_verified=False
                )

            if not buyer:

                details.append({
                    "company": company_name,
                    "website": website,
                    "email": None,
                    "status": "skipped",
                    "verified": None
                })

                skipped_count += 1

                continue

            saved, is_new = self.buyers.save(buyer)

            details.append({
                "company": saved.company,
                "website": saved.website,
                "email": saved.email,
                "status": "saved" if is_new else "duplicate",
                "verified": saved.email_live_verified
            })

            if is_new:
                new_count += 1
            else:
                duplicate_count += 1

        return {
            "new_count": new_count,
            "duplicate_count": duplicate_count,
            "skipped_count": skipped_count,
            "details": details
        }

    def _lookup_known_email(self, company_name, website):
        """
        A single, focused question about ONE company - deliberately
        separate from the batch-naming prompt above, because asking
        for 12 companies AND their contact details in one shot makes
        the model hedge and leave email blank almost every time, even
        for companies (Anthropologie, CB2, Williams-Sonoma...) whose
        published trade email it likely does know. Isolating the
        question gets a meaningfully more confident answer.

        Returns a validated email string, or None if the model doesn't
        have genuine knowledge of one (an "UNKNOWN" answer is the
        expected, common case - not a failure) or if the call itself
        fails - one candidate's lookup failing should never take down
        the rest of the batch.
        """

        prompt = f"""
        Company: {company_name}
        Website: {website}

        Do you have specific, genuine knowledge of a real, publicly-
        published trade/wholesale contact EMAIL ADDRESS for this exact
        company - the kind that appears on their own site's trade
        program page, in press materials, or industry directories?

        Rules:
        - If yes, respond with ONLY that email address and nothing else.
        - If you do not have specific, genuine knowledge - or you would
          only be constructing a plausible-looking guess such as
          "info@" or "trade@" plus their domain - respond with exactly:
          UNKNOWN
        - UNKNOWN is a completely normal, expected answer for most
          companies. Only answer with an address you are confident is
          real and correct.
        """

        try:
            raw_text = self._generate_with_retry(prompt)
        except ValueError:
            return None

        candidate_email = raw_text.strip().strip('"').lower()

        if candidate_email == "unknown":
            return None

        if self.EMAIL_PATTERN.match(candidate_email):
            return candidate_email

        return None

    def _resolve_website(self, company_name):
        """
        Gemini named a company but wasn't confident of the domain - one
        targeted real web search to find it, reusing the existing
        Google adapter rather than inventing a URL.
        """

        results = self.google_search.search(f'"{company_name}" official site')

        for result in results:

            if result.url and result.url.startswith("http"):
                return result.url

        return None

    def _build_prompt(self, profile, buyer_type_hint, batch_size):

        products = profile.products or ""

        categories = profile.categories or ""

        buyer_type_line = (
            f'Focus specifically on this kind of buyer: "{buyer_type_hint}".'
            if buyer_type_hint else
            "Cover a sensible spread of different buyer types yourself "
            "(retailers with trade programs, boutique hotels/spas, event "
            "planners/rental companies, interior design studios, gift "
            "shops, etc) rather than just one kind."
        )

        return f"""
        You are a B2B export sales researcher helping a small exporter
        find REAL companies in the UNITED STATES and CANADA who would
        plausibly buy the following products:

        Products: {products}
        Categories: {categories}

        {buyer_type_line}

        List {batch_size} REAL, well-known companies you have genuine
        knowledge of - not invented or generic-sounding names. For each
        one, only include a "website" field if you are genuinely
        confident of the exact domain; leave it blank (empty string)
        otherwise rather than guessing.

        For the "email" field: leave it blank (empty string) for almost
        every company - most of the time you do not actually know a
        specific real contact address, and a plausible-looking guess is
        worse than nothing. ONLY fill it in for a MAJOR, very well-known
        company where you have specific, genuine knowledge of a real,
        publicly-published trade/wholesale contact address (the kind of
        thing that appears on the company's own site and in press/
        industry sources) - not a guessed pattern like "info@" or
        "trade@" plus their domain. When in doubt, leave it blank.

        CRITICAL RULES:
        - Never fill in a phone number or contact person.
        - Do NOT invent companies that don't actually exist.
        - Do NOT guess or pattern-match an email - only include one you
          have genuine, specific knowledge of.
        - Every company must be based in, or have retail/trade presence
          in, the United States or Canada.

        Respond with ONLY valid JSON (no markdown fences, no commentary,
        no trailing commas), exactly matching this structure:

        [
          {{"company": "...", "website": "https://... or empty string", "email": "only if genuinely known, else empty string", "reason": "one short phrase on why this company fits"}}
        ]
        """

    def _generate_with_retry(self, prompt):

        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):

            try:

                response = self.client.models.generate_content(
                    model=self.MODEL,
                    contents=prompt
                )

                return response.text or ""

            except Exception as e:

                last_error = e

                error_text = str(e)

                is_retryable = any(
                    marker in error_text
                    for marker in self.RETRYABLE_MARKERS
                )

                print(f"AI Discovery error (attempt {attempt}/{self.MAX_RETRIES}):", e)

                if not is_retryable or attempt == self.MAX_RETRIES:
                    break

                time.sleep(2 ** attempt)

        raise ValueError(
            f"The AI service is temporarily unavailable. Please try again "
            f"in a moment. ({last_error})"
        )

    def _parse_json(self, raw_text):

        cleaned = raw_text.strip()

        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:

            match = re.search(r"\[.*\]", cleaned, re.DOTALL)

            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    raise ValueError(
                        "The AI service returned an unexpected response. "
                        "Please try again."
                    )
            else:
                raise ValueError(
                    "The AI service returned an unexpected response. "
                    "Please try again."
                )

        if not isinstance(data, list):
            raise ValueError(
                "The AI service returned an unexpected response format. "
                "Please try again."
            )

        return data
