import requests


class HTMLFetcher:

    def __init__(self):

        self.headers = {

            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0 Safari/537.36"

        }

        # A shared session reuses TCP/TLS connections across requests,
        # which is faster than opening a fresh connection every time.
        self.session = requests.Session()

        self.session.headers.update(self.headers)

    def fetch(self, url):

        if not url:
            return ""

        try:

            response = self.session.get(
                url,
                timeout=4,
                allow_redirects=True
            )

            response.raise_for_status()

            return response.text

        except requests.RequestException as e:

            print(f"[Fetcher] {url}")

            print(e)

            return ""