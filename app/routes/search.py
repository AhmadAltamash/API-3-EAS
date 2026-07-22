from flask import Blueprint
from flask import render_template
from flask import request

from app.services.buyer.buyer_service import BuyerService

search_bp = Blueprint(
    "search",
    __name__
)


@search_bp.route("/search", methods=["GET", "POST"])
def search():

    buyers = []

    if request.method == "POST":

        keyword = request.form.get(
            "keyword",
            ""
        ).strip()

        source = request.form.get(
            "source"
        )

        buyer_service = BuyerService()

        buyers = buyer_service.search_buyers(
            keyword,
            source
        )

    return render_template(
        "search.html",
        buyers=buyers
    )