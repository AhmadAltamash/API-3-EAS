from datetime import datetime

from app.extensions import db
from app.models import Buyer
from app.models import PipelineActivity


class StageService:
    """
    Single source of truth for the CRM pipeline stage ordering and for
    recording every stage transition to the activity timeline.

    The ordered stages before "Contacted" (Discovered, Qualified, Buyer
    Identified, Email Verified) can be reached automatically by the app
    itself, based on real signals already available:

      - Discovered      -> a buyer record is created
      - Qualified       -> the buyer has been AI-analyzed (Phase 3)
      - Buyer Identified -> analysis found a named decision-maker
      - Email Verified   -> analysis confirmed the email domain via MX
      - Contacted        -> a campaign email was actually sent

    Everything after Contacted (Replied, Interested, Quotation
    Requested/Sent, Sample Requested, Negotiation, Order Won/Lost)
    reflects things that happen outside this app (a reply arriving, a
    phone call, a sample being shipped) - there's no automated reply
    detection yet (that needs an IMAP/inbox integration, which is a
    separate, larger piece of work), so those are set manually by
    whoever is running the account, from the buyer detail page.
    """

    STAGE_ORDER = [
        "Discovered",
        "Qualified",
        "Buyer Identified",
        "Email Verified",
        "Contacted",
        "Replied",
        "Interested",
        "Quotation Requested",
        "Quotation Sent",
        "Sample Requested",
        "Negotiation",
        "Order Won",
        "Order Lost",
    ]

    def stage_index(self, stage):

        try:
            return self.STAGE_ORDER.index(stage)
        except ValueError:
            return 0

    def log_activity(self, buyer_id, stage, note=None):

        activity = PipelineActivity(
            buyer_id=buyer_id,
            stage=stage,
            note=note
        )

        db.session.add(activity)
        db.session.commit()

    def advance_to(self, buyer, new_stage, note=None):
        """
        Used by automatic hooks elsewhere in the app. Only moves the
        buyer FORWARD in STAGE_ORDER - never regresses a stage a human
        may have already manually corrected, and never re-logs a stage
        the buyer has already passed through.
        """

        if buyer is None or new_stage not in self.STAGE_ORDER:
            return buyer

        current_index = self.stage_index(buyer.pipeline_stage or "Discovered")
        new_index = self.stage_index(new_stage)

        if new_index <= current_index:
            return buyer

        buyer.pipeline_stage = new_stage

        db.session.commit()

        self.log_activity(buyer.id, new_stage, note)

        return buyer

    def set_stage_manual(self, buyer_id, new_stage, note=None):
        """
        Used by the buyer detail page - a human can set any stage at
        any time (sales reality: sometimes a lead needs to be moved
        back, or a stage skipped), always logged to the timeline.
        """

        buyer = Buyer.query.get(buyer_id)

        if buyer is None:
            return None

        if new_stage not in self.STAGE_ORDER:
            return buyer

        buyer.pipeline_stage = new_stage

        db.session.commit()

        self.log_activity(buyer.id, new_stage, note)

        return buyer

    def get_timeline(self, buyer_id):

        return PipelineActivity.query.filter_by(
            buyer_id=buyer_id
        ).order_by(
            PipelineActivity.created_at.asc()
        ).all()

    def is_contacted_or_later(self, buyer):

        if buyer is None or not buyer.pipeline_stage:
            return False

        return self.stage_index(buyer.pipeline_stage) >= self.stage_index("Contacted")

    def counts_by_stage(self):
        """
        For the pipeline funnel widget on Reports - returns an ordered
        list of (stage, count) tuples, in STAGE_ORDER, including stages
        with zero buyers so the funnel always shows the full shape.
        """

        rows = db.session.query(
            Buyer.pipeline_stage,
            db.func.count(Buyer.id)
        ).group_by(
            Buyer.pipeline_stage
        ).all()

        counts = {stage: 0 for stage in self.STAGE_ORDER}

        for stage, count in rows:
            if stage in counts:
                counts[stage] = count
            elif stage is None:
                counts["Discovered"] += count

        return [(stage, counts[stage]) for stage in self.STAGE_ORDER]
