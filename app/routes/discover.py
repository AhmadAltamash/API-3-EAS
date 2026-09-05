from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request

from app.services.ai.ai_discovery_service import AIDiscoveryService


discover_bp = Blueprint(
    "discover",
    __name__
)


@discover_bp.route("/discover", methods=["GET", "POST"])
def discover():

    result = None

    if request.method == "POST":

        buyer_type_hint = request.form.get("buyer_type_hint", "").strip()

        batch_size = request.form.get("batch_size", 12, type=int)

        # Bounded, same philosophy as "Analyze Next 5 Leads" - a single
        # click shouldn't be able to trigger an unbounded number of
        # AI calls + website fetches in one request.
        batch_size = max(5, min(batch_size or 12, 20))

        try:

            result = AIDiscoveryService().discover(
                buyer_type_hint=buyer_type_hint or None,
                batch_size=batch_size
            )

            flash(
                f"AI Discovery run complete! "
                f"{result['new_count']} new companies saved, "
                f"{result['duplicate_count']} already known, "
                f"{result['skipped_count']} named by the AI but couldn't "
                f"be verified with a live email (nothing guessed or saved "
                f"for those).",
                "success"
            )

        except ValueError as e:

            flash(str(e), "danger")

    return render_template(
        "discover.html",
        result=result
    )
