import re
from datetime import datetime
from pathlib import Path

from flask import Blueprint
from flask import current_app
from flask import flash
from flask import render_template
from flask import request
from flask import send_file

from app.services.gmail.campaign_service import CampaignService
from app.services.export.export_service import ExportService
from app.services.database.buyer_repository import BuyerRepository


follow_up_bp = Blueprint(
    "follow_up",
    __name__
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _parse_extra_emails(raw):

    candidates = [
        e.strip()
        for e in re.split(r"[,\n]+", raw or "")
        if e.strip()
    ]

    valid = [e for e in candidates if EMAIL_PATTERN.match(e)]

    invalid = [e for e in candidates if not EMAIL_PATTERN.match(e)]

    return valid, invalid


@follow_up_bp.route("/follow-up", methods=["GET", "POST"])
def follow_up():

    result = None

    if request.method == "POST":

        subject = request.form.get("subject")

        body = request.form.get("body")

        extra_emails_raw = request.form.get("extra_emails", "")

        extra_emails, invalid_emails = _parse_extra_emails(extra_emails_raw)

        if invalid_emails:

            flash(
                "Skipped invalid email address(es): "
                + ", ".join(invalid_emails),
                "warning"
            )

        attachments = request.files.getlist("attachments")

        attachment_paths = []

        if attachments:

            upload_folder = Path(current_app.root_path) / "uploads"

            upload_folder.mkdir(exist_ok=True)

            for attachment in attachments:

                if not attachment or not attachment.filename:
                    continue

                attachment_path = upload_folder / attachment.filename

                attachment.save(attachment_path)

                attachment_paths.append(str(attachment_path))

        result = CampaignService().send_follow_up(
            subject=subject,
            body=body,
            attachment_paths=attachment_paths,
            extra_emails=extra_emails
        )

        flash(
            f"Follow-up run completed! "
            f"Sent: {result['sent']} | "
            f"Failed: {result['failed']} | "
            f"Total: {result['total']}",
            "success"
        )

        # Auto-export: every follow-up send downloads a dated CSV of who
        # it went to, same convention as the main campaign CSV report.
        csv_file = ExportService().campaign_csv(
            result["report"]
        )

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return send_file(
            csv_file,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"follow_up_report_{timestamp}.csv"
        )

    pending_buyers = BuyerRepository().follow_up_buyers()

    return render_template(
        "follow_up.html",
        result=result,
        pending_buyers=pending_buyers
    )
