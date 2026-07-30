from app.services.search.search_manager import SearchManager
from app.services.database.buyer_repository import BuyerRepository
from app.services.ai.gemini_classifier import GeminiService
from app.services.export.export_service import ExportService

class BuyerService:

    def __init__(self):

        self.search_manager = SearchManager()

        self.repository = BuyerRepository()

        self.ai = GeminiService()

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

        for buyer in buyers:

            saved = self.repository.save(
                buyer
            )

            saved_buyers.append(saved)

        self.export.buyers_csv(
            self.repository.all()
        )

        return saved_buyers

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

        self.repository.update_category(

            buyer.id,

            category

        )

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

        return count