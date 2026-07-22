from urllib.parse import urlparse

from .base_extractor import BaseExtractor


class CountryExtractor(BaseExtractor):

    DOMAIN_MAP = {
        ".de": "Germany",
        ".fr": "France",
        ".it": "Italy",
        ".es": "Spain",
        ".uk": "United Kingdom",
        ".co.uk": "United Kingdom",
        ".ca": "Canada",
        ".au": "Australia",
        ".in": "India",
        ".jp": "Japan",
        ".cn": "China",
        ".br": "Brazil",
        ".mx": "Mexico",
        ".nl": "Netherlands",
        ".be": "Belgium",
        ".ch": "Switzerland",
        ".at": "Austria",
        ".se": "Sweden",
        ".no": "Norway",
        ".fi": "Finland",
        ".pl": "Poland"
    }

    def extract(self, buyer, html):

        domain = urlparse(buyer.website).netloc.lower()

        for suffix, country in self.DOMAIN_MAP.items():

            if domain.endswith(suffix):

                buyer.country = country
                return buyer

        return buyer