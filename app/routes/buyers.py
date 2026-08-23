from pathlib import Path

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import url_for

from app.services.buyer.buyer_service import BuyerService
from app.services.crm.stage_service import StageService
from app.services.database.buyer_repository import BuyerRepository


buyers_bp = Blueprint(
    "buyers",
    __name__
)


@buyers_bp.route("/buyers")
def buyers():

    from app.services.database.buyer_repository import BuyerRepository

    return render_template(
        "buyers.html",
        buyers=BuyerRepository().contactable_buyers()
    )


@buyers_bp.route("/buyers/<int:buyer_id>")
def buyer_detail(buyer_id):

    buyer = BuyerService().get_buyer(buyer_id)

    if buyer is None:

        flash("Buyer not found.", "warning")

        return redirect(url_for("buyers.buyers"))

    stages = StageService()

    return render_template(
        "buyer_detail.html",
        buyer=buyer,
        timeline=stages.get_timeline(buyer_id),
        stage_order=stages.STAGE_ORDER
    )


@buyers_bp.route(
    "/buyers/<int:buyer_id>/stage",
    methods=["POST"]
)
def update_stage(buyer_id):

    new_stage = request.form.get("stage")

    note = request.form.get("note", "").strip() or None

    stages = StageService()

    if new_stage not in stages.STAGE_ORDER:

        flash("Invalid pipeline stage.", "danger")

    else:

        stages.set_stage_manual(buyer_id, new_stage, note=note)

        flash(f"Stage updated to {new_stage}.", "success")

    return redirect(
        url_for("buyers.buyer_detail", buyer_id=buyer_id)
    )


@buyers_bp.route(
    "/buyers/add",
    methods=["GET", "POST"]
)
def add_inbound_lead():

    if request.method == "POST":

        company = request.form.get("company", "").strip()

        if not company:

            flash("Company name is required.", "warning")

            return redirect(url_for("buyers.add_inbound_lead"))

        buyer = BuyerRepository().add_inbound_lead(
            company=company,
            email=request.form.get("email", "").strip() or None,
            website=request.form.get("website", "").strip() or None,
            country=request.form.get("country", "").strip() or None,
            state=request.form.get("state", "").strip() or None,
            buyer_name=request.form.get("buyer_name", "").strip() or None,
            note=request.form.get("note", "").strip() or None
        )

        flash(f"Added inbound lead: {buyer.company}", "success")

        return redirect(
            url_for("buyers.buyer_detail", buyer_id=buyer.id)
        )

    return render_template("add_inbound_lead.html")


@buyers_bp.route(
    "/buyers/<int:buyer_id>/analyze",
    methods=["POST"]
)
def analyze_buyer(buyer_id):

    data = BuyerService().analyze_buyer(buyer_id)

    if data is None:

        flash("Buyer not found.", "warning")

        return redirect(url_for("buyers.buyers"))

    flash(
        f"Analysis complete - lead score {data['lead_score']} "
        f"({data['outreach_priority']}).",
        "success"
    )

    return redirect(
        url_for("buyers.buyer_detail", buyer_id=buyer_id)
    )


@buyers_bp.route(
    "/buyers/analyze-unscored",
    methods=["POST"]
)
def analyze_unscored():

    count = BuyerService().analyze_unscored(limit=5)

    flash(
        f"Analyzed {count} buyer(s). Click again to analyze the next batch.",
        "success"
    )

    return redirect(
        url_for("buyers.buyers")
    )


@buyers_bp.route("/buyers/download")
def download_buyers():

    return send_file(

        Path("app")
        / "exports"
        / "buyers.csv",

        as_attachment=True
    )


@buyers_bp.route(
    "/buyers/delete-all",
    methods=["POST"]
)
def delete_all():

    BuyerService().delete_all_buyers()

    return redirect(
        url_for("buyers.buyers")
    )


@buyers_bp.route(
    "/buyers/delete/<int:buyer_id>",
    methods=["POST"]
)
def delete_one(buyer_id):

    BuyerService().delete_buyer(
        buyer_id
    )

    return redirect(
        url_for("buyers.buyers")
    )