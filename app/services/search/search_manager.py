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

        pipeline = BuyerPipeline()

        all_results = []

        if source == "all":

            for adapter in self.adapters.values():
                all_results.extend(adapter.search(keyword))

        else:

            adapter = self.adapters.get(source)

            if adapter is None:
                return []

            all_results = adapter.search(keyword)

        # Remove duplicate URLs
        unique = {}

        for result in all_results:
            if result.url and result.url not in unique:
                unique[result.url] = result

        search_results = list(unique.values())

        search_results = ResultFilter().filter(search_results)

        buyers = []

        for result in search_results:

            buyer = pipeline.process(result)

            if buyer:
                buyers.append(buyer)

        return buyers