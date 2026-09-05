from concurrent.futures import ThreadPoolExecutor, as_completed

from .google_search import GoogleSearch
from .facebook_search import FacebookSearch
from .linkedin_search import LinkedInSearch
from .directory_search import DirectorySearch
from .website_search import WebsiteSearch
from .serpapi_search import SerpApiSearch

from app.services.pipeline.buyer_pipeline import BuyerPipeline
from app.services.filter.result_filter import ResultFilter
from app.services.filter.relevance_filter import RelevanceFilter


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

        # Kept OUT of self.adapters on purpose - "all" fans out across
        # every adapter in that dict, and SerpApi's free tier is a
        # scarce 250/month. Only spend one of those credits when the
        # source is explicitly chosen, never as a side effect of a
        # routine "All Sources" search.
        self.serpapi = SerpApiSearch()

    def search(self, source, keyword):

        all_results = []

        if source == "serpapi":

            all_results = self.serpapi.search(keyword)

        elif source == "all":

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

        # Load catalogue keywords ONCE here, in the request thread
        # (has the Flask app context) - not inside the worker pool
        # below, which doesn't. This also avoids re-querying the DB
        # once per candidate.
        relevance_keywords = RelevanceFilter().get_keywords()

        # Process each candidate (fetch website, extract, classify US/email)
        # in parallel - this is the step that used to run one URL at a time.
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:

            futures = {
                executor.submit(
                    BuyerPipeline().process,
                    result,
                    relevance_keywords
                ): result
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