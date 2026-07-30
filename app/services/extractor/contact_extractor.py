import re
import urllib3
import requests

from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ContactExtractor:

    EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    PHONE_REGEX = r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?){2,4}\d{2,5}"

    COUNTRIES = [
        "India",
        "Germany",
        "United States",
        "USA",
        "United Kingdom",
        "UK",
        "Canada",
        "Australia",
        "China",
        "Japan",
        "Nepal",
        "France",
        "Italy",
        "Spain"
    ]

    def extract(self, url):

        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        pages = [
            "",
            "/contact",
            "/contact-us",
            "/contactus",
            "/about",
            "/about-us"
        ]

        email = None
        phone = None
        country = None

        for page in pages:

            try:

                full_url = url.rstrip("/") + page

                print(f"Checking: {full_url}")

                response = requests.get(
                    full_url,
                    headers=headers,
                    timeout=10,
                    verify=False
                )

                print("Status:", response.status_code)

                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                html = response.text
                text = soup.get_text(" ", strip=True)

                # ----------------------------
                # MAILTO
                # ----------------------------

                if not email:

                    for link in soup.find_all("a", href=True):

                        href = link["href"]

                        if href.startswith("mailto:"):

                            email = (
                                href
                                .replace("mailto:", "")
                                .split("?")[0]
                                .strip()
                            )

                            break

                # ----------------------------
                # EMAIL REGEX
                # ----------------------------

                if not email:

                    emails = list(set(
                        re.findall(
                            self.EMAIL_REGEX,
                            html
                        )
                    ))

                    blacklist = [
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".svg",
                        ".css",
                        ".js"
                    ]

                    for e in emails:

                        if any(x in e.lower() for x in blacklist):
                            continue

                        email = e
                        break

                # ----------------------------
                # PHONE
                # ----------------------------

                if not phone:

                    phones = re.findall(
                        self.PHONE_REGEX,
                        text
                    )

                    for p in phones:

                        digits = re.sub(r"\D", "", p)

                        if len(digits) >= 8:

                            phone = p.strip()

                            break

                # ----------------------------
                # COUNTRY
                # ----------------------------

                if not country:

                    for c in self.COUNTRIES:

                        if c.lower() in text.lower():

                            country = c

                            break

                if email and phone and country:
                    break

            except Exception as e:

                print(e)

        return {

            "email": email,

            "phone": phone,

            "country": country

        }