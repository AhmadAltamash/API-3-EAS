from pathlib import Path

from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import send_file
from flask import url_for

from app.services.buyer.buyer_service import BuyerService


buyers_bp = Blueprint(
    "buyers",
    __name__
)


@buyers_bp.route("/buyers")
def buyers():

    service = BuyerService()

    return render_template(
        "buyers.html",
        buyers=service.all_buyers()
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