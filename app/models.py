from datetime import datetime
from app.extensions import db


class Campaign(db.Model):
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)

    campaign_name = db.Column(db.String(150), nullable=False)

    subject = db.Column(db.String(255), nullable=False)

    body = db.Column(db.Text, nullable=False)

    recipients = db.Column(db.Integer, default=0)

    sent = db.Column(db.Integer, default=0)

    failed = db.Column(db.Integer, default=0)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Buyer(db.Model):
    __tablename__ = "buyers"

    id = db.Column(db.Integer, primary_key=True)

    company = db.Column(db.String(200), nullable=False)

    buyer_name = db.Column(db.String(200))

    email = db.Column(db.String(255))

    website = db.Column(db.String(300), unique=True)

    snippet = db.Column(db.Text)

    country = db.Column(db.String(100))

    state = db.Column(db.String(50))

    phone = db.Column(db.String(100))

    source = db.Column(db.String(100))

    category = db.Column(db.String(100), default="Unknown")

    status = db.Column(db.String(50), default="New")

    # -------------------------------------------------------------
    # Lead intelligence (Phase 3) - populated by LeadIntelligenceService
    # when a buyer is analyzed. All nullable: a buyer that hasn't been
    # analyzed yet simply has None/empty values for these.
    # -------------------------------------------------------------

    lead_score = db.Column(db.Integer)

    outreach_priority = db.Column(db.String(20))

    lead_score_reasons = db.Column(db.Text)

    product_match_percent = db.Column(db.Integer)

    relevant_categories = db.Column(db.String(500))

    style_estimate = db.Column(db.String(150))

    positioning_estimate = db.Column(db.String(100))

    recommended_products = db.Column(db.Text)

    decision_maker_name = db.Column(db.String(150))

    decision_maker_title = db.Column(db.String(150))

    email_domain_verified = db.Column(db.Boolean)

    analyzed_at = db.Column(db.DateTime)

    # -------------------------------------------------------------
    # CRM pipeline (Phase 4)
    # -------------------------------------------------------------

    pipeline_stage = db.Column(db.String(50), default="Discovered")

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class EmailLog(db.Model):

    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey("buyers.id"),
        nullable=False
    )

    company = db.Column(db.String(255))

    receiver = db.Column(db.String(255))

    website = db.Column(db.String(300))

    subject = db.Column(db.String(255))

    body = db.Column(db.Text)

    status = db.Column(
        db.String(50),
        default="Sent"
    )

    sent_at = db.Column(
        db.DateTime,
        default=db.func.now()
    )


class CatalogueProfile(db.Model):
    """
    Stores the most recently AI-analyzed product catalogue (see
    CatalogueAnalyzer / /catalogue page). Single-row table - saving a
    new catalogue overwrites row id=1. Used by LeadIntelligenceService
    to score how well a buyer's business matches what we actually sell.

    List-like fields are stored as simple comma-separated text rather
    than JSON, since they're always short, human-curated lists and this
    keeps them trivial to read back out in templates without parsing.
    """

    __tablename__ = "catalogue_profile"

    id = db.Column(db.Integer, primary_key=True)

    products = db.Column(db.Text)

    categories = db.Column(db.Text)

    materials = db.Column(db.Text)

    industries = db.Column(db.Text)

    buyer_types = db.Column(db.Text)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class PipelineActivity(db.Model):
    """
    One row per stage transition for a buyer - the "complete activity
    timeline" for a company moving through the CRM pipeline (Discovered
    -> Qualified -> Buyer Identified -> Email Verified -> Contacted ->
    Replied -> Interested -> Quotation Requested -> Quotation Sent ->
    Sample Requested -> Negotiation -> Order Won/Lost).

    Rows are append-only - the current stage lives on Buyer.pipeline_stage,
    this table is purely the history of how it got there.
    """

    __tablename__ = "pipeline_activity"

    id = db.Column(db.Integer, primary_key=True)

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey("buyers.id"),
        nullable=False
    )

    stage = db.Column(db.String(50), nullable=False)

    note = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )