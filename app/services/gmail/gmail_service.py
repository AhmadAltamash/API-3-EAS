import mimetypes
import os
import smtplib

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app


class GmailService:

    def connect(self):

        sender = current_app.config.get("GMAIL_EMAIL")
        password = current_app.config.get("GMAIL_APP_PASSWORD")

        if not sender or not password:
            raise Exception(
                "GMAIL_EMAIL or GMAIL_APP_PASSWORD is not configured."
            )

        try:

            server = smtplib.SMTP(
                "smtp.gmail.com",
                587,
                timeout=60
            )

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(
                sender,
                password
            )

            print("✓ Connected to Gmail SMTP")

            return server

        except Exception as e:

            print("✗ Gmail connection failed")

            print(e)

            raise

    def disconnect(self, server):

        if server is None:
            return

        try:

            server.quit()

            print("✓ Gmail connection closed")

        except Exception as e:

            print("Error while closing SMTP connection")

            print(e)

    def is_alive(self, server):
        """
        Cheap health check (SMTP NOOP) to catch a connection that's died
        between sends - e.g. Gmail closed it, or a prior timeout left it
        in a broken state - before attempting a real send (which would
        otherwise waste time re-uploading an attachment only to fail).
        """

        if server is None:
            return False

        try:
            status = server.noop()[0]
            return status == 250
        except Exception:
            return False

    def send(
        self,
        server,
        receiver,
        subject,
        body,
        attachment_paths=None,
        cc_emails=None
    ):

        sender = current_app.config.get("GMAIL_EMAIL")

        message = MIMEMultipart()

        message["From"] = sender
        message["To"] = receiver
        if cc_emails:
            message["Cc"] = ", ".join(cc_emails)
        message["Subject"] = subject

        message.attach(
            MIMEText(body, "plain")
        )

        # -------------------------
        # Attachments (multiple, any type)
        # -------------------------

        if attachment_paths:

            for attachment_path in attachment_paths:

                if not attachment_path or not os.path.exists(attachment_path):
                    continue

                try:

                    mime_type, _ = mimetypes.guess_type(attachment_path)

                    if mime_type:
                        maintype, subtype = mime_type.split("/", 1)
                    else:
                        maintype, subtype = "application", "octet-stream"

                    with open(attachment_path, "rb") as file:

                        part = MIMEBase(
                            maintype,
                            subtype
                        )

                        part.set_payload(file.read())

                    encoders.encode_base64(part)

                    filename = os.path.basename(
                        attachment_path
                    )

                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"'
                    )

                    message.attach(part)

                except Exception as e:

                    print(f"Attachment Error ({attachment_path}):")

                    print(e)

        # -------------------------
        # Send Email
        # -------------------------

        # Deliberately NOT caught here: if the SMTP connection has dropped,
        # this raises so the caller (CampaignService) can reconnect and
        # retry, instead of silently marking every remaining buyer as
        # failed for the rest of the run.
        server.send_message(message)

        print(f"✓ Sent to {receiver}")

        return True