from ddgs import DDGS

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult


class GoogleSearch(BaseSearchAdapter):

    # A colleague's working script tries these DDGS backends in order,
    # falling through to the next only if the previous one raised or
    # came back empty - meaningfully more resilient than trusting a
    # single default backend, which is all this adapter used to do.
    BACKENDS = ["auto", "duckduckgo", "brave", "mojeek"]

    def search(self, keyword):

        # US-focused query
        query = (
            f'{keyword} importer OR wholesaler OR distributor '
            f'"United States" OR USA OR Canada'
        )

        for backend in self.BACKENDS:

            results = self._search_with_backend(query, backend)

            if results:
                return results

        return []

    def _search_with_backend(self, query, backend):

        results = []

        try:

            with DDGS() as ddgs:

                search_results = ddgs.text(
                    query,
                    max_results=50,
                    backend=backend
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
            print(f"[GoogleSearch] backend '{backend}' failed: {e}")

        return results