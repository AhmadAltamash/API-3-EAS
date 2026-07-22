from .html_fetcher import HTMLFetcher
from .contact_finder import ContactFinder
from .html_cleaner import HTMLCleaner


class WebsiteProcessor:

    def __init__(self):

        self.fetcher = HTMLFetcher()

        self.finder = ContactFinder()

        self.cleaner = HTMLCleaner()

    def process(self, website):

        homepage = self.fetcher.fetch(website)

        if not homepage:

            return ""

        pages = self.finder.find(

            website,

            homepage

        )

        html = homepage

        for page in pages:

            html += "\n"

            html += self.fetcher.fetch(page)

        return self.cleaner.clean(html)