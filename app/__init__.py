from flask import Flask

from config import Config

from .extensions import db, migrate

from .routes.buyers import buyers_bp
from .routes.classify import classify_bp
from .routes.campaign import campaign_bp
from .routes.reports import reports_bp
from .routes.settings import settings_bp
from .routes.dashboard import dashboard_bp
from .routes.search import search_bp
from app.routes.enrichment import enrichment_bp
from app.routes.sent_companies import sent_companies_bp
from app.routes.catalogue import catalogue_bp
from app.routes.follow_up import follow_up_bp

from app.services.timezone.send_time_service import SendTimeService




def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    migrate.init_app(app, db)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(buyers_bp)
    app.register_blueprint(classify_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(enrichment_bp)
    app.register_blueprint(sent_companies_bp)
    app.register_blueprint(catalogue_bp)
    app.register_blueprint(follow_up_bp)

    # Lets templates call send_time_info(country, state) directly,
    # e.g. in buyers.html to show each buyer's local/IST send window.
    app.jinja_env.globals["send_time_info"] = SendTimeService().get_send_time_info
    

    # Create database tables automatically
    with app.app_context():
        db.create_all()
        _ensure_new_columns(app)

    return app


def _ensure_new_columns(app):
    """
    Self-healing schema check, run on every startup.

    db.create_all() only creates tables that don't exist yet - it never
    alters a table that's already there. So on an existing database from
    before this update, newly-added model columns (buyers.state,
    email_logs.website) would silently be missing and cause
    'no such column' errors at query time.

    This checks the app's actual live database (via its own engine, so
    there's no guessing about file paths/instance folders) and adds any
    missing columns directly. Safe to run on every startup - it's a
    no-op once the columns exist.
    """

    from sqlalchemy import inspect, text

    if db.engine.dialect.name != "sqlite":
        # ALTER TABLE ADD COLUMN is broadly supported, but this project
        # is built around sqlite - flag it rather than guess at another
        # dialect's syntax.
        print(
            "[schema check] Non-SQLite database detected - skipping "
            "automatic column check. If you see 'no such column' errors "
            "for buyers.state or email_logs.website, add them manually."
        )
        return

    inspector = inspect(db.engine)

    existing_tables = inspector.get_table_names()

    if "buyers" in existing_tables:

        buyer_columns = {c["name"] for c in inspector.get_columns("buyers")}

        # (column name, SQL type) for every column added after the
        # original schema - each is only added if it isn't there yet.
        new_buyer_columns = [
            ("state", "VARCHAR(50)"),
            ("lead_score", "INTEGER"),
            ("outreach_priority", "VARCHAR(20)"),
            ("lead_score_reasons", "TEXT"),
            ("product_match_percent", "INTEGER"),
            ("relevant_categories", "VARCHAR(500)"),
            ("style_estimate", "VARCHAR(150)"),
            ("positioning_estimate", "VARCHAR(100)"),
            ("recommended_products", "TEXT"),
            ("decision_maker_name", "VARCHAR(150)"),
            ("decision_maker_title", "VARCHAR(150)"),
            ("email_domain_verified", "BOOLEAN"),
            ("analyzed_at", "DATETIME"),
            ("pipeline_stage", "VARCHAR(50)"),
            ("needs_follow_up", "BOOLEAN"),
        ]

        added_pipeline_stage = False
        added_needs_follow_up = False

        for column_name, column_type in new_buyer_columns:

            if column_name not in buyer_columns:
                db.session.execute(text(
                    f"ALTER TABLE buyers ADD COLUMN {column_name} {column_type}"
                ))
                db.session.commit()
                print(f"[schema check] Added missing column: buyers.{column_name}")

                if column_name == "pipeline_stage":
                    added_pipeline_stage = True

                if column_name == "needs_follow_up":
                    added_needs_follow_up = True

        if added_pipeline_stage:

            # ALTER TABLE ADD COLUMN doesn't apply the model's Python-side
            # default to rows that already existed - backfill them once so
            # every existing buyer starts the CRM pipeline at "Discovered"
            # instead of sitting at NULL.
            db.session.execute(text(
                "UPDATE buyers SET pipeline_stage = 'Discovered' "
                "WHERE pipeline_stage IS NULL"
            ))
            db.session.commit()
            print("[schema check] Backfilled existing buyers to pipeline_stage='Discovered'")

        if added_needs_follow_up:

            # Same story: existing rows get NULL, not the Python-side
            # False default, until backfilled once.
            db.session.execute(text(
                "UPDATE buyers SET needs_follow_up = 0 "
                "WHERE needs_follow_up IS NULL"
            ))
            db.session.commit()
            print("[schema check] Backfilled existing buyers to needs_follow_up=False")

    if "email_logs" in existing_tables:

        log_columns = {c["name"] for c in inspector.get_columns("email_logs")}

        if "website" not in log_columns:
            db.session.execute(text(
                "ALTER TABLE email_logs ADD COLUMN website VARCHAR(300)"
            ))
            db.session.commit()
            print("[schema check] Added missing column: email_logs.website")

    # catalogue_profile is a brand new table (not an existing one gaining
    # a column), so db.create_all() already creates it - nothing to do
    # here for it specifically.