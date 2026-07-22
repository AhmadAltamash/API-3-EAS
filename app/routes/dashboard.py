from flask import Blueprint, render_template

from app.services.dashboard.dashboard_service import DashboardService


dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def dashboard():

    data = DashboardService().get_dashboard_data()

    return render_template(
        "dashboard.html",

        total_buyers=data.get("total_buyers", 0),
        email_buyers=data.get("email_buyers", 0),
        classified_buyers=data.get("classified_buyers", 0),
        total_campaigns=data.get("total_campaigns", 0),

        total_sent=data.get("total_sent", 0),
        total_failed=data.get("total_failed", 0),
        success_rate=data.get("success_rate", 0),

        recent_campaigns=data.get("recent_campaigns", []),
        recent_buyers=data.get("recent_buyers", []),
    )