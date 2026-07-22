from app.models import Buyer

from app.services.website.website_processor import WebsiteProcessor

from app.services.extractor.email_extractor import EmailExtractor
from app.services.extractor.company_extractor import CompanyExtractor
from app.services.extractor.country_extractor import CountryExtractor


class BuyerPipeline:

    def __init__(self):

        self.processor = WebsiteProcessor()

        self.email = EmailExtractor()

        self.company = CompanyExtractor()

        self.country = CountryExtractor()

    def process(self, search_result):

        buyer = Buyer()

        buyer.company = search_result.title
        buyer.website = search_result.url
        buyer.snippet = search_result.snippet
        buyer.source = search_result.source

        html = self.processor.process(
            buyer.website
        )

        buyer = self.company.extract(
            buyer,
            html
        )

        buyer = self.email.extract(
            buyer,
            html
        )

        buyer = self.country.extract(
            buyer,
            html
        )

        return buyer
    