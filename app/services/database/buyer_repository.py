from app.extensions import db
from app.models import Buyer
from app.services.crm.stage_service import StageService


class BuyerRepository:

    def __init__(self):
        self.stages = StageService()

    def save(self, buyer):

        # Prevent duplicate websites - guard against a falsy website
        # short-circuit-matching some other record that also has no
        # website on file yet (rare, but two different companies both
        # showing website=None used to silently collapse into one).
        existing = None

        if buyer.website:

            existing = Buyer.query.filter_by(
                website=buyer.website
            ).first()

        # Prevent duplicate email addresses - the same inbox (often a
        # generic info@/sales@ address) can turn up on more than one page
        # of the same site and would otherwise be saved as two separate
        # buyer records, burning two campaign send-slots on one company.
        if not existing and buyer.email:

            existing = Buyer.query.filter_by(
                email=buyer.email
            ).first()

        if existing:

            # A duplicate isn't a dead end - it means this company is
            # already tracked (possibly already in Sent Companies /
            # mid-way through the CRM pipeline). Backfill anything this
            # pass learned that the earlier save missed, so the record
            # your Follow-Up/Sent Companies pages point to keeps
            # improving instead of staying frozen at the first pass.
            self._merge_new_info(existing, buyer)

            return existing, False

        new_buyer = Buyer(
            company=buyer.company,
            buyer_name=buyer.buyer_name,
            email=buyer.email,
            website=buyer.website,
            snippet=buyer.snippet,
            country=buyer.country,
            source=buyer.source,
            category=buyer.category,
            phone=buyer.phone,
            email_live_verified=getattr(buyer, "email_live_verified", None),
            product_match_percent=getattr(buyer, "product_match_percent", None),
            pipeline_stage="Discovered"
        )

        db.session.add(new_buyer)
        db.session.commit()

        self.stages.log_activity(
            new_buyer.id,
            "Discovered",
            note=f"Found via {buyer.source or 'search'}"
        )

        return new_buyer, True

    def _merge_new_info(self, existing, incoming):

        changed = False

        if incoming.phone and not existing.phone:
            existing.phone = incoming.phone
            changed = True

        if incoming.country and not existing.country:
            existing.country = incoming.country
            changed = True

        if incoming.snippet and not existing.snippet:
            existing.snippet = incoming.snippet
            changed = True

        if incoming.buyer_name and not existing.buyer_name:
            existing.buyer_name = incoming.buyer_name
            changed = True

        # A later live-confirmed find should upgrade an earlier
        # unverified record - never the other way around (an
        # unverified re-find shouldn't downgrade a confirmed one).
        if getattr(incoming, "email_live_verified", None) and not existing.email_live_verified:
            existing.email_live_verified = True
            changed = True

        # Same "only ever improve, never downgrade" rule for the
        # relevance score - a re-find that happened to see stronger
        # keyword evidence (e.g. a company-name match this time
        # instead of only a snippet match before) should raise the
        # stored score; a weaker rediscovery shouldn't erase a
        # stronger one already on file, and an AI-refined score from
        # the Phase 3 "Analyze" step should never get overwritten by
        # this cheap keyword estimate either.
        incoming_score = getattr(incoming, "product_match_percent", None)

        if (
            incoming_score is not None
            and (existing.product_match_percent is None or incoming_score > existing.product_match_percent)
            and existing.analyzed_at is None
        ):
            existing.product_match_percent = incoming_score
            changed = True

        if changed:
            db.session.commit()

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

    def set_follow_up(self, buyer_id, needs_follow_up):
        """
        Used by the Sent Companies page toggle. Setting True also
        advances the buyer to the "Replied" CRM stage (advance_to()
        only moves forward, so this is safe to call repeatedly and
        never regresses a stage a human has already moved further
        along manually). Setting False just clears the flag - it
        does not undo the stage, since a real reply did happen even
        if the toggle was clicked by mistake and un-clicked.
        """

        buyer = Buyer.query.get(buyer_id)

        if not buyer:
            return None

        buyer.needs_follow_up = needs_follow_up

        db.session.commit()

        if needs_follow_up:
            self.stages.advance_to(
                buyer, "Replied",
                note="Marked as responded on Sent Companies page"
            )

        return buyer

    def follow_up_buyers(self):
        """
        Buyers toggled "Yes" on Sent Companies and not yet re-cleared -
        the audience for the Follow-Up Emails page/send.
        """

        return Buyer.query.filter_by(
            needs_follow_up=True
        ).order_by(
            Buyer.id.desc()
        ).all()

    def find_or_create_manual(self, email):
        """
        Used by the Follow-Up Emails page's "extra email" field, for
        addresses an intern hands you that aren't in the buyer database
        yet (not found by a search, not toggled from Sent Companies).
        Reuses the normal email-dedup rule - if this address is already
        a known buyer, that existing record is used (and gains a
        Follow-Up activity entry) rather than creating a second one.
        """

        email = email.strip().lower()

        existing = Buyer.query.filter_by(email=email).first()

        if existing:
            return existing

        domain = email.split("@")[-1] if "@" in email else "unknown"

        buyer = Buyer(
            company=f"Manual Contact ({domain})",
            email=email,
            source="Manual Entry",
            category="Manual",
            email_live_verified=False,
            pipeline_stage="Discovered"
        )

        db.session.add(buyer)
        db.session.commit()

        self.stages.log_activity(
            buyer.id,
            "Discovered",
            note="Added manually on the Follow-Up Emails page"
        )

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