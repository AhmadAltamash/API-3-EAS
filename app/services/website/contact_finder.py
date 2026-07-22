from bs4 import BeautifulSoup
from urllib.parse import urljoin


class ContactFinder:

    KEYWORDS = [

        "contact",

        "contact-us",

        "about",

        "about-us",

        "team",

        "company",

        "support",

        "imprint"

    ]

    def find(self, base_url, html):

        soup = BeautifulSoup(html, "lxml")

        pages = []

        for link in soup.find_all("a", href=True):

            href = link["href"]

            url = urljoin(base_url, href)

            if any(
                word in url.lower()
                for word in self.KEYWORDS
            ):

                pages.append(url)

        return list(dict.fromkeys(pages))