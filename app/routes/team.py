from datetime import datetime, date

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from app.services.database.intern_repository import InternRepository


team_bp = Blueprint(
    "team",
    __name__
)


@team_bp.route("/team", methods=["GET"])
def team():

    repo = InternRepository()

    return render_template(
        "team.html",
        interns=repo.all()
    )


@team_bp.route("/team/add", methods=["POST"])
def add_intern():

    name = request.form.get("name", "").strip()

    date_joined_raw = request.form.get("date_joined", "").strip()

    if not name:
        flash("Please enter a name.", "warning")
        return redirect(url_for("team.team"))

    if date_joined_raw:

        try:
            date_joined = datetime.strptime(date_joined_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "warning")
            return redirect(url_for("team.team"))

    else:
        date_joined = date.today()

    InternRepository().create(name, date_joined)

    flash(f"Added {name} to the team.", "success")

    return redirect(url_for("team.team"))


@team_bp.route("/team/<int:intern_id>/edit", methods=["GET", "POST"])
def edit_intern(intern_id):

    repo = InternRepository()

    intern = repo.get(intern_id)

    if not intern:
        flash("That team member no longer exists.", "warning")
        return redirect(url_for("team.team"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        date_joined_raw = request.form.get("date_joined", "").strip()

        def to_int_or_none(field_name):

            raw = request.form.get(field_name, "").strip()

            if raw == "":
                return None

            try:
                return int(raw)
            except ValueError:
                return None

        date_joined = None

        if date_joined_raw:

            try:
                date_joined = datetime.strptime(date_joined_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format.", "warning")
                return redirect(url_for("team.edit_intern", intern_id=intern_id))

        repo.update_details(
            intern_id,
            name=name or None,
            date_joined=date_joined,
            emails_sent=to_int_or_none("emails_sent"),
            automated_responses=to_int_or_none("automated_responses"),
            positive_responses=to_int_or_none("positive_responses")
        )

        flash(f"Updated {name or intern.name}.", "success")

        return redirect(url_for("team.team"))

    return render_template(
        "edit_intern.html",
        intern=intern
    )


@team_bp.route("/team/<int:intern_id>/update-stats", methods=["POST"])
def update_stats(intern_id):

    def to_int(field_name):

        raw = request.form.get(field_name, "").strip()

        if not raw:
            return 0

        try:
            return int(raw)
        except ValueError:
            return 0

    emails = to_int("emails")

    automated = to_int("automated")

    positive = to_int("positive")

    intern = InternRepository().append_stats(
        intern_id,
        emails=emails,
        automated=automated,
        positive=positive
    )

    if intern:

        flash(
            f"Added {emails} email(s), {automated} automated, "
            f"{positive} positive to {intern.name}'s totals.",
            "success"
        )

    return redirect(url_for("team.team"))


@team_bp.route("/team/<int:intern_id>/discontinue", methods=["POST"])
def discontinue_intern(intern_id):

    date_raw = request.form.get("date_discontinued", "").strip()

    if date_raw:

        try:
            date_discontinued = datetime.strptime(date_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "warning")
            return redirect(url_for("team.team"))

    else:
        date_discontinued = date.today()

    intern = InternRepository().discontinue(intern_id, date_discontinued)

    if intern:
        flash(
            f"Marked {intern.name} as discontinued as of "
            f"{date_discontinued.strftime('%d/%m/%Y')}. Their working "
            f"days are now frozen as of that date.",
            "success"
        )

    return redirect(url_for("team.team"))


@team_bp.route("/team/<int:intern_id>/reactivate", methods=["POST"])
def reactivate_intern(intern_id):

    intern = InternRepository().reactivate(intern_id)

    if intern:
        flash(f"{intern.name} is active again.", "success")

    return redirect(url_for("team.team"))


@team_bp.route("/team/<int:intern_id>/delete", methods=["POST"])
def delete_intern(intern_id):

    repo = InternRepository()

    intern = repo.get(intern_id)

    name = intern.name if intern else "Intern"

    repo.delete(intern_id)

    flash(f"Removed {name} from the team.", "success")

    return redirect(url_for("team.team"))
