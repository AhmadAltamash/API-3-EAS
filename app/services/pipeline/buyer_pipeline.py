from app.models import Buyer

from app.services.website.website_processor import WebsiteProcessor

from app.services.extractor.email_extractor import EmailExtractor
from app.services.extractor.company_extractor import CompanyExtractor
from app.services.extractor.country_extractor import CountryExtractor
from app.services.extractor.phone_extractor import PhoneExtractor

from app.services.filter.relevance_filter import RelevanceFilter


class BuyerPipeline:

    def __init__(self):

        self.processor = WebsiteProcessor()

        self.email = EmailExtractor()

        self.company = CompanyExtractor()

        self.country = CountryExtractor()

        self.phone = PhoneExtractor()

        self.relevance = RelevanceFilter()

    def process(self, search_result, relevance_keywords=None):

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

        # Only keep US/Canada-based buyers with a usable email
        if buyer.country not in ("United States", "Canada"):
            return None

        if not buyer.email:
            return None

        # Only keep buyers that plausibly deal in what our catalogue
        # says we sell (no-op if no catalogue has been uploaded yet).
        # relevance_keywords should be precomputed by the caller when
        # process() runs inside a worker thread (see BuyerPipeline
        # docstring / SearchManager) - querying the DB from in here
        # requires an app context that worker threads don't have.
        if not self.relevance.is_relevant(
            buyer,
            clean_text,
            keywords=relevance_keywords
        ):
            return None

        return buyer
    