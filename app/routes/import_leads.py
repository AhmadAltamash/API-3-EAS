from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request

from app.services.imports.lead_csv_importer import LeadCSVImporter


import_leads_bp = Blueprint(
    "import_leads",
    __name__
)


@import_leads_bp.route("/import-leads", methods=["GET", "POST"])
def import_leads():

    result = None

    if request.method == "POST":

        file = request.files.get("csv_file")

        if not file or not file.filename:

            flash("Please choose a CSV/TSV file to upload.", "warning")

            return render_template("import_leads.html", result=None)

        try:
            content = file.read().decode("utf-8-sig", errors="ignore")
        except Exception:

            flash(
                "Couldn't read that file - make sure it's a plain "
                "CSV/TSV text file exported from Excel/Sheets/Notepad.",
                "danger"
            )

            return render_template("import_leads.html", result=None)

        importer = LeadCSVImporter()

        parsed_rows = importer.parse(content)

        if not parsed_rows:

            flash(
                "No rows found in that file, or the company/email "
                "columns couldn't be recognized.",
                "warning"
            )

            return render_template("import_leads.html", result=None)

        result = importer.import_rows(parsed_rows)

        flash(
            f"Import complete! {result['new_count']} new companies saved, "
            f"{result['duplicate_count']} already known, "
            f"{result['invalid_count']} row(s) skipped (missing/invalid "
            f"company or email).",
            "success"
        )

    return render_template(
        "import_leads.html",
        result=result
    )
