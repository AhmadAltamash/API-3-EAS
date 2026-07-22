import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class WebsiteCrawler:

    CONTACT_KEYWORDS = [
        "contact",
        "contact-us",
        "about",
        "about-us",
        "company",
        "team",
        "support"
    ]

    def __init__(self):

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            )
        }

    def fetch_html(self, url):

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            response.raise_for_status()

            return response.text

        except Exception as e:

            print(f"[Crawler] {e}")

            return None

    def discover_pages(self, website):

        html = self.fetch_html(website)

        if html is None:
            return []

        soup = BeautifulSoup(html, "lxml")

        pages = []

        for link in soup.find_all("a", href=True):

            href = link["href"]

            full_url = urljoin(website, href)

            if any(
                word in full_url.lower()
                for word in self.CONTACT_KEYWORDS
            ):
                pages.append(full_url)

        pages = list(dict.fromkeys(pages))

        return pages

    def crawl(self, website):

        html_pages = []

        homepage = self.fetch_html(website)

        if homepage:

            html_pages.append(homepage)

        pages = self.discover_pages(website)

        for page in pages:

            html = self.fetch_html(page)

            if html:

                html_pages.append(html)

        return html_pages