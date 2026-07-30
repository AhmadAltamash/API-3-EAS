from ddgs import DDGS

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult


class LinkedInSearch(BaseSearchAdapter):

    def search(self, keyword):

        results = []

        query = (
            f'site:linkedin.com/company "{keyword}" '
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
                            source="LinkedIn"
                        )
                    )

        except Exception as e:
            print(e)

        return results