from .google_search import GoogleSearch
from .facebook_search import FacebookSearch
from .linkedin_search import LinkedInSearch
from .directory_search import DirectorySearch
from .website_search import WebsiteSearch

from app.services.pipeline.buyer_pipeline import BuyerPipeline
from app.services.filter.result_filter import ResultFilter

class SearchManager:

    def __init__(self):

        self.adapters = {
            "google": GoogleSearch(),
            "facebook": FacebookSearch(),
            "linkedin": LinkedInSearch(),
            "directory": DirectorySearch(),
            "website": WebsiteSearch(),
        }

    def search(self, source, keyword):

        adapter = self.adapters.get(source)

        if adapter is None:
            return []

        search_results = adapter.search(keyword)

        search_results = ResultFilter().filter(search_results)

        pipeline = BuyerPipeline()

        buyers = []

        for result in search_results:
            buyers.append(
                pipeline.process(result)
            )

        return buyers