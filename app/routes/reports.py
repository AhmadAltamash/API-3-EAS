from flask import Blueprint
from flask import render_template

from app.services.dashboard.dashboard_service import DashboardService

reports_bp = Blueprint(
    "reports",
    __name__
)


@reports_bp.route("/reports")
def reports():

    data = DashboardService().get_dashboard_data()

    return render_template(
        "reports.html",

        total_buyers=data.get("total_buyers", 0),
        email_buyers=data.get("email_buyers", 0),
        classified_buyers=data.get("classified_buyers", 0),
        total_campaigns=data.get("total_campaigns", 0),

        total_sent=data.get("total_sent", 0),
        total_failed=data.get("total_failed", 0),
        success_rate=data.get("success_rate", 0),

        recent_campaigns=data.get("recent_campaigns", [])
    )