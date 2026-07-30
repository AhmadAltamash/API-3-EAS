from app.extensions import db
from app.models import Campaign


class CampaignRepository:

    def save(
        self,
        campaign_name,
        subject,
        body,
        recipients,
        sent,
        failed
    ):

        campaign = Campaign(

            campaign_name=campaign_name,

            subject=subject,

            body=body,

            recipients=recipients,

            sent=sent,

            failed=failed

        )

        db.session.add(campaign)

        db.session.commit()

        return campaign

    def all(self):

        return Campaign.query.order_by(
            Campaign.created_at.desc()
        ).all()