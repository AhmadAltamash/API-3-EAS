import re
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

    US_STATES = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC"
    ]

    US_STATE_NAMES = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California",
        "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
        "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas",
        "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts",
        "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
        "Nebraska", "Nevada", "New Hampshire", "New Jersey",
        "New Mexico", "New York", "North Carolina", "North Dakota",
        "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
        "South Carolina", "South Dakota", "Tennessee", "Texas",
        "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
        "Wisconsin", "Wyoming"
    ]

    # e.g. "Austin, TX 78701" or "TX 78701-1234"
    US_STATE_ZIP_PATTERN = re.compile(
        r"\b(" + "|".join(US_STATES) + r")\b\s+\d{5}(-\d{4})?"
    )

    # e.g. "Dallas, Texas 75214" - full state name followed by a zip code
    US_STATE_NAME_ZIP_PATTERN = re.compile(
        r"\b(" + "|".join(US_STATE_NAMES) + r")\b\s*,?\s*\d{5}(-\d{4})?"
    )

    # e.g. "+1 (555) 123-4567", "(555) 123-4567", "555-123-4567"
    US_PHONE_PATTERN = re.compile(
        r"(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}"
    )

    US_TEXT_PATTERN = re.compile(
        r"\bunited states\b|\bUSA\b", re.IGNORECASE
    )

    def extract(self, buyer, html):

        domain = urlparse(buyer.website).netloc.lower()

        # Foreign country-code domains are a clear signal - check first
        for suffix, country in self.DOMAIN_MAP.items():

            if domain.endswith(suffix):

                buyer.country = country
                return buyer

        text = html or ""

        if domain.endswith(".us"):
            buyer.country = "United States"
            return buyer

        if self.US_TEXT_PATTERN.search(text):
            buyer.country = "United States"
            return buyer

        if self.US_STATE_ZIP_PATTERN.search(text):
            buyer.country = "United States"
            return buyer

        if self.US_STATE_NAME_ZIP_PATTERN.search(text):
            buyer.country = "United States"
            return buyer

        if self.US_PHONE_PATTERN.search(text):
            buyer.country = "United States"
            return buyer

        # No US signal found and no foreign ccTLD matched either -
        # leave unset so the pipeline treats it as non-US and skips it.
        return buyer