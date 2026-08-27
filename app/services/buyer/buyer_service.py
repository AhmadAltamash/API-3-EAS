import time

from app.services.search.search_manager import SearchManager
from app.services.database.buyer_repository import BuyerRepository
from app.services.ai.gemini_classifier import GeminiService
from app.services.ai.lead_intelligence_service import LeadIntelligenceService
from app.services.export.export_service import ExportService

class BuyerService:

    def __init__(self):

        self.search_manager = SearchManager()

        self.repository = BuyerRepository()

        self.ai = GeminiService()

        self.intelligence = LeadIntelligenceService()

        self.export = ExportService()

    # -----------------------------
    # Search Buyers
    # -----------------------------
    def search_buyers(self, keyword, source):

        buyers = self.search_manager.search(
            source,
            keyword
        )

        saved_buyers = []

        new_count = 0
        duplicate_count = 0

        for buyer in buyers:

            saved, is_new = self.repository.save(
                buyer
            )

            saved_buyers.append(saved)

            if is_new:
                new_count += 1
            else:
                duplicate_count += 1

        self.export.buyers_csv(
            self.repository.all()
        )

        return {
            "buyers": saved_buyers,
            "new_count": new_count,
            "duplicate_count": duplicate_count
        }

    # -----------------------------
    # Get All Buyers
    # -----------------------------
    def all_buyers(self):

        return self.repository.all()

    # -----------------------------
    # Get Single Buyer
    # -----------------------------
    def get_buyer(self, buyer_id):

        return self.repository.get(
            buyer_id
        )

    # -----------------------------
    # AI Classification
    # -----------------------------
    def classify_buyer(self, buyer_id):

        buyer = self.repository.get(
            buyer_id
        )

        if buyer is None:

            return None

        category = self.ai.classify(
            buyer.company,
            buyer.website,
            buyer.snippet
        )

        print("Category =", category)

        self.repository.update_category(
            buyer.id,
            category
        )

        return category

    # -----------------------------
    # AI Lead Intelligence (Phase 3)
    # -----------------------------
    def analyze_buyer(self, buyer_id):

        buyer = self.repository.get(
            buyer_id
        )

        if buyer is None:
            return None

        data = self.intelligence.analyze(buyer)

        self.repository.update_intelligence(
            buyer.id,
            data
        )

        return data

    def analyze_unscored(self, limit=5):
        """
        Analyzes up to `limit` not-yet-scored buyers in one call. Kept
        deliberately small - unlike classify (one quick API call per
        buyer), a full analysis does a website fetch, a possible About-
        page fetch, a Gemini call, and an MX lookup per buyer, so this
        runs synchronously within a single web request and shouldn't be
        pointed at hundreds of buyers at once.
        """

        buyers = self.repository.unscored_buyers(limit=limit)

        count = 0

        for buyer in buyers:

            data = self.intelligence.analyze(buyer)

            self.repository.update_intelligence(
                buyer.id,
                data
            )

            count += 1

            time.sleep(2)

        return count

    # -----------------------------
    # Delete Buyer
    # -----------------------------
    def delete_buyer(self, buyer_id):

        self.repository.delete(buyer_id)

        self.export.buyers_csv(
            self.repository.all()
        )

    def delete_all_buyers(self):

        self.repository.delete_all()

        self.export.buyers_csv([])

    # -----------------------------
    # Dashboard
    # -----------------------------
    def total_buyers(self):

        return self.repository.count()

    def total_importers(self):

        return self.repository.count_by_category(
            "Importer"
        )

    def total_exporters(self):

        return self.repository.count_by_category(
            "Exporter"
        )

    def total_wholesalers(self):

        return self.repository.count_by_category(
            "Wholesaler"
        )

    def total_distributors(self):

        return self.repository.count_by_category(
            "Distributor"
        )

    def total_manufacturers(self):

        return self.repository.count_by_category(
            "Manufacturer"
        )

    def total_retailers(self):

        return self.repository.count_by_category(
            "Retailer"
        )
    
    def classify_all(self):

        buyers = self.repository.unknown_buyers()

        count = 0

        for buyer in buyers:

            category = self.ai.classify(

                buyer.company,

                buyer.website,

                buyer.snippet

            )

            self.repository.update_category(

                buyer.id,

                category

            )

            count += 1

            # Small gap between calls so a batch of buyers doesn't burst
            # past Gemini's requests-per-minute limit and start tripping
            # 429/503 errors on every subsequent buyer.
            time.sleep(2)

        return count