from ddgs import DDGS

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult


class FacebookSearch(BaseSearchAdapter):

    def search(self, keyword):

        results = []

        query = (
            f'site:facebook.com "{keyword}" '
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
                            source="Facebook"
                        )
                    )

        except Exception as e:
            print(e)

        return results