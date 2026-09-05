from urllib.parse import urljoin, urlparse

from app.models import Buyer

from app.services.website.website_processor import WebsiteProcessor

from app.services.extractor.email_extractor import EmailExtractor
from app.services.extractor.company_extractor import CompanyExtractor
from app.services.extractor.country_extractor import CountryExtractor
from app.services.extractor.phone_extractor import PhoneExtractor

from app.services.filter.relevance_filter import RelevanceFilter
from app.services.search.search_result import SearchResult


class BuyerPipeline:

    # A search hit that links out to this many DISTINCT other company
    # domains is treated as a directory/aggregator listing, not a real
    # company's own homepage - a genuine small business site almost
    # never links to 8+ other unrelated companies, so this is a fairly
    # low-false-positive signal on its own.
    DIRECTORY_DOMAIN_THRESHOLD = 8

    # How many of a directory's listed companies to actually try -
    # bounded so one directory hit can't balloon into dozens of extra
    # fetches; tune down further if a run feels slow.
    MAX_DIRECTORY_CANDIDATES = 3

    # Common non-company domains that show up in nav/footer/share links
    # on almost every site - never worth treating as a "listed company".
    SKIP_DOMAINS = {
        "facebook.com", "twitter.com", "x.com", "instagram.com",
        "linkedin.com", "youtube.com", "pinterest.com", "tiktok.com",
        "google.com", "goo.gl", "maps.google.com", "apple.com",
        "wikipedia.org", "wa.me", "whatsapp.com", "amazon.com"
    }

    def __init__(self):

        self.processor = WebsiteProcessor()

        self.email = EmailExtractor()

        self.company = CompanyExtractor()

        self.country = CountryExtractor()

        self.phone = PhoneExtractor()

        self.relevance = RelevanceFilter()

    def process(self, search_result, relevance_keywords=None, allow_directory_hop=True):

        buyer = Buyer()

        buyer.company = search_result.title
        buyer.website = search_result.url
        buyer.snippet = search_result.snippet
        buyer.source = search_result.source

        raw_html, clean_text = self.processor.process(
            buyer.website
        )

        buyer = self.company.extract(
            buyer,
            raw_html
        )

        buyer = self.email.extract(
            buyer,
            clean_text
        )

        buyer = self.country.extract(
            buyer,
            clean_text
        )

        buyer = self.phone.extract(
            buyer,
            raw_html
        )

        # Only keep US/Canada-based buyers with a usable email. A
        # directory/aggregator page will usually fail BOTH of these -
        # it has no country of its own and no single company's email -
        # so the directory-hop check has to happen here, before giving
        # up, not after either check individually.
        found_valid_buyer = (
            buyer.country in ("United States", "Canada")
            and bool(buyer.email)
        )

        if not found_valid_buyer:

            # Before giving up, check whether this page is actually a
            # directory/aggregator LISTING many other companies rather
            # than a company page itself. If so, try a bounded number
            # of the companies it actually links to instead. Bounded to
            # a single hop (allow_directory_hop is turned off for the
            # recursive call) so a directory that happens to link to
            # another directory can't chain into unbounded fetching.
            if allow_directory_hop and self._looks_like_directory(raw_html, buyer.website):

                for candidate_url in self._extract_candidate_links(raw_html, buyer.website):

                    candidate_result = SearchResult(
                        title=candidate_url,
                        url=candidate_url,
                        snippet=f"Found via directory listing: {search_result.title}",
                        source=search_result.source
                    )

                    candidate_buyer = self.process(
                        candidate_result,
                        relevance_keywords=relevance_keywords,
                        allow_directory_hop=False
                    )

                    if candidate_buyer:
                        return candidate_buyer

            return None

        # We only reach here with a real email this app found by
        # fetching the live page itself - mark it as such so the
        # database can distinguish this from an AI-recalled or
        # manually-imported address later.
        buyer.email_live_verified = True

        # Score how well this buyer plausibly matches what our
        # catalogue says we sell (None if no catalogue has been
        # uploaded yet - a no-op, keep everyone, same as before).
        # relevance_keywords should be precomputed by the caller when
        # process() runs inside a worker thread (see BuyerPipeline
        # docstring / SearchManager) - querying the DB from in here
        # requires an app context that worker threads don't have.
        #
        # Only a genuine zero (catalogue exists, but not one keyword
        # matched anywhere) gets rejected - a weak-but-real match is
        # kept, scored, and visible, instead of being silently thrown
        # away the way the old True/False version would still have
        # kept it (>=1 keyword) but without ever recording HOW
        # relevant it actually was.
        relevance_score = self.relevance.score(
            buyer,
            clean_text,
            keywords=relevance_keywords
        )

        if relevance_score is not None:

            buyer.product_match_percent = relevance_score

            if relevance_score == 0:
                return None

        return buyer

    def _domain(self, url):

        try:

            netloc = urlparse(url).netloc.lower()

            return netloc[4:] if netloc.startswith("www.") else netloc

        except Exception:
            return ""

    def _looks_like_directory(self, raw_html, base_url):

        if not raw_html:
            return False

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_html, "lxml")
        except Exception:
            return False

        base_domain = self._domain(base_url)

        external_domains = set()

        for link in soup.find_all("a", href=True):

            href = link["href"].strip()

            if not href or href.startswith(("#", "mailto:", "tel:")):
                continue

            domain = self._domain(urljoin(base_url, href))

            if domain and domain != base_domain and domain not in self.SKIP_DOMAINS:
                external_domains.add(domain)

        return len(external_domains) >= self.DIRECTORY_DOMAIN_THRESHOLD

    def _extract_candidate_links(self, raw_html, base_url):

        if not raw_html:
            return []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_html, "lxml")
        except Exception:
            return []

        base_domain = self._domain(base_url)

        seen_domains = set()
        candidates = []

        for link in soup.find_all("a", href=True):

            if len(candidates) >= self.MAX_DIRECTORY_CANDIDATES:
                break

            href = link["href"].strip()

            if not href or href.startswith(("#", "mailto:", "tel:")):
                continue

            absolute = urljoin(base_url, href)

            domain = self._domain(absolute)

            if not domain or domain == base_domain or domain in self.SKIP_DOMAINS:
                continue

            if domain in seen_domains:
                continue

            seen_domains.add(domain)

            candidates.append(absolute)

        return candidates