from pathlib import Path

from flask import Blueprint
from flask import current_app
from flask import flash
from flask import render_template
from flask import request
from flask import send_file

from app.services.gmail.campaign_service import CampaignService
from app.services.export.export_service import ExportService


campaign_bp = Blueprint(
    "campaign",
    __name__
)


@campaign_bp.route("/campaign", methods=["GET", "POST"])
def campaign():

    result = None

    if request.method == "POST":

        campaign_name = request.form.get("campaign_name")

        subject = request.form.get("subject")

        body = request.form.get("body")

        categories = request.form.getlist("categories")

        send_all = request.form.get("send_all") == "1"

        attachment = request.files.get("attachment")

        attachment_path = None

        if attachment and attachment.filename:

            upload_folder = Path(current_app.root_path) / "uploads"

            upload_folder.mkdir(exist_ok=True)

            attachment_path = upload_folder / attachment.filename

            attachment.save(attachment_path)

            attachment_path = str(attachment_path)

        result = CampaignService().send_campaign(

            campaign_name=campaign_name,

            categories=categories,

            send_all=send_all,

            subject=subject,

            body=body,

            attachment_path=attachment_path

        )

        flash(

            f"Campaign completed successfully! "
            f"Sent: {result['sent']} | "
            f"Failed: {result['failed']} | "
            f"Total: {result['total']}",

            "success"

        )

        csv_file = ExportService().campaign_csv(

            result["report"]

        )

        return send_file(

            csv_file,

            mimetype="text/csv",

            as_attachment=True,

            download_name=f"{campaign_name}_report.csv"

        )

    return render_template(

        "campaign.html",

        result=result

    )