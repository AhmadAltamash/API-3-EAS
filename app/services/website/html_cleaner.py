from bs4 import BeautifulSoup


class HTMLCleaner:

    def clean(self, html):

        soup = BeautifulSoup(html, "lxml")

        for tag in soup(

            [
                "script",

                "style",

                "svg",

                "noscript",

                "iframe"

            ]

        ):

            tag.decompose()

        return soup.get_text(
            separator=" ",
            strip=True
        )