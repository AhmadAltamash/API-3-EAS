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
from app.routes.campaign_history import campaign_history_bp




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
    app.register_blueprint(campaign_history_bp)
    

    # Create database tables automatically
    with app.app_context():
        db.create_all()

    return app