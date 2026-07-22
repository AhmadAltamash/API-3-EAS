from app.services.database.buyer_repository import BuyerRepository
from app.services.extractor.contact_extractor import ContactExtractor


class EnrichmentService:

    def __init__(self):
        self.repository = BuyerRepository()
        self.extractor = ContactExtractor()

    def enrich_all(self):

        buyers = self.repository.all()

        enriched = 0
        skipped = 0

        for buyer in buyers:

            if not buyer.website:
                skipped += 1
                continue

            if buyer.email:
                skipped += 1
                continue

            print(f"Checking {buyer.company}")

            data = self.extractor.extract(buyer.website)

            self.repository.update_contact(
                buyer.id,
                data["email"],
                data["country"],
                data["phone"]
            )

            enriched += 1

        return {
            "enriched": enriched,
            "skipped": skipped,
            "total": len(buyers)
        }