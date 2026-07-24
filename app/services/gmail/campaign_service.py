from app.services.gmail.gmail_service import GmailService
from app.services.gmail.email_repository import EmailRepository
from app.services.database.buyer_repository import BuyerRepository
from app.services.database.campaign_repository import CampaignRepository


class CampaignService:

    def __init__(self):

        self.gmail = GmailService()

        self.logs = EmailRepository()

        self.buyers = BuyerRepository()

        self.campaigns = CampaignRepository()

    def send_campaign(
        self,
        campaign_name,
        categories,
        send_all,
        subject,
        body,
        attachment_path=None
    ):

        buyers = self.buyers.all()

        sent = 0
        failed = 0
        recipients = 0
        report = []

        server = self.gmail.connect()

        try:

            for buyer in buyers:

                if not send_all and buyer.category not in categories:
                    continue

                if not buyer.email:
                    continue

                recipients += 1

                personalized_body = (
                    body
                    .replace("{{company}}", buyer.company or "")
                    .replace("{{buyer_name}}", buyer.buyer_name or "")
                )

                success = self.gmail.send(
                    server=server,
                    receiver=buyer.email,
                    subject=subject,
                    body=personalized_body,
                    attachment_path=attachment_path
                )

                self.logs.save(
                    buyer,
                    subject,
                    personalized_body,
                    "Sent" if success else "Failed"
                )

                report.append({
                    "company": buyer.company,
                    "email": buyer.email,
                    "country": buyer.country,
                    "category": buyer.category,
                    "website": buyer.website,
                    "source": buyer.source,
                    "status": "Sent" if success else "Failed"
                })

                if success:
                    sent += 1
                else:
                    failed += 1

        finally:
            self.gmail.disconnect(server)

        self.campaigns.save(
            campaign_name=campaign_name,
            subject=subject,
            body=body,
            recipients=recipients,
            sent=sent,
            failed=failed
        )

        return {
            "campaign_name": campaign_name,
            "sent": sent,
            "failed": failed,
            "total": recipients,
            "report": report
        }
    