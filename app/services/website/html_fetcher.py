import requests


class HTMLFetcher:

    def __init__(self):

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            )
        }

    def fetch(self, url):

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            response.raise_for_status()

            return response.text

        except Exception as e:

            print(f"[Fetcher] {url}")

            print(e)

            return ""