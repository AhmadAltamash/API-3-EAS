from .base_adapter import BaseSearchAdapter


class FacebookSearch(BaseSearchAdapter):

    def search(self, keyword):

        print(f"[Facebook] Searching for: {keyword}")

        return []