from .base_adapter import BaseSearchAdapter


class LinkedInSearch(BaseSearchAdapter):

    def search(self, keyword):

        print(f"[LinkedIn] Searching for: {keyword}")

        return []