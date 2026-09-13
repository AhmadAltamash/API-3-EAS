import time

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
    more. Fails soft (returns an empty list, never raises) after
    retries are exhausted - one source having a bad day shouldn't take
    down an "all sources" search.
    """

    ENDPOINT = "https://serpapi.com/search.json"

    # A long-open connection is exactly the kind of thing that gets
    # killed mid-flight by an intermediate proxy or a hosting
    # platform's own worker timeout (this project already has a
    # comment elsewhere about Render worker timeouts) - keep this
    # modest rather than generous. Same reasoning for NUM_RESULTS:
    # asking Google to compute a much larger results page takes
    # noticeably longer and fails more often, for free-tier accounts
    # in particular.
    TIMEOUT_SECONDS = 15

    NUM_RESULTS = 30

    MAX_RETRIES = 3

    # requests/urllib3 wrap timeouts, connection resets, and DNS
    # hiccups all under variations of "connection" errors - retrying
    # these is worthwhile since they're often transient. A 4xx (bad
    # key, bad request) or an API-level quota error is NOT retryable -
    # retrying those just burns quota for the same guaranteed failure.
    RETRYABLE_EXCEPTIONS = (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    )

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

        data = self._request_with_retry(query)

        if data is None:
            return []

        # SerpApi returns HTTP 200 with an "error" field in the body
        # for things like an exhausted monthly quota or a bad key -
        # it doesn't necessarily raise via raise_for_status().
        if isinstance(data, dict) and data.get("error"):
            print(f"[SerpApiSearch] API error: {data['error']}")
            return []

        results = []

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

    def _request_with_retry(self, query):

        for attempt in range(1, self.MAX_RETRIES + 1):

            try:

                response = requests.get(
                    self.ENDPOINT,
                    params={
                        "q": query,
                        "engine": "google",
                        "api_key": self.api_key,
                        "num": self.NUM_RESULTS
                    },
                    timeout=self.TIMEOUT_SECONDS
                )

                response.raise_for_status()

                return response.json()

            except self.RETRYABLE_EXCEPTIONS as e:

                print(f"[SerpApiSearch] attempt {attempt}/{self.MAX_RETRIES} - connection issue: {e}")

                if attempt == self.MAX_RETRIES:
                    return None

                time.sleep(2 ** attempt)

            except Exception as e:

                # Not a connection issue (a 4xx, a malformed response,
                # etc) - retrying won't help and would just burn quota
                # on a guaranteed repeat failure.
                print(f"[SerpApiSearch] request error (not retrying): {e}")
                return None

        return None
