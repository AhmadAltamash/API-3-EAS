from .base_adapter import BaseSearchAdapter


class DirectorySearch(BaseSearchAdapter):

    def search(self, keyword):

        print(f"[Directory] Searching for: {keyword}")

        return []