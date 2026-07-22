class ResultFilter:

    BLOCKED_DOMAINS = [
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "twitter.com",
        "youtube.com",
        "volza.com",
        "trademo.com",
        "tradewheel.com",
        "alibaba.com",
        "statista.com",
        "oec.world"
    ]

    BLOCKED_WORDS = [
        "blog",
        "market",
        "report",
        "statistics",
        "news",
        "guide",
        "how to",
        "market potential",
        "market entry"
    ]

    def filter(self, results):

        filtered = []

        for result in results:

            url = result.url.lower()
            title = result.title.lower()

            
            if any(domain in url for domain in self.BLOCKED_DOMAINS):
                continue

            
            if any(word in title for word in self.BLOCKED_WORDS):
                continue

            filtered.append(result)

        return filtered