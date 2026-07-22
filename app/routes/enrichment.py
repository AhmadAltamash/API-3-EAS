from flask import Blueprint, redirect, url_for, flash

from app.services.extractor.enrichment_service import EnrichmentService

enrichment_bp = Blueprint("enrichment", __name__)


@enrichment_bp.route("/enrich")
def enrich():

    result = EnrichmentService().enrich_all()

    flash(
        f"Enrichment completed! "
        f"{result['enriched']} enriched, "
        f"{result['skipped']} skipped.",
        "success"
    )

    return redirect(url_for("buyers.buyers"))