from flask import Blueprint
from flask import render_template

settings_bp = Blueprint(
    "settings",
    __name__
)


@settings_bp.route("/settings")
def settings():

    return render_template(
        "settings.html"
    )