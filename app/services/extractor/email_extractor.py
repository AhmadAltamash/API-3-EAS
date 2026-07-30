import re

from .base_extractor import BaseExtractor


class EmailExtractor(BaseExtractor):

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    def extract(self, buyer, html):

        emails = self.EMAIL_PATTERN.findall(html)

        if emails:

            buyer.email = emails[0]

        return buyer