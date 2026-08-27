import re

from .base_extractor import BaseExtractor


class PhoneExtractor(BaseExtractor):
    """
    Pulls a business phone number out of a company's homepage.
    Kept intentionally simple (regex, not AI) to match the style of
    EmailExtractor/CountryExtractor - this is a "best guess from
    public site text" field for manual outreach reference, not a
    verified number.

    Pass raw_html (not the stripped clean_text) - tel: links live in
    an href attribute, so they only survive in the unstripped HTML.
    The loose text pattern still works fine against raw_html too.
    """

    # tel: links are the most reliable signal when present
    TEL_LINK_PATTERN = re.compile(
        r'tel:([+\d][\d\s().-]{6,20}\d)',
        re.IGNORECASE
    )

    # loose US/Canada-style number in visible text, e.g.
    # (555) 123-4567 / 555-123-4567 / +1 555 123 4567
    TEXT_PHONE_PATTERN = re.compile(
        r'(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    )

    def extract(self, buyer, text):

        if not text:
            return buyer

        tel_matches = self.TEL_LINK_PATTERN.findall(text)

        if tel_matches:
            buyer.phone = tel_matches[0].strip()
            return buyer

        text_matches = self.TEXT_PHONE_PATTERN.findall(text)

        for candidate in text_matches:

            digits = re.sub(r"\D", "", candidate)

            # avoid grabbing zip+4, order numbers, years, etc.
            if len(digits) in (10, 11):
                buyer.phone = candidate.strip()
                break

        return buyer
