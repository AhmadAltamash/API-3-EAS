from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


class ListingLinkExtractor:
    """
    Directory/category pages (e.g. a "candle wholesalers in New Jersey"
    listing) rarely have a single company's contact info on them - they
    just link out to many companies at once. This pulls those individual
    company links out of the listing page's HTML so each one can be
    queued and processed on its own, instead of the listing page being
    treated (and rejected) as if it were a single buyer record.
    """

    IGNORE_DOMAINS = {
        "facebook.com", "twitter.com", "x.com", "instagram.com",
        "linkedin.com", "youtube.com", "google.com", "maps.google.com",
        "apple.com", "yelp.com", "pinterest.com", "tiktok.com",
        "schema.org", "w3.org",
    }

    def extract(self, html, base_url, max_links=6):

        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            return []

        base_domain = urlparse(base_url).netloc.lower()

        candidates = []
        seen = set()

        for a in soup.find_all("a", href=True):

            href = a["href"].strip()

            if not href:
                continue

            if href.startswith(("#", "mailto:", "javascript:", "tel:")):
                continue

            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)

            if parsed.scheme not in ("http", "https"):
                continue

            domain = parsed.netloc.lower()

            if any(ignored in domain for ignored in self.IGNORE_DOMAINS):
                continue

            if absolute in seen:
                continue

            # A link that leaves the directory entirely is usually the
            # company's own website ("Visit Website" links) - the most
            # useful kind, since the pipeline can pull that company's
            # real contact info straight from it.
            is_external = domain != base_domain

            # For links staying on the directory's own domain, only keep
            # ones that look like a distinct company/profile page rather
            # than another category or navigation link.
            if not is_external:
                if len(parsed.path.strip("/").split("/")) < 3:
                    continue

            seen.add(absolute)

            candidates.append((is_external, absolute))

            if len(candidates) >= max_links * 3:
                break

        # External company-website links first, then same-site profile pages
        candidates.sort(key=lambda c: not c[0])

        return [url for _, url in candidates[:max_links]]
