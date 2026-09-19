from datetime import datetime, date
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

    # Distinct from email_domain_verified above (which only checks the
    # domain has valid MX records). This tracks provenance: True means
    # this app fetched the live page itself and found the email there;
    # False/None means it came from somewhere we didn't independently
    # confirm - Gemini's own knowledge (AI Discovery, when the target
    # site blocks our fetcher) or a manually-curated CSV import.
    email_live_verified = db.Column(db.Boolean)

    # Same honesty pattern as email_live_verified above, applied to
    # country. True means the page itself confirmed it (a state name,
    # "United States"/"Canada", a .us/.ca domain, etc). False means the
    # page gave no signal at all and this was assumed from what
    # country the search itself was scoped to - a real, useful lead,
    # just one this app didn't independently verify. None means this
    # predates the feature (an old row saved before this distinction
    # existed).
    country_confirmed = db.Column(db.Boolean)

    analyzed_at = db.Column(db.DateTime)

    # -------------------------------------------------------------
    # CRM pipeline (Phase 4)
    # -------------------------------------------------------------

    pipeline_stage = db.Column(db.String(50), default="Discovered")

    # Toggled from the Sent Companies page: "did this company respond?"
    # True moves the buyer to the Replied stage and makes them eligible
    # for the Follow-Up Emails page/send.
    needs_follow_up = db.Column(db.Boolean, default=False)

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

    buyer = db.relationship("Buyer", backref="email_logs")

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

class Intern(db.Model):
    """
    A team member the lead is tracking outreach performance for.
    emails_sent/automated_responses/positive_responses are running
    totals - updated by ADDING today's numbers on top (see
    InternRepository.append_stats), never by overwriting them.
    total_working_days is NOT stored here - it's calculated from
    date_joined to the current date every time it's read (see the
    property below), so it's always correct without needing a daily
    update job.
    """

    __tablename__ = "interns"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    status = db.Column(db.String(20), default="Active")

    emails_sent = db.Column(db.Integer, default=0)

    automated_responses = db.Column(db.Integer, default=0)

    positive_responses = db.Column(db.Integer, default=0)

    date_joined = db.Column(db.Date, nullable=False)

    # Set only when status is "Discontinued" - the specific day the
    # lead says this person stopped, which may not be today (e.g.
    # backfilling someone who left last week). Once set,
    # total_working_days freezes as of this date instead of
    # continuing to grow with today's date.
    date_discontinued = db.Column(db.Date)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    @property
    def total_working_days(self):

        if not self.date_joined:
            return 0

        end_date = self.date_discontinued or date.today()

        delta = end_date - self.date_joined

        return max(delta.days, 0)
