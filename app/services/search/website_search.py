from .base_adapter import BaseSearchAdapter


class WebsiteSearch(BaseSearchAdapter):

    def search(self, keyword):

        print(f"[Website] Searching for: {keyword}")

        return []