from flask import Blueprint, render_template
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