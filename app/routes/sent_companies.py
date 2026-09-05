from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from app.services.gmail.email_repository import EmailRepository
from app.services.database.buyer_repository import BuyerRepository

sent_companies_bp = Blueprint(
    "sent_companies",
    __name__
)


@sent_companies_bp.route("/sent-companies")
def sent_companies():

    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    email_query = request.args.get("q", "").strip()

    pagination = EmailRepository().sent_paginated(
        page=page,
        per_page=15,
        email_query=email_query or None
    )

    return render_template(
        "sent_companies.html",
        pagination=pagination,
        logs=pagination.items,
        email_query=email_query
    )


@sent_companies_bp.route(
    "/sent-companies/follow-up/<int:buyer_id>",
    methods=["POST"]
)
def toggle_follow_up(buyer_id):
    """
    "Did this company respond?" toggle next to each row. Yes marks the
    buyer for the Follow-Up Emails page and advances their CRM stage
    to Replied; No just clears the flag.
    """

    value = request.form.get("value") == "yes"

    BuyerRepository().set_follow_up(buyer_id, value)

    page = request.form.get("page", 1, type=int) or 1

    email_query = request.form.get("q", "")

    return redirect(
        url_for(
            "sent_companies.sent_companies",
            page=page,
            q=email_query or None
        )
    )
