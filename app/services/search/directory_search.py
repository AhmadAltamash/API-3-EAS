from ddgs import DDGS

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult


class DirectorySearch(BaseSearchAdapter):

    # Well-known B2B / business directory sites likely to list US companies
    DIRECTORY_SITES = [
        "thomasnet.com",
        "manta.com",
        "bbb.org",
        "dnb.com",
    ]

    def search(self, keyword):

        results = []

        site_filter = " OR ".join(
            f"site:{site}" for site in self.DIRECTORY_SITES
        )

        query = (
            f'({site_filter}) "{keyword}" '
            f'"United States" OR USA'
        )

        try:

            with DDGS() as ddgs:

                search_results = ddgs.text(
                    query,
                    max_results=20
                )

                for item in search_results:

                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("href", ""),
                            snippet=item.get("body", ""),
                            source="Directory"
                        )
                    )

        except Exception as e:
            print(f"[Directory] {e}")

        return results