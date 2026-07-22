import requests


class HTMLFetcher:

    def __init__(self):

        self.headers = {

            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36"

        }

    def fetch(self, url):

        if not url:
            return ""

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=5,
                allow_redirects=True
            )

            response.raise_for_status()

            return response.text

        except requests.RequestException as e:

            print(f"[Fetcher] {url}")

            print(e)

            return ""