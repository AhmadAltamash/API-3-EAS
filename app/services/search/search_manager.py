from concurrent.futures import ThreadPoolExecutor, as_completed

from .google_search import GoogleSearch
from .facebook_search import FacebookSearch
from .linkedin_search import LinkedInSearch
from .directory_search import DirectorySearch
from .website_search import WebsiteSearch

from app.services.pipeline.buyer_pipeline import BuyerPipeline
from app.services.filter.result_filter import ResultFilter


class SearchManager:

    # Website fetches are I/O-bound (waiting on network), so a thread pool
    # gives a big speedup over processing results one at a time.
    MAX_WORKERS = 20

    def __init__(self):

        self.adapters = {
            "google": GoogleSearch(),
            "facebook": FacebookSearch(),
            "linkedin": LinkedInSearch(),
            "directory": DirectorySearch(),
            "website": WebsiteSearch(),
        }

    def search(self, source, keyword):

        all_results = []

        if source == "all":

            # Query every source adapter concurrently too, since each one
            # makes its own outbound search request.
            with ThreadPoolExecutor(max_workers=len(self.adapters)) as executor:

                futures = [
                    executor.submit(adapter.search, keyword)
                    for adapter in self.adapters.values()
                ]

                for future in as_completed(futures):

                    try:
                        all_results.extend(future.result())
                    except Exception as e:
                        print(f"[SearchManager] source error: {e}")

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

        # Process each candidate (fetch website, extract, classify US/email)
        # in parallel - this is the step that used to run one URL at a time.
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:

            futures = {
                executor.submit(BuyerPipeline().process, result): result
                for result in search_results
            }

            for future in as_completed(futures):

                try:

                    buyer = future.result()

                    if buyer:
                        buyers.append(buyer)

                except Exception as e:
                    print(f"[SearchManager] pipeline error: {e}")

        return buyers