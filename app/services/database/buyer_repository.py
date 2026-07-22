from app.extensions import db
from app.models import Buyer
from app.extensions import db


class BuyerRepository:

    def save(self, buyer):

        # Prevent duplicate websites
        existing = Buyer.query.filter_by(
            website=buyer.website
        ).first()

        if existing:
            return existing

        new_buyer = Buyer(
            company=buyer.company,
            buyer_name=buyer.buyer_name,
            email=buyer.email,
            website=buyer.website,
            snippet=buyer.snippet,
            country=buyer.country,
            source=buyer.source,
            category=buyer.category
        )

        db.session.add(new_buyer)
        db.session.commit()

        return new_buyer

    def get(self, buyer_id):

        return Buyer.query.get(buyer_id)

    def all(self):

        return Buyer.query.order_by(
            Buyer.id.desc()
        ).all()

    def all(self):
        buyers = Buyer.query.all()
        print(f"Total buyers in database: {len(buyers)}")
        return buyers

    def update_category(self, buyer_id, category):

        buyer = Buyer.query.get(buyer_id)

        if buyer:

            buyer.category = category

            db.session.commit()

        return buyer

    def update_email(self, buyer_id, email):

        buyer = Buyer.query.get(buyer_id)

        if buyer:

            buyer.email = email

            db.session.commit()

        return buyer

    def update_country(self, buyer_id, country):

        buyer = Buyer.query.get(buyer_id)

        if buyer:

            buyer.country = country

            db.session.commit()

        return buyer

    def update_status(self, buyer_id, status):

        buyer = Buyer.query.get(buyer_id)

        if buyer:

            buyer.status = status

            db.session.commit()

        return buyer

    def delete(self, buyer_id):

        buyer = Buyer.query.get(buyer_id)

        if buyer:

            db.session.delete(buyer)

            db.session.commit()

    def count(self):

        return Buyer.query.count()

    def count_by_category(self, category):

        return Buyer.query.filter_by(
            category=category
        ).count()

    def unknown_buyers(self):

        return Buyer.query.filter_by(
            category="Unknown"
        ).all()

    def update_categories(self, buyers):

        db.session.commit()

    def update_contact(
        self,
        buyer_id,
        email,
        country,
        phone
    ):

        buyer = Buyer.query.get(buyer_id)

        if not buyer:
            return

        if email:
            buyer.email = email

        if country and not buyer.country:
            buyer.country = country

        if phone:
            buyer.phone = phone

        db.session.commit()