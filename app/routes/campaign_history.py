from flask import Blueprint, render_template

from app.services.database.campaign_repository import CampaignRepository

campaign_history_bp = Blueprint(
    "campaign_history",
    __name__
)


@campaign_history_bp.route("/campaign/history")
def history():

    campaigns = CampaignRepository().all()

    return render_template(

        "campaign_history.html",

        campaigns=campaigns

    )