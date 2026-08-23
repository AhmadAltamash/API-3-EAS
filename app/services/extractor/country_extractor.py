import re
from urllib.parse import urlparse

from .base_extractor import BaseExtractor


class CountryExtractor(BaseExtractor):

    # Countries we are NOT targeting - ccTLD is a reliable "not US/Canada"
    # signal, checked first. .ca was removed from this list: Canada is now
    # a target market, not a country to exclude.
    DOMAIN_MAP = {
        ".de": "Germany",
        ".fr": "France",
        ".it": "Italy",
        ".es": "Spain",
        ".uk": "United Kingdom",
        ".co.uk": "United Kingdom",
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

    CA_PROVINCES = [
        "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE",
        "QC", "SK", "YT"
    ]

    CA_PROVINCE_NAMES = [
        "Alberta", "British Columbia", "Manitoba", "New Brunswick",
        "Newfoundland and Labrador", "Nova Scotia",
        "Northwest Territories", "Nunavut", "Ontario",
        "Prince Edward Island", "Quebec", "Saskatchewan", "Yukon"
    ]

    # Reverse lookups: full state/province name -> abbreviation, used so
    # buyer.state is always stored as the short code the timezone service
    # expects, regardless of whether the page spelled the name out.
    US_NAME_TO_ABBR = dict(zip(
        [name.lower() for name in US_STATE_NAMES], US_STATES
    ))

    CA_NAME_TO_ABBR = dict(zip(
        [name.lower() for name in CA_PROVINCE_NAMES], CA_PROVINCES
    ))

    # Canada Post's first postal-code letter maps to a specific
    # province/territory region - lets us guess the province even when a
    # page only shows a bare postal code with no spelled-out province.
    CA_FSA_FIRST_LETTER_TO_PROVINCE = {
        "A": "NL", "B": "NS", "C": "PE", "E": "NB",
        "G": "QC", "H": "QC", "J": "QC",
        "K": "ON", "L": "ON", "M": "ON", "N": "ON", "P": "ON",
        "R": "MB", "S": "SK", "T": "AB", "V": "BC",
        "X": "NT", "Y": "YT",
    }

    # e.g. "Austin, TX 78701" or "TX 78701-1234"
    US_STATE_ZIP_PATTERN = re.compile(
        r"\b(" + "|".join(US_STATES) + r")\b\s+\d{5}(-\d{4})?"
    )

    # e.g. "Dallas, Texas 75214" - full state name followed by a zip code
    US_STATE_NAME_ZIP_PATTERN = re.compile(
        r"\b(" + "|".join(US_STATE_NAMES) + r")\b\s*,?\s*\d{5}(-\d{4})?"
    )

    US_TEXT_PATTERN = re.compile(
        r"\bunited states\b|\bUSA\b", re.IGNORECASE
    )

    # Canadian postal code, e.g. "M5V 3A8" - letter/digit/letter, digit/
    # letter/digit. The restricted letter set (no D,F,I,O,Q,U) matches
    # Canada Post's actual rules, which keeps this from firing on random
    # alphanumeric codes.
    _CA_POSTAL_LETTERS = "ABCEGHJ-NPRSTVXY"

    CA_POSTAL_PATTERN = re.compile(
        r"\b([" + _CA_POSTAL_LETTERS + r"])\d["
        + _CA_POSTAL_LETTERS + r"]\s?\d[" + _CA_POSTAL_LETTERS + r"]\d\b",
        re.IGNORECASE
    )

    # Province abbreviation followed by a postal code - required together
    # since two-letter province codes like "ON" or "PE" are also common
    # English words on their own.
    CA_PROVINCE_ZIP_PATTERN = re.compile(
        r"\b(" + "|".join(CA_PROVINCES) + r")\b\s+["
        + _CA_POSTAL_LETTERS + r"]\d[" + _CA_POSTAL_LETTERS + r"]"
    )

    CA_PROVINCE_NAME_PATTERN = re.compile(
        r"\b(" + "|".join(CA_PROVINCE_NAMES) + r")\b", re.IGNORECASE
    )

    CA_TEXT_PATTERN = re.compile(
        r"\bcanada\b", re.IGNORECASE
    )

    def extract(self, buyer, html):

        domain = urlparse(buyer.website).netloc.lower()

        # Countries we're not targeting - a clear signal, checked first
        for suffix, country in self.DOMAIN_MAP.items():

            if domain.endswith(suffix):

                buyer.country = country
                return buyer

        text = html or ""

        if domain.endswith(".us"):
            buyer.country = "United States"
            return buyer

        if domain.endswith(".ca"):
            buyer.country = "Canada"
            return buyer

        # Province abbreviation + postal code is the strongest Canada
        # signal - check it before the bare postal-code pattern so we
        # capture the province directly when it's available.
        match = self.CA_PROVINCE_ZIP_PATTERN.search(text)
        if match:
            buyer.country = "Canada"
            buyer.state = match.group(1).upper()
            return buyer

        match = self.CA_PROVINCE_NAME_PATTERN.search(text)
        if match:
            buyer.country = "Canada"
            buyer.state = self.CA_NAME_TO_ABBR.get(match.group(1).lower())
            return buyer

        # Bare Canadian postal code, no province text nearby - use the
        # first letter to guess the province via Canada Post's regions.
        match = self.CA_POSTAL_PATTERN.search(text)
        if match:
            buyer.country = "Canada"
            buyer.state = self.CA_FSA_FIRST_LETTER_TO_PROVINCE.get(
                match.group(1).upper()
            )
            return buyer

        if self.CA_TEXT_PATTERN.search(text) and not self.US_TEXT_PATTERN.search(text):
            buyer.country = "Canada"
            return buyer

        if self.US_TEXT_PATTERN.search(text):
            buyer.country = "United States"
            return buyer

        match = self.US_STATE_ZIP_PATTERN.search(text)
        if match:
            buyer.country = "United States"
            buyer.state = match.group(1).upper()
            return buyer

        match = self.US_STATE_NAME_ZIP_PATTERN.search(text)
        if match:
            buyer.country = "United States"
            buyer.state = self.US_NAME_TO_ABBR.get(match.group(1).lower())
            return buyer

        # Deliberately NOT falling back to a phone-number check: US and
        # Canada share the same NANP phone format ((xxx) xxx-xxxx), so a
        # phone number alone can't tell the two apart - guessing here
        # would silently mislabel Canadian companies as American. Better
        # to leave country unset (and have the pipeline skip the buyer)
        # than report an unreliable country - quality over quantity.
        return buyer
