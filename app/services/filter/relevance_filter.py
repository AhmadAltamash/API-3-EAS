from app.services.database.catalogue_profile_repository import (
    CatalogueProfileRepository
)


class RelevanceFilter:
    """
    Scores how well a buyer plausibly matches what the uploaded
    catalogue says we sell. This runs at ingestion time (inside
    BuyerPipeline), before a buyer ever reaches the database - it's
    the cheap counterpart to LeadIntelligenceService's Phase 3
    product-match %, which uses a real Gemini call and only runs
    *after* a buyer is already saved (via the "Analyze" step).

    Deliberately cheap: plain keyword/phrase matching against text we
    already have (search snippet + homepage text), no extra Gemini
    calls per candidate. If no catalogue has been uploaded yet, this
    is a no-op so existing behavior is unaffected.

    This used to be a hard True/False gate. It's now a 0-100 score,
    because a boolean throws away information a scored version keeps:
    a company that matches on one loosely-related keyword and one that
    matches on three exact ones used to look identical (both "pass") -
    now they're visibly different, and BuyerPipeline only rejects the
    genuine zero-signal case (no catalogue keyword found anywhere),
    not the "matched but not strongly" case that a stricter reading of
    the old boolean could have silently thrown away.
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
        pass the result into score() for every candidate - NOT from
        inside a ThreadPoolExecutor worker, since worker threads don't
        have the app context needed for a DB query.
        """
        return self._keywords(self.catalogue_repo.get())

    def _keyword_matches(self, keyword, haystack):

        if keyword in haystack:
            return True

        # loose singular/plural match ("candle holder" vs "holders")
        if keyword.endswith("s") and keyword[:-1] in haystack:
            return True

        if not keyword.endswith("s") and (keyword + "s") in haystack:
            return True

        return False

    def score(self, buyer, page_text="", keywords=None):
        """
        buyer: a Buyer instance with .company / .snippet already set.
        page_text: cleaned homepage text (optional - snippet alone is
        often enough, page_text improves recall).
        keywords: precomputed list from get_keywords(). Pass this in
        whenever score() might run outside the main request thread
        (e.g. inside a worker pool) - if omitted, this method will
        query the DB itself, which only works with an active app
        context.

        Returns:
        - None if no catalogue is on file - "not evaluated", not
          "zero relevance". Callers should treat this as "keep,
          we genuinely can't tell" exactly like the old is_relevant()
          did for a brand-new setup with nothing uploaded yet.
        - 0-100 otherwise: percentage of catalogue keywords found,
          with a company-name match weighted higher than a snippet/
          page-text-only match (a keyword actually in the company
          name is a much stronger signal than one merely appearing
          somewhere on the page).
        """

        if keywords is None:
            keywords = self.get_keywords()

        if not keywords:
            return None

        company_text = (buyer.company or "").lower()

        rest_text = " ".join(filter(None, [
            buyer.snippet,
            page_text
        ])).lower()

        if not company_text.strip() and not rest_text.strip():
            return None

        matched_weight = 0.0

        for kw in keywords:

            if self._keyword_matches(kw, company_text):
                matched_weight += 1.0
            elif self._keyword_matches(kw, rest_text):
                matched_weight += 0.6

        raw_score = (matched_weight / len(keywords)) * 100

        return round(min(raw_score, 100))

    def is_relevant(self, buyer, page_text="", keywords=None):
        """
        Kept for anything still calling the old boolean interface.
        A genuine zero-signal match (score 0, catalogue present) is
        the only case this treats as "not relevant" - matches "not
        strongly relevant" is still True here, same behavior as
        score() being used with a >0 threshold.
        """

        result = self.score(buyer, page_text, keywords)

        return result is None or result > 0
