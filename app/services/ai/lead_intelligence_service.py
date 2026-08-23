import json
import re
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from google import genai

from config import Config

from app.services.website.html_fetcher import HTMLFetcher
from app.services.website.html_cleaner import HTMLCleaner
from app.services.database.catalogue_profile_repository import CatalogueProfileRepository


class LeadIntelligenceService:
    """
    Produces the structured "why is this a good/bad prospect" profile
    for a single buyer:

      - product/style match against our uploaded catalogue (AI)
      - a named decision-maker, scanned from the site itself (not AI -
        pattern matching, so it's either found for real or not found;
        never guessed)
      - whether the contact email's domain can actually receive mail
        (MX record check - "domain-verified", not full mailbox
        verification, which needs a paid API)
      - an explainable lead score built from simple, disclosed rules,
        not an opaque AI number
    """

    MODEL = "gemini-3.5-flash"

    MAX_RETRIES = 3

    RETRYABLE_MARKERS = (
        "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded"
    )

    # Roles worth calling out as a "decision-maker" rather than a
    # generic contact - purchasing-side titles specifically, per the
    # brief (buyer, purchasing/procurement/sourcing/category/merchandise/
    # import manager, or an owner/founder at a small company).
    DECISION_MAKER_TITLES = [
        "Purchasing Manager", "Procurement Manager", "Sourcing Manager",
        "Category Manager", "Merchandise Manager", "Import Manager",
        "Buyer", "Owner", "Co-Founder", "Founder", "President", "CEO",
    ]

    _TITLE_PATTERN = "|".join(re.escape(t) for t in DECISION_MAKER_TITLES)

    # "Jane Smith, Purchasing Manager" / "Jane Smith - Buyer"
    NAME_THEN_TITLE = re.compile(
        r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\s*[,\-\u2013\u2014:]\s*("
        + _TITLE_PATTERN + r")\b"
    )

    # "Purchasing Manager: Jane Smith" / "Buyer - Jane Smith"
    TITLE_THEN_NAME = re.compile(
        r"\b(" + _TITLE_PATTERN
        + r")\s*[,\-\u2013\u2014:]\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\b"
    )

    ABOUT_LINK_KEYWORDS = [
        "about", "team", "our-team", "staff", "management",
        "leadership", "contact", "who-we-are"
    ]

    BUYER_SIDE_CATEGORIES = {"Wholesaler", "Distributor", "Retailer", "Importer"}
    SELLER_SIDE_CATEGORIES = {"Manufacturer", "Exporter"}

    def __init__(self):

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)

        self.fetcher = HTMLFetcher()
        self.cleaner = HTMLCleaner()

        self.catalogue_repo = CatalogueProfileRepository()

    # -------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------

    def analyze(self, buyer):

        raw_html = self.fetcher.fetch(buyer.website) if buyer.website else ""
        clean_text = self.cleaner.clean(raw_html) if raw_html else ""

        about_text = self._fetch_about_page_text(raw_html, buyer.website)

        decision_maker = self._find_decision_maker(
            clean_text + "\n" + about_text
        )

        email_verified = self._check_mx(buyer.email)

        catalogue = self.catalogue_repo.get()

        ai_profile = self._analyze_product_match(
            buyer, clean_text, catalogue
        )

        score, reasons, priority = self._compute_score(
            product_match_percent=ai_profile.get("product_match_percent"),
            category=buyer.category,
            decision_maker=decision_maker,
            email_verified=email_verified,
            has_catalogue=catalogue is not None,
        )

        return {
            "product_match_percent": ai_profile.get("product_match_percent"),
            "relevant_categories": ai_profile.get("relevant_categories", []),
            "style_estimate": ai_profile.get("style"),
            "positioning_estimate": ai_profile.get("positioning"),
            "recommended_products": ai_profile.get("recommended_products", []),
            "decision_maker_name": decision_maker["name"] if decision_maker else None,
            "decision_maker_title": decision_maker["title"] if decision_maker else None,
            "email_domain_verified": email_verified,
            "lead_score": score,
            "lead_score_reasons": reasons,
            "outreach_priority": priority,
        }

    # -------------------------------------------------------------
    # Decision-maker scan (pattern matching, not AI - either it's
    # genuinely on the page or it isn't)
    # -------------------------------------------------------------

    def _fetch_about_page_text(self, homepage_html, base_url):

        if not homepage_html or not base_url:
            return ""

        link = self._find_about_link(homepage_html, base_url)

        if not link:
            return ""

        html = self.fetcher.fetch(link)

        return self.cleaner.clean(html) if html else ""

    def _find_about_link(self, html, base_url):

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            return None

        base_domain = urlparse(base_url).netloc.lower()

        for a in soup.find_all("a", href=True):

            href = a["href"].strip()

            if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
                continue

            link_text = (a.get_text() or "").strip().lower()
            href_lower = href.lower()

            if not any(
                kw in href_lower or kw in link_text
                for kw in self.ABOUT_LINK_KEYWORDS
            ):
                continue

            absolute = urljoin(base_url, href)

            if urlparse(absolute).netloc.lower() != base_domain:
                continue

            return absolute

        return None

    def _find_decision_maker(self, text):

        if not text:
            return None

        match = self.NAME_THEN_TITLE.search(text)

        if match:
            return {
                "name": match.group(1).strip(),
                "title": self._normalize_title(match.group(2))
            }

        match = self.TITLE_THEN_NAME.search(text)

        if match:
            return {
                "name": match.group(2).strip(),
                "title": self._normalize_title(match.group(1))
            }

        return None

    def _normalize_title(self, raw_title):

        raw_lower = raw_title.strip().lower()

        for canonical in self.DECISION_MAKER_TITLES:
            if canonical.lower() == raw_lower:
                return canonical

        return raw_title.strip()

    # -------------------------------------------------------------
    # Email domain verification (MX record - "can this domain receive
    # mail at all", not full mailbox verification)
    # -------------------------------------------------------------

    def _check_mx(self, email):

        if not email or "@" not in email:
            return False

        domain = email.split("@")[-1].strip()

        if not domain:
            return False

        try:
            import dns.resolver
        except ImportError:
            print("[lead intelligence] dnspython not installed - skipping MX check")
            return False

        try:
            answers = dns.resolver.resolve(domain, "MX", lifetime=5)
            return len(answers) > 0
        except Exception:
            return False

    # -------------------------------------------------------------
    # AI product/style match against our catalogue
    # -------------------------------------------------------------

    def _analyze_product_match(self, buyer, site_text, catalogue):

        if not catalogue or not (catalogue.products or catalogue.categories):
            # No catalogue uploaded yet - nothing to compare against.
            return {}

        if not site_text:
            return {}

        prompt = f"""
        You are a B2B buyer-qualification analyst.

        OUR CATALOGUE:
        Products: {catalogue.products}
        Categories: {catalogue.categories}
        Materials: {catalogue.materials or "unspecified"}

        PROSPECT COMPANY: {buyer.company}
        PROSPECT WEBSITE CONTENT:
        \"\"\"
        {site_text[:8000]}
        \"\"\"

        Assess how well this prospect fits as a BUYER of our catalogue
        (not as a competitor selling the same thing).

        Respond with ONLY valid JSON, exactly matching this structure
        (no markdown fences, no commentary):

        {{
          "product_match_percent": <integer 0-100>,
          "relevant_categories": ["...", "..."],
          "style": "...",
          "positioning": "Budget" | "Mid-Market" | "Mid-Premium" | "Premium" | "Unknown",
          "recommended_products": ["...", "..."]
        }}
        """

        try:
            raw = self._generate_with_retry(prompt)
            data = self._parse_json(raw)
        except Exception as e:
            print(f"[lead intelligence] product-match analysis failed: {e}")
            return {}

        data.setdefault("relevant_categories", [])
        data.setdefault("recommended_products", [])

        return data

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
                    marker in error_text for marker in self.RETRYABLE_MARKERS
                )

                if not is_retryable or attempt == self.MAX_RETRIES:
                    break

                time.sleep(2 ** attempt)

        raise ValueError(f"AI service unavailable: {last_error}")

    def _parse_json(self, raw_text):

        cleaned = raw_text.strip()

        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:

            match = re.search(r"\{.*\}", cleaned, re.DOTALL)

            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

            raise ValueError("AI response wasn't valid JSON")

    # -------------------------------------------------------------
    # Explainable lead scoring
    # -------------------------------------------------------------

    def _compute_score(
        self,
        product_match_percent,
        category,
        decision_maker,
        email_verified,
        has_catalogue,
    ):

        reasons = []
        score = 0

        # Product match - up to 40 pts
        if has_catalogue and product_match_percent is not None:

            points = round(product_match_percent * 0.4)
            score += points

            reasons.append(
                f"Product match: {product_match_percent}% \u2192 +{points} pts"
            )

        else:

            reasons.append(
                "No catalogue uploaded (or site content unavailable) - "
                "product match not scored (+0 pts)"
            )

        # Business type fit - up to 30 pts
        if category in self.BUYER_SIDE_CATEGORIES:

            score += 30

            reasons.append(
                f"Business type: {category} (a buyer-side company) \u2192 +30 pts"
            )

        elif category in self.SELLER_SIDE_CATEGORIES:

            score += 5

            reasons.append(
                f"Business type: {category} (likely a competitor, not a "
                f"buyer) \u2192 +5 pts"
            )

        else:

            score += 15

            reasons.append(
                f"Business type: {category or 'Unknown'} \u2192 +15 pts"
            )

        # Decision-maker found - up to 20 pts
        if decision_maker:

            score += 20

            reasons.append(
                f"Named decision-maker found: {decision_maker['name']}, "
                f"{decision_maker['title']} \u2192 +20 pts"
            )

        else:

            score += 5

            reasons.append(
                "No named decision-maker found on site - generic contact "
                "only \u2192 +5 pts"
            )

        # Email domain verified - up to 10 pts
        if email_verified:

            score += 10

            reasons.append(
                "Business email domain verified (MX records found) "
                "\u2192 +10 pts"
            )

        else:

            reasons.append(
                "Email domain could not be verified \u2192 +0 pts"
            )

        score = max(0, min(100, score))

        if score >= 70:
            priority = "HIGH"
        elif score >= 40:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return score, reasons, priority
