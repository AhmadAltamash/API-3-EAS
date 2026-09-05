import requests

from .base_adapter import BaseSearchAdapter
from .search_result import SearchResult


class SerpApiSearch(BaseSearchAdapter):
    """
    Real Google search results via serpapi.com's REST API - a paid
    provider with a genuinely recurring (not one-time) free tier of
    250 searches/month, no credit card required. Unlike GoogleSearch
    (which despite its name queries DuckDuckGo through the unofficial
    `ddgs` library, not Google at all), this is actual Google SERP
    data, the same kind of result you'd see typing into google.com.

    Added as a new option in the existing Source dropdown - NOT a
    replacement for the "google"/ddgs adapter, so the two can be
    compared side by side before deciding whether to lean on this one
    more. Fails soft (returns an empty list, never raises) on a
    missing key, network error, or exhausted quota, exactly like every
    other adapter here - one source having a bad day shouldn't take
    down an "all sources" search.
    """

    ENDPOINT = "https://serpapi.com/search.json"

    TIMEOUT_SECONDS = 10

    def __init__(self, api_key=None):

        super().__init__()

        if api_key is not None:
            self.api_key = api_key
        else:
            from config import Config
            self.api_key = Config.SERPAPI_KEY

    def search(self, keyword):

        if not self.api_key:
            print("[SerpApiSearch] No SERPAPI_KEY configured - skipping.")
            return []

        # Same US-focused query convention as GoogleSearch, for
        # consistency between the two Google-labeled sources.
        query = (
            f'{keyword} importer OR wholesaler OR distributor '
            f'"United States" OR USA OR Canada'
        )

        results = []

        try:

            response = requests.get(
                self.ENDPOINT,
                params={
                    "q": query,
                    "engine": "google",
                    "api_key": self.api_key,
                    "num": 30
                },
                timeout=self.TIMEOUT_SECONDS
            )

            response.raise_for_status()

            data = response.json()

        except Exception as e:
            print(f"[SerpApiSearch] request error: {e}")
            return []

        # SerpApi returns HTTP 200 with an "error" field in the body
        # for things like an exhausted monthly quota or a bad key -
        # it doesn't necessarily raise via raise_for_status() above.
        if isinstance(data, dict) and data.get("error"):
            print(f"[SerpApiSearch] API error: {data['error']}")
            return []

        for item in data.get("organic_results", []):

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="SerpApi"
                )
            )

        return results
