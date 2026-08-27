from app.services.database.catalogue_profile_repository import (
    CatalogueProfileRepository
)


class RelevanceFilter:
    """
    Rejects buyers that don't plausibly deal in what the uploaded
    catalogue says we sell. This runs at ingestion time (inside
    BuyerPipeline), before a buyer ever reaches the database - it's
    the missing counterpart to LeadIntelligenceService's Phase 3
    product-match %, which only runs *after* a buyer is already saved.

    Deliberately cheap: plain keyword/phrase matching against text we
    already have (search snippet + homepage text), no extra Gemini
    calls per candidate. If no catalogue has been uploaded yet, this
    is a no-op so existing behavior is unaffected.
    """

    def __init__(self, catalogue_repo=None):
        self.catalogue_repo = catalogue_repo or CatalogueProfileRepository()

    def _keywords(self, profile):

        if not profile:
            return []

        raw = ", ".join(filter(None, [
            profile.products,
            profile.categories,
            profile.materials
        ]))

        keywords = [
            kw.strip().lower()
            for kw in raw.split(",")
            if kw.strip()
        ]

        return keywords

    def get_keywords(self):
        """
        Loads the catalogue keywords once. Call this from the main
        request thread (where the Flask app context is active) and
        pass the result into is_relevant() for every candidate -
        NOT from inside a ThreadPoolExecutor worker, since worker
        threads don't have the app context needed for a DB query.
        """
        return self._keywords(self.catalogue_repo.get())

    def is_relevant(self, buyer, page_text="", keywords=None):
        """
        buyer: a Buyer instance with .company / .snippet already set.
        page_text: cleaned homepage text (optional - snippet alone is
        often enough, page_text improves recall).
        keywords: precomputed list from get_keywords(). Pass this in
        whenever is_relevant() might run outside the main request
        thread (e.g. inside a worker pool) - if omitted, this method
        will query the DB itself, which only works with an active
        app context.

        Returns True (keep) if no catalogue is on file, or if we
        can't tell either way - this filter should never be the
        reason zero results come back for a brand-new setup.
        """

        if keywords is None:
            keywords = self.get_keywords()

        if not keywords:
            return True

        haystack = " ".join(filter(None, [
            buyer.company,
            buyer.snippet,
            page_text
        ])).lower()

        if not haystack.strip():
            return True

        for kw in keywords:

            if kw in haystack:
                return True

            # loose singular/plural match ("candle holder" vs "holders")
            if kw.endswith("s") and kw[:-1] in haystack:
                return True

            if not kw.endswith("s") and (kw + "s") in haystack:
                return True

        return False
