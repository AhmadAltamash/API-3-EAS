from app.extensions import db
from app.models import CatalogueProfile


class CatalogueProfileRepository:

    def get(self):

        return CatalogueProfile.query.get(1)

    def save(self, analysis):
        """
        analysis: the dict returned by CatalogueAnalyzer.analyze()
        (products/categories/materials/industries/buyer_types lists).
        Always writes to row id=1 - only the most recent catalogue is
        kept, since that's what buyer analysis should be compared against.
        """

        profile = CatalogueProfile.query.get(1)

        if profile is None:
            profile = CatalogueProfile(id=1)
            db.session.add(profile)

        profile.products = ", ".join(analysis.get("products", []))
        profile.categories = ", ".join(analysis.get("categories", []))
        profile.materials = ", ".join(analysis.get("materials", []))
        profile.industries = ", ".join(analysis.get("industries", []))
        profile.buyer_types = ", ".join(analysis.get("buyer_types", []))

        db.session.commit()

        return profile
