class PlaywrightFetcher:
    """
    Renders a page with a real headless browser (Chromium) and returns
    the fully JS-executed HTML. Kept completely independent, the same
    way SerpApiSearch is independent of the default DDGS adapter:

    - A separate module, not code folded into HTMLFetcher/WebsiteProcessor.
    - Off by default. Only used when explicitly opted into per search
      (see the "Also try a real browser" checkbox on the Search page),
      never silently applied to every fetch.
    - Only reached as a last resort, after the fast HTTP fetch and the
      contact-page-link fallback have both already failed to find an
      email - a full browser launch is roughly 10-50x heavier than a
      plain HTTP request, so it should never be the first thing tried.

    Requires the `playwright` Python package AND its browser binary
    (`playwright install chromium`) - the second step downloads an
    actual ~150MB Chromium build and needs real network access to
    Playwright's own CDN, which is a separate step from `pip install`.
    If that hasn't been run, every call here fails soft (returns "")
    with a clear one-line explanation printed, rather than crashing
    the search.
    """

    TIMEOUT_MS = 15000

    def fetch(self, url):

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print(
                "[PlaywrightFetcher] The 'playwright' package isn't "
                "installed - run: pip install playwright"
            )
            return ""

        try:

            with sync_playwright() as p:

                browser = p.chromium.launch(headless=True)

                try:

                    page = browser.new_page()

                    page.set_default_timeout(self.TIMEOUT_MS)

                    page.goto(url, wait_until="domcontentloaded")

                    # A short extra wait for content that renders just
                    # after the initial DOM is ready (common for React/
                    # Vue sites) - not a full "networkidle" wait, which
                    # can hang indefinitely on pages with long-polling
                    # or analytics scripts that never truly go idle.
                    page.wait_for_timeout(2000)

                    html = page.content()

                    return html or ""

                finally:
                    browser.close()

        except Exception as e:

            error_text = str(e)

            if "Executable doesn't exist" in error_text:
                print(
                    "[PlaywrightFetcher] Chromium isn't downloaded yet - "
                    "run: playwright install chromium"
                )
            else:
                print(f"[PlaywrightFetcher] fetch failed for {url}: {e}")

            return ""
