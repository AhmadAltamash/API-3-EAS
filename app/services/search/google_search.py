from ddgs import DDGS

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult


class GoogleSearch(BaseSearchAdapter):

    def search(self, keyword):

        results = []

        try:

            with DDGS() as ddgs:

                search_results = ddgs.text(
                    keyword,
                    max_results=20
                )

                for item in search_results:

                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("href", ""),
                            snippet=item.get("body", ""),
                            source="Google"
                        )
                    )

        except Exception as e:

            print(e)

        return results