from ddgs import DDGS

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult


class WebsiteSearch(BaseSearchAdapter):

    def search(self, keyword):

        results = []

        # Broad query targeting general company/contact pages rather than
        # a specific platform - complements the Google/Facebook/LinkedIn/
        # Directory adapters with independent business websites.
        query = (
            f'{keyword} company "contact us" '
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
                            source="Website"
                        )
                    )

        except Exception as e:
            print(f"[Website] {e}")

        return results