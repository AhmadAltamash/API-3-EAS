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
                timeout=20
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

    def send(
        self,
        server,
        receiver,
        subject,
        body,
        attachment_path=None
    ):

        sender = current_app.config.get("GMAIL_EMAIL")

        message = MIMEMultipart()

        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = subject

        message.attach(
            MIMEText(body, "plain")
        )

        # -------------------------
        # Attachment
        # -------------------------

        if attachment_path and os.path.exists(attachment_path):

            try:

                with open(attachment_path, "rb") as file:

                    part = MIMEBase(
                        "application",
                        "octet-stream"
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

                print("Attachment Error:")

                print(e)

        # -------------------------
        # Send Email
        # -------------------------

        try:

            server.send_message(message)

            print(f"✓ Sent to {receiver}")

            return True

        except Exception as e:

            print(f"✗ Failed to send to {receiver}")

            print(e)

            return False