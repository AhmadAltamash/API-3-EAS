from dataclasses import dataclass


@dataclass
class SearchResult:

    title: str = ""

    url: str = ""

    snippet: str = ""

    source: str = ""

    # Optional - the country the SEARCH itself was scoped to (from the
    # structured search form's Country field), not anything found on
    # the page. Used as a fallback in BuyerPipeline only when the page
    # itself gives no country signal - never overrides a real,
    # page-confirmed country, and is always tagged as assumed rather
    # than confirmed when used.
    target_country: str = ""

    # Optional - whether this search explicitly opted into the real-
    # browser (Playwright) fallback for pages that come back empty
    # under a plain HTTP fetch. Off by default - see PlaywrightFetcher
    # and the "Also try a real browser" checkbox on the Search page.
    use_browser_fallback: bool = False