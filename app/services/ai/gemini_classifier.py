from google import genai
from config import Config


class GeminiService:

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

        try:

            response = self.client.models.generate_content(
                model="models/gemini-3.5-flash",
                contents=prompt
            )

            print("Gemini Response:", response.text)

            return response.text.strip()

        except Exception as e:

            print("Gemini Error:", e)

        return "Unknown"