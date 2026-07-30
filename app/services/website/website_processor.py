from .html_fetcher import HTMLFetcher
from .html_cleaner import HTMLCleaner


class WebsiteProcessor:

    def __init__(self):
        self.fetcher = HTMLFetcher()
        self.cleaner = HTMLCleaner()

    def process(self, website):

        if not website:
            return ""

        homepage = self.fetcher.fetch(website)

        if not homepage:
            return ""

        # Only process the homepage.
        # Crawling multiple pages causes Render worker timeouts.
        return self.cleaner.clean(homepage)