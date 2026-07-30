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

    phone = db.Column(db.String(100))

    source = db.Column(db.String(100))

    category = db.Column(db.String(100), default="Unknown")

    status = db.Column(db.String(50), default="New")

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