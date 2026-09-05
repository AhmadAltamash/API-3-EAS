import re

from urllib.parse import urljoin

from .html_fetcher import HTMLFetcher
from .html_cleaner import HTMLCleaner


class WebsiteProcessor:

    # If the homepage has no visible email, try ONE more page instead
    # of giving up outright - this is exactly the case that was making
    # AI Discovery/Search skip real, well-known companies: their
    # homepage often has no plain-text email at all, but their actual
    # /contact or /trade page does. Deliberately bounded to a single
    # extra fetch of a link that's ACTUALLY on the homepage (never a
    # guessed URL), so this stays cheap and doesn't reintroduce the
    # Render worker timeouts a full multi-page crawl would risk.
    CONTACT_PAGE_HINTS = (
        "contact", "about", "wholesale", "trade", "b2b", "vendor"
    )

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    def __init__(self):
        self.fetcher = HTMLFetcher()
        self.cleaner = HTMLCleaner()

    def process(self, website):

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

        contact_url = self._find_contact_link(website, homepage_html)

        if contact_url:

            contact_html = self.fetcher.fetch(contact_url)

            if contact_html and self.EMAIL_PATTERN.search(contact_html):
                return contact_html, self.cleaner.clean(contact_html)

        return homepage_html, self.cleaner.clean(homepage_html)

    def _find_contact_link(self, base_url, homepage_html):
        """
        Looks for a real <a href> on the homepage whose URL suggests a
        contact/about/wholesale page - never constructs or guesses a
        URL that isn't actually linked from the page.
        """

        try:

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(homepage_html, "lxml")

            for link in soup.find_all("a", href=True):

                href = link["href"].strip()

                if not href or href.startswith("#"):
                    continue

                href_lower = href.lower()

                if any(hint in href_lower for hint in self.CONTACT_PAGE_HINTS):
                    return urljoin(base_url, href)

        except Exception:
            pass

        return None