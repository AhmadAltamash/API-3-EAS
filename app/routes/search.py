from flask import Blueprint
from flask import render_template
from flask import request

from app.services.buyer.buyer_service import BuyerService
from app.services.search.query_template_service import QueryTemplateService

search_bp = Blueprint(
    "search",
    __name__
)


@search_bp.route("/search", methods=["GET", "POST"])
def search():

    buyers = []
    search_summary = None

    if request.method == "POST":

        keyword = request.form.get(
            "keyword",
            ""
        ).strip()

        source = request.form.get(
            "source"
        )

        buyer_service = BuyerService()

        result = buyer_service.search_buyers(
            keyword,
            source
        )

        buyers = result["buyers"]

        search_summary = {
            "new": result["new_count"],
            "duplicate": result["duplicate_count"]
        }

    smart_queries = QueryTemplateService().build_queries()

    return render_template(
        "search.html",
        buyers=buyers,
        search_summary=search_summary,
        smart_queries=smart_queries
    )