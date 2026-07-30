from bs4 import BeautifulSoup

from .base_extractor import BaseExtractor


class CompanyExtractor(BaseExtractor):

    def extract(self, buyer, html):

        soup = BeautifulSoup(html, "lxml")

        if soup.title:

            buyer.company = soup.title.text.strip()

        return buyer