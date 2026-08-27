from app.services.database.catalogue_profile_repository import (
    CatalogueProfileRepository
)


class QueryTemplateService:
    """
    Turns the uploaded catalogue's products/categories into a set of
    targeted search queries, each combining one product with one
    buyer-type modifier - the "trade program" / "event planner" /
    "boutique hotel" phrasing that tends to land on a company's actual
    trade/wholesale contact page instead of a blocked directory
    listing, and on companies that plausibly buy this kind of product
    rather than any US/Canada company with a scrapable email.

    Deliberately does NOT run anything - it only builds the query
    strings. Running one is still an explicit, bounded action (see the
    "Run" button per query on the Search page), same philosophy as the
    "Analyze Next 5 Leads" button in Phase 3 - a single request/response
    Flask app with no background job runner shouldn't fire off a dozen
    full multi-adapter searches in one HTTP request.
    """

    # (label, query phrase). Kept separate from CatalogueProfile.buyer_types
    # so this works even before any AI-extracted buyer types exist, and so
    # the phrasing stays tuned to what actually gets past directory blocks.
    BUYER_TYPE_MODIFIERS = [
        ("Trade Program", '"trade program" OR "wholesale inquiries" OR "vendor application"'),
        ("Home Decor Boutique", '"home decor boutique"'),
        ("Boutique Hotel / Spa", 'boutique hotel OR spa OR wellness retreat'),
        ("Event Planner / Rentals", 'event planner OR wedding rentals OR venue decor rental'),
        ("Gift Shop", 'gift shop wholesale buyer'),
    ]

    MAX_QUERIES = 12

    def __init__(self, catalogue_repo=None):
        self.catalogue_repo = catalogue_repo or CatalogueProfileRepository()

    def _product_keywords(self, profile):

        if not profile:
            return []

        raw = ", ".join(filter(None, [
            profile.products,
            profile.categories
        ]))

        return [kw.strip() for kw in raw.split(",") if kw.strip()]

    def _modifiers(self, profile):

        modifiers = list(self.BUYER_TYPE_MODIFIERS)

        # Fold in whatever buyer types Gemini already extracted from the
        # catalogue during upload (Phase 1) - free extra targeting, no
        # extra AI call needed here.
        if profile and profile.buyer_types:

            for buyer_type in profile.buyer_types.split(","):

                buyer_type = buyer_type.strip()

                if buyer_type:
                    modifiers.append((buyer_type.title(), buyer_type))

        return modifiers

    def build_queries(self, max_queries=None):
        """
        Returns a list of dicts: {"query", "product", "buyer_type"}.
        Empty list if no catalogue has been uploaded yet - caller
        should fall back to manual keyword search in that case.

        Ordered breadth-first across products within each modifier
        (all products x Trade Program, then all products x next
        modifier, ...) so a low cap still covers every product at
        least once with the highest-value modifier before repeating.
        """

        profile = self.catalogue_repo.get()

        products = self._product_keywords(profile)

        if not products:
            return []

        cap = max_queries or self.MAX_QUERIES

        modifiers = self._modifiers(profile)

        queries = []

        for modifier_label, modifier_phrase in modifiers:

            for product in products:

                if len(queries) >= cap:
                    return queries

                queries.append({
                    "query": f"{product} {modifier_phrase}",
                    "product": product,
                    "buyer_type": modifier_label,
                })

        return queries
