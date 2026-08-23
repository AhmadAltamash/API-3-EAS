from flask import Blueprint
from flask import render_template
from flask import request

from app.services.gmail.email_repository import EmailRepository

sent_companies_bp = Blueprint(
    "sent_companies",
    __name__
)


@sent_companies_bp.route("/sent-companies")
def sent_companies():

    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    pagination = EmailRepository().sent_paginated(
        page=page,
        per_page=15
    )

    return render_template(
        "sent_companies.html",
        pagination=pagination,
        logs=pagination.items
    )
