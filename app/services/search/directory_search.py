from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from ddgs import DDGS

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult
from app.services.website.html_fetcher import HTMLFetcher
from app.services.website.listing_link_extractor import ListingLinkExtractor


class DirectorySearch(BaseSearchAdapter):

    # thomasnet.com and manta.com were dropped: both return a blanket
    # 403 Forbidden to any automated request regardless of query, so they
    # never yield anything no matter how this is built. These alternatives
    # are generally reachable with a plain request.
    DIRECTORY_SITES = [
        "bbb.org",
        "chamberofcommerce.com",
        "yellowpages.com",
    ]

    MAX_LISTING_PAGES = 6
    MAX_LINKS_PER_LISTING = 5

    def __init__(self):

        super().__init__()

        self.fetcher = HTMLFetcher()
        self.extractor = ListingLinkExtractor()

    def search(self, keyword):

        results = []

        site_filter = " OR ".join(
            f"site:{site}" for site in self.DIRECTORY_SITES
        )

        query = (
            f'({site_filter}) "{keyword}" '
            f'"United States" OR USA OR Canada'
        )

        listing_urls = []

        try:

            with DDGS() as ddgs:

                for item in ddgs.text(query, max_results=self.MAX_LISTING_PAGES):

                    url = item.get("href", "")

                    if url:
                        listing_urls.append(url)

        except Exception as e:
            print(f"[Directory] {e}")
            return results

        if not listing_urls:
            return results

        # A listing page indexes many companies at once, so fetch each one
        # and pull out the individual company links instead of treating the
        # listing page itself as a single buyer record (which is why this
        # source used to come back empty even when the search matched
        # plenty of listings).
        with ThreadPoolExecutor(max_workers=len(listing_urls)) as executor:

            futures = {
                executor.submit(self.fetcher.fetch, url): url
                for url in listing_urls
            }

            for future in as_completed(futures):

                listing_url = futures[future]

                try:
                    html = future.result()
                except Exception as e:
                    print(f"[Directory] {listing_url}: {e}")
                    continue

                if not html:
                    # Blocked (403) or unreachable. Bypassing a site's bot
                    # protection isn't something this adapter will try to
                    # do - skip it and move on to the next listing.
                    continue

                company_links = self.extractor.extract(
                    html,
                    listing_url,
                    max_links=self.MAX_LINKS_PER_LISTING
                )

                for link in company_links:

                    results.append(
                        SearchResult(
                            title=f"Listed on {urlparse(listing_url).netloc}",
                            url=link,
                            snippet="",
                            source="Directory"
                        )
                    )

        return results