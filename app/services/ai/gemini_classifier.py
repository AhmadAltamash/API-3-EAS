import time

from google import genai
from config import Config


class GeminiService:

    # Flash-Lite is the right tier for a single-label classification task
    # like this (cheaper, higher requests-per-minute headroom than the
    # full Flash/Pro models, which are overkill here and more likely to
    # be under heavy demand).
    MODEL = "gemini-3.5-flash-lite"

    MAX_RETRIES = 3

    # Errors worth retrying - transient/overload conditions, not "your
    # prompt is invalid" type errors.
    RETRYABLE_MARKERS = (
        "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded"
    )

    def __init__(self):

        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY
        )

    def classify(self, company, website, snippet):

        prompt = f"""
        You are an expert export lead classifier.

        Classify this company.

        Company:
        {company}

        Website:
        {website}

        Search Snippet:
        {snippet}

        Possible Categories:

        Importer
        Exporter
        Manufacturer
        Distributor
        Wholesaler
        Retailer
        Unknown

        Guidelines:

        - Imports goods → Importer

        - Exports goods → Exporter

        - Makes products → Manufacturer

        - Sells to retailers → Wholesaler

        - Supplies products for brands → Distributor

        - Sells directly to consumers → Retailer

        Return ONLY one category.

        No explanation.
        """

        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):

            try:

                response = self.client.models.generate_content(
                    model=self.MODEL,
                    contents=prompt
                )

                print("Gemini Response:", response.text)

                return response.text.strip()

            except Exception as e:

                last_error = e

                error_text = str(e)

                is_retryable = any(
                    marker in error_text
                    for marker in self.RETRYABLE_MARKERS
                )

                print(f"Gemini Error (attempt {attempt}/{self.MAX_RETRIES}):", e)

                if not is_retryable or attempt == self.MAX_RETRIES:
                    break

                # Back off before retrying - Google's own guidance for a
                # 503 "high demand" response is to wait and retry rather
                # than hammer it again immediately.
                time.sleep(2 ** attempt)

        print("Gemini classification failed after retries:", last_error)

        return "Unknown"