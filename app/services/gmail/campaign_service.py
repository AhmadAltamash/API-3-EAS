import time
from datetime import datetime

from app.services.gmail.gmail_service import GmailService
from app.services.gmail.email_repository import EmailRepository
from app.services.database.buyer_repository import BuyerRepository
from app.services.database.campaign_repository import CampaignRepository


class CampaignService:

    # Gmail personal accounts get flagged/limited fast, so cap how many
    # companies a single campaign run will email. Adjust if needed.
    MAX_RECIPIENTS_PER_CAMPAIGN = 6

    # Small gap between sends to reduce the risk of Gmail's spam-rate
    # throttling kicking in mid-campaign.
    SEND_DELAY_SECONDS = 2

    def __init__(self):

        self.gmail = GmailService()

        self.logs = EmailRepository()

        self.buyers = BuyerRepository()

        self.campaigns = CampaignRepository()

    def _send_with_retry(
        self,
        server,
        receiver,
        subject,
        body,
        attachment_paths
    ):
        """
        Sends one email. If the SMTP connection has dropped (a common
        cause of "works for the first company, then errors on the rest"),
        reconnect once and retry the same recipient before giving up.

        Returns (success, server) - server may be a freshly reconnected
        session, which the caller must keep using for later recipients.
        """

        try:

            self.gmail.send(
                server=server,
                receiver=receiver,
                subject=subject,
                body=body,
                attachment_paths=attachment_paths
            )

            return True, server

        except Exception as e:

            print(f"✗ Send failed for {receiver}, reconnecting and retrying once: {e}")

            try:
                self.gmail.disconnect(server)
            except Exception:
                pass

            try:
                server = self.gmail.connect()
            except Exception as reconnect_error:
                print(f"✗ Reconnect failed: {reconnect_error}")
                return False, server

            try:

                self.gmail.send(
                    server=server,
                    receiver=receiver,
                    subject=subject,
                    body=body,
                    attachment_paths=attachment_paths
                )

                return True, server

            except Exception as retry_error:

                print(f"✗ Retry failed for {receiver}: {retry_error}")

                return False, server

    def send_campaign(
        self,
        campaign_name,
        categories,
        send_all,
        subject,
        body,
        attachment_paths=None
    ):

        buyers = self.buyers.all()

        sent = 0
        failed = 0
        recipients = 0
        report = []

        run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        server = self.gmail.connect()

        try:

            for buyer in buyers:

                if recipients >= self.MAX_RECIPIENTS_PER_CAMPAIGN:
                    break

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

                success, server = self._send_with_retry(
                    server=server,
                    receiver=buyer.email,
                    subject=subject,
                    body=personalized_body,
                    attachment_paths=attachment_paths
                )

                self.logs.save(
                    buyer,
                    subject,
                    personalized_body,
                    "Sent" if success else "Failed"
                )

                report.append({
                    "date": run_date,
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

                    # Remove the buyer once emailed so this (or a future)
                    # campaign never sends to them again.
                    self.buyers.delete(buyer.id)

                else:
                    failed += 1

                # Brief pause between sends, even after a failure, to stay
                # under Gmail's rate limits.
                time.sleep(self.SEND_DELAY_SECONDS)

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
    