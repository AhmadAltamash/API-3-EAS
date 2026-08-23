from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request

from app.services.ai.catalogue_analyzer import CatalogueAnalyzer
from app.services.database.catalogue_profile_repository import CatalogueProfileRepository

catalogue_bp = Blueprint(
    "catalogue",
    __name__
)


def _profile_to_analysis_dict(profile):

    if not profile:
        return None

    def split(value):
        return [v.strip() for v in (value or "").split(",") if v.strip()]

    return {
        "products": split(profile.products),
        "categories": split(profile.categories),
        "materials": split(profile.materials),
        "industries": split(profile.industries),
        "buyer_types": split(profile.buyer_types),
    }


@catalogue_bp.route("/catalogue", methods=["GET", "POST"])
def catalogue():

    analysis = None

    if request.method == "POST":

        file = request.files.get("catalogue_file")

        if not file or not file.filename:

            flash("Please choose a catalogue file to upload.", "warning")

            return render_template("catalogue.html", analysis=None)

        analyzer = CatalogueAnalyzer()

        try:

            text = analyzer.extract_text(file)

            analysis = analyzer.analyze(text)

            # Persist so buyer lead-scoring (Buyer Database -> Analyze)
            # has something to compare prospects against.
            CatalogueProfileRepository().save(analysis)

        except ValueError as e:

            flash(str(e), "danger")

            return render_template("catalogue.html", analysis=None)

        except Exception as e:

            flash(f"Catalogue analysis failed: {e}", "danger")

            return render_template("catalogue.html", analysis=None)

    else:

        # Show the currently-active saved catalogue (if any) on a plain
        # page visit, so it's clear what buyer analysis is being scored
        # against without needing to re-upload the file.
        analysis = _profile_to_analysis_dict(
            CatalogueProfileRepository().get()
        )

    return render_template(
        "catalogue.html",
        analysis=analysis
    )
