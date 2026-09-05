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
    last_query = None

    if request.method == "POST":

        # Smart Query rows submit a single ready-made "keyword" field
        # directly (see search.html) - the structured product/city/
        # state/country fields below are only for the main search box.
        # A regression check just caught that these two submission
        # shapes weren't being reconciled: every Smart Query "Run"
        # click was silently searching for an empty string after the
        # structured-field rework, since the route stopped reading a
        # raw "keyword" field at all. Checking for it first fixes that.
        raw_keyword = request.form.get("keyword", "").strip()

        if raw_keyword:

            keyword = raw_keyword

            last_query = None

        else:

            product = request.form.get("product", "").strip()

            city = request.form.get("city", "").strip()

            state = request.form.get("state", "").strip()

            country = request.form.get("country", "").strip()

            # Combine the structured fields into the single keyword
            # string the search adapters already expect - this is
            # purely a nicer input UI, the underlying search backend
            # is unchanged.
            keyword = " ".join(
                part for part in (product, city, state, country) if part
            ).strip()

            last_query = {
                "product": product,
                "city": city,
                "state": state,
                "country": country
            }

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
            "duplicate": result["duplicate_count"],
            "source": source or "all"
        }

    smart_queries = QueryTemplateService().build_queries()

    return render_template(
        "search.html",
        buyers=buyers,
        search_summary=search_summary,
        smart_queries=smart_queries,
        last_query=last_query
    )