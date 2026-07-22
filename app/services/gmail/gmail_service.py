import os
import smtplib

from email import encoders

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app


class GmailService:

    def send(
        self,
        receiver,
        subject,
        body,
        attachment_path=None
    ):

        sender = current_app.config["GMAIL_EMAIL"]
        password = current_app.config["GMAIL_APP_PASSWORD"]

        message = MIMEMultipart()

        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = subject

        # Email Body
        message.attach(
            MIMEText(body, "plain")
        )

        # ===========================
        # Attachment
        # ===========================

        if attachment_path and os.path.exists(attachment_path):

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

        # ===========================
        # Send Email
        # ===========================

        try:

            with smtplib.SMTP(
                "smtp.gmail.com",
                587
            ) as server:

                server.starttls()

                server.login(
                    sender,
                    password
                )

                server.send_message(message)

            print(f"✓ Sent to {receiver}")

            return True

        except Exception as e:

            print(f"✗ Failed to send to {receiver}")

            print(e)

            return False