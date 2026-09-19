import re

from urllib.parse import urljoin

from .html_fetcher import HTMLFetcher
from .html_cleaner import HTMLCleaner
from .playwright_fetcher import PlaywrightFetcher


class WebsiteProcessor:

    # If the homepage has no visible email, try more of these instead
    # of giving up outright - this is exactly the case that was making
    # AI Discovery/Search skip real, well-known companies: their
    # homepage often has no plain-text email at all, but their actual
    # /contact or /trade page does. A colleague's working scraper does
    # the same thing and also matches on the link's visible TEXT, not
    # just its href - a real gap here, since a nav link like
    # <a href="/pages/get-in-touch">Contact Us</a> has "contact" in the
    # text but not the URL, and was being missed entirely. Bounded to
    # a handful of candidates actually found on the page (never a
    # guessed URL), so this stays cheap and doesn't reintroduce the
    # Render worker timeouts a full multi-page crawl would risk.
    CONTACT_PAGE_HINTS = (
        "contact", "contactus", "about", "wholesale", "trade",
        "b2b", "vendor", "support", "reach-us", "reach us", "get-in-touch"
    )

    MAX_CONTACT_CANDIDATES = 5

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    def __init__(self):
        self.fetcher = HTMLFetcher()
        self.cleaner = HTMLCleaner()
        self.browser_fetcher = PlaywrightFetcher()

    def process(self, website, use_browser_fallback=False):

        if not website:
            return "", ""

        homepage_html = self.fetcher.fetch(website)

        if not homepage_html:
            return "", ""

        # Only process the homepage, unless it has no visible email -
        # see CONTACT_PAGE_HINTS above for why and how far this goes.
        # Crawling more broadly than that risks Render worker timeouts.
        #
        # Returns (raw_html, cleaned_text) - raw HTML is needed for things
        # like the <title> tag, while the cleaned text is better for
        # email/country pattern matching since scripts/styles are stripped.
        if self.EMAIL_PATTERN.search(homepage_html):
            return homepage_html, self.cleaner.clean(homepage_html)

        for contact_url in self._find_contact_links(website, homepage_html):

            contact_html = self.fetcher.fetch(contact_url)

            if contact_html and self.EMAIL_PATTERN.search(contact_html):
                return contact_html, self.cleaner.clean(contact_html)

        # Last resort, opt-in only: a real browser, for JS-rendered
        # sites where the plain HTTP fetch above got back an empty
        # shell (a homepage's raw HTML with no email and no useful
        # contact links to follow is exactly what that looks like).
        # Never reached unless the search explicitly asked for it -
        # see the class docstring in PlaywrightFetcher for why.
        if use_browser_fallback:

            rendered_html = self.browser_fetcher.fetch(website)

            if rendered_html and self.EMAIL_PATTERN.search(rendered_html):
                return rendered_html, self.cleaner.clean(rendered_html)

        return homepage_html, self.cleaner.clean(homepage_html)

    def _find_contact_links(self, base_url, homepage_html):
        """
        Looks for real <a href> links on the homepage whose URL OR
        visible text suggests a contact/about/wholesale page - never
        constructs or guesses a URL that isn't actually linked from
        the page. Returns up to MAX_CONTACT_CANDIDATES, in the order
        they appear, so the caller can try each until one has an email.
        """

        candidates = []

        try:

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(homepage_html, "lxml")

            seen = set()

            for link in soup.find_all("a", href=True):

                if len(candidates) >= self.MAX_CONTACT_CANDIDATES:
                    break

                href = link["href"].strip()

                if not href or href.startswith("#"):
                    continue

                href_lower = href.lower()

                text_lower = link.get_text(" ", strip=True).lower()

                if any(
                    hint in href_lower or hint in text_lower
                    for hint in self.CONTACT_PAGE_HINTS
                ):

                    full_url = urljoin(base_url, href)

                    if full_url not in seen:
                        seen.add(full_url)
                        candidates.append(full_url)

        except Exception:
            pass

        return candidates