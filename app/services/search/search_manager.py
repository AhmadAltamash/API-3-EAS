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

    # Buyer-intent phrasing variations tried per search, in addition to
    # the plain keyword itself - modeled directly on a colleague's
    # working script, which fires ~15 such variations in parallel
    # against DDGS and reports meaningfully higher yield than a single
    # query ever could. Kept a bit more conservative here (this
    # sandbox has no way to test DuckDuckGo's real rate-limit
    # tolerance directly), and deliberately excluded from SerpApi -
    # that quota is scarce and shouldn't multiply per click.
    QUERY_MODIFIERS = [
        "",
        "wholesale",
        "distributor",
        "bulk buyer",
        "trade program",
        "wholesale inquiries",
    ]

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

    def _query_variations(self, keyword, limit):

        variations = []

        for modifier in self.QUERY_MODIFIERS[:limit]:

            variation = f"{keyword} {modifier}".strip()

            if variation not in variations:
                variations.append(variation)

        return variations

    def search(self, source, keyword, target_country=None, use_browser_fallback=False):

        all_results = []

        if source == "serpapi":

            # Exactly one query, exactly one credit - no multiplication.
            all_results = self.serpapi.search(keyword)

        elif source == "all":

            # Fans out across every adapter already, so fewer query
            # variations per adapter to keep the total call count
            # reasonable (5 adapters x 3 variations = 15 calls, the
            # same order of magnitude as the colleague script's 15).
            queries = self._query_variations(keyword, limit=3)

            with ThreadPoolExecutor(max_workers=len(self.adapters) * len(queries)) as executor:

                futures = [
                    executor.submit(adapter.search, query)
                    for adapter in self.adapters.values()
                    for query in queries
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

            queries = self._query_variations(keyword, limit=6)

            with ThreadPoolExecutor(max_workers=len(queries)) as executor:

                futures = [
                    executor.submit(adapter.search, query)
                    for query in queries
                ]

                for future in as_completed(futures):

                    try:
                        all_results.extend(future.result())
                    except Exception as e:
                        print(f"[SearchManager] query variation error: {e}")

        # Tag every result with the country the SEARCH was scoped to,
        # BEFORE dedup/pipeline - BuyerPipeline only ever uses this as
        # a fallback when the page itself gives no country signal, and
        # always marks it as assumed rather than confirmed when it does.
        #
        # Also tag whether this run explicitly opted into the real-
        # browser fallback - off unless the person checked that box,
        # since a browser launch is much heavier than a plain fetch
        # and shouldn't silently apply to every search.
        for result in all_results:
            result.target_country = target_country or ""
            result.use_browser_fallback = bool(use_browser_fallback)

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