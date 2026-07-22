from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import flash

from app.services.buyer.buyer_service import BuyerService

classify_bp = Blueprint(
    "classify",
    __name__
)


# ==========================================================
# AI Classification Dashboard
# ==========================================================

@classify_bp.route("/classify")
def classify_page():

    buyers = BuyerService().all_buyers()

    return render_template(
        "classify.html",
        buyers=buyers
    )


# ==========================================================
# Classify Single Buyer
# ==========================================================

@classify_bp.route("/classify/<int:buyer_id>")
def classify(buyer_id):

    try:

        BuyerService().classify_buyer(
            buyer_id
        )

        flash(
            "Buyer classified successfully.",
            "success"
        )

    except Exception as e:

        flash(
            str(e),
            "danger"
        )

    return redirect(
        url_for("classify.classify_page")
    )


# ==========================================================
# Classify All Buyers
# ==========================================================

@classify_bp.route("/classify-all")
def classify_all():

    try:

        BuyerService().classify_all()

        flash(
            "All buyers classified successfully.",
            "success"
        )

    except Exception as e:

        flash(
            str(e),
            "danger"
        )

    return redirect(
        url_for("classify.classify_page")
    )