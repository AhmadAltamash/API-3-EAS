from app.extensions import db
from app.models import Buyer, Campaign, EmailLog


class DashboardService:

    def get_dashboard_data(self):

        total_buyers = Buyer.query.count()

        email_buyers = Buyer.query.filter(
            Buyer.email.isnot(None),
            Buyer.email != ""
        ).count()

        classified_buyers = Buyer.query.filter(
            Buyer.category.isnot(None),
            Buyer.category != "",
            Buyer.category != "Unknown"
        ).count()

        total_campaigns = Campaign.query.count()

        total_sent = EmailLog.query.filter_by(
            status="Sent"
        ).count()

        total_failed = EmailLog.query.filter_by(
            status="Failed"
        ).count()

        total_emails = total_sent + total_failed

        if total_emails == 0:
            success_rate = 0
        else:
            success_rate = round(
                (total_sent / total_emails) * 100,
                1
            )

        recent_campaigns = (
            Campaign.query
            .order_by(Campaign.id.desc())
            .limit(5)
            .all()
        )

        recent_buyers = (
            Buyer.query
            .order_by(Buyer.id.desc())
            .limit(5)
            .all()
        )

        return {

            "total_buyers": total_buyers,

            "email_buyers": email_buyers,

            "classified_buyers": classified_buyers,

            "total_campaigns": total_campaigns,

            "total_sent": total_sent,

            "total_failed": total_failed,

            "success_rate": success_rate,

            "recent_campaigns": recent_campaigns,

            "recent_buyers": recent_buyers

        }