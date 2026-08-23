from app.extensions import db
from app.models import Buyer
from app.services.crm.stage_service import StageService


class BuyerRepository:

    def __init__(self):
        self.stages = StageService()

    def save(self, buyer):

        # Prevent duplicate websites
        existing = Buyer.query.filter_by(
            website=buyer.website
        ).first()

        if existing:
            return existing

        # Prevent duplicate email addresses - the same inbox (often a
        # generic info@/sales@ address) can turn up on more than one page
        # of the same site and would otherwise be saved as two separate
        # buyer records, burning two campaign send-slots on one company.
        if buyer.email:

            existing_email = Buyer.query.filter_by(
                email=buyer.email
            ).first()

            if existing_email:
                return existing_email

        new_buyer = Buyer(
            company=buyer.company,
            buyer_name=buyer.buyer_name,
            email=buyer.email,
            website=buyer.website,
            snippet=buyer.snippet,
            country=buyer.country,
            source=buyer.source,
            category=buyer.category,
            pipeline_stage="Discovered"
        )

        db.session.add(new_buyer)
        db.session.commit()

        self.stages.log_activity(
            new_buyer.id,
            "Discovered",
            note=f"Found via {buyer.source or 'search'}"
        )

        return new_buyer

    def get(self, buyer_id):

        return Buyer.query.get(buyer_id)

    def all(self):

        return Buyer.query.order_by(
            Buyer.id.desc()
        ).all()

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

    def unscored_buyers(self, limit=5):

        return Buyer.query.filter(
            Buyer.lead_score.is_(None)
        ).order_by(
            Buyer.id.desc()
        ).limit(limit).all()

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

    def delete_all(self):

        Buyer.query.delete()

        db.session.commit()

    def contactable_buyers(self):
        """
        Buyers not yet at "Contacted" or a later CRM stage - used by the
        campaign sender so it never emails someone twice. Replaces the
        old approach of deleting a buyer right after a successful send,
        which made a CRM pipeline impossible (there'd be nothing left to
        track through Replied/Interested/Negotiation/etc).
        """

        contacted_index = self.stages.stage_index("Contacted")

        pre_contact_stages = self.stages.STAGE_ORDER[:contacted_index]

        return Buyer.query.filter(
            db.or_(
                Buyer.pipeline_stage.in_(pre_contact_stages),
                Buyer.pipeline_stage.is_(None)
            )
        ).order_by(
            Buyer.id.desc()
        ).all()

    def add_inbound_lead(
        self,
        company,
        email=None,
        website=None,
        country=None,
        state=None,
        buyer_name=None,
        note=None
    ):
        """
        Manual entry point for a company that approached us directly,
        rather than one discovered via search - still flows through the
        same CRM pipeline from here on.
        """

        new_buyer = Buyer(
            company=company,
            buyer_name=buyer_name,
            email=email,
            website=website,
            country=country,
            state=state,
            source="Inbound",
            category="Unknown",
            pipeline_stage="Discovered"
        )

        db.session.add(new_buyer)
        db.session.commit()

        self.stages.log_activity(
            new_buyer.id,
            "Discovered",
            note=note or "Inbound lead - contacted us directly"
        )

        return new_buyer

    def update_intelligence(self, buyer_id, data):
        """
        data: the dict returned by LeadIntelligenceService.analyze().
        """

        from datetime import datetime

        buyer = Buyer.query.get(buyer_id)

        if not buyer:
            return None

        buyer.lead_score = data.get("lead_score")
        buyer.outreach_priority = data.get("outreach_priority")

        reasons = data.get("lead_score_reasons") or []
        buyer.lead_score_reasons = "\n".join(reasons)

        buyer.product_match_percent = data.get("product_match_percent")

        relevant_categories = data.get("relevant_categories") or []
        buyer.relevant_categories = ", ".join(relevant_categories)

        buyer.style_estimate = data.get("style_estimate")
        buyer.positioning_estimate = data.get("positioning_estimate")

        recommended_products = data.get("recommended_products") or []
        buyer.recommended_products = ", ".join(recommended_products)

        buyer.decision_maker_name = data.get("decision_maker_name")
        buyer.decision_maker_title = data.get("decision_maker_title")
        buyer.email_domain_verified = data.get("email_domain_verified")
        buyer.analyzed_at = datetime.utcnow()

        db.session.commit()

        # Being analyzed at all counts as qualification effort
        self.stages.advance_to(
            buyer, "Qualified",
            note=f"Lead score {buyer.lead_score}/100 ({buyer.outreach_priority})"
        )

        if buyer.decision_maker_name:
            self.stages.advance_to(
                buyer, "Buyer Identified",
                note=f"{buyer.decision_maker_name} - {buyer.decision_maker_title}"
            )

        if buyer.email_domain_verified:
            self.stages.advance_to(
                buyer, "Email Verified",
                note="MX record confirmed for email domain"
            )

        return buyer