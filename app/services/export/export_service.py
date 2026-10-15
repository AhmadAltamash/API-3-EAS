import csv
from io import BytesIO, TextIOWrapper
from pathlib import Path


class ExportService:

    def campaign_csv(self, buyers):

        output = BytesIO()

        text_output = TextIOWrapper(
            output,
            encoding="utf-8",
            newline=""
        )

        writer = csv.writer(text_output)

        writer.writerow([
            "Date",
            "Company",
            "Email",
            "Website"
        ])

        for buyer in buyers:

            writer.writerow([
                buyer.get("date", ""),
                buyer.get("company", ""),
                buyer.get("email", ""),
                buyer.get("website", "")
            ])

        text_output.flush()

        # Prevent TextIOWrapper from closing the BytesIO
        text_output.detach()

        output.seek(0)

        return output

    def intern_csv(self, interns):
        """
        Name/Status/Emails/Automated/Positive/Joined/Working Days for
        a downloadable snapshot of the team - the caller decides which
        interns to include (e.g. InternRepository.active_only() to
        exclude discontinued members).
        """

        output = BytesIO()

        text_output = TextIOWrapper(
            output,
            encoding="utf-8",
            newline=""
        )

        writer = csv.writer(text_output)

        writer.writerow([
            "Name",
            "Status",
            "Product Assigned",
            "Emails",
            "Automated",
            "Positive",
            "Joined",
            "Working Days"
        ])

        for intern in interns:

            writer.writerow([
                intern.name,
                intern.status,
                intern.product_assigned or "",
                intern.emails_sent or 0,
                intern.automated_responses or 0,
                intern.positive_responses or 0,
                intern.date_joined.strftime("%d/%m/%Y") if intern.date_joined else "",
                intern.total_working_days
            ])

        text_output.flush()

        text_output.detach()

        output.seek(0)

        return output

    def buyers_csv(self, buyers):

        export_folder = Path("app") / "exports"

        export_folder.mkdir(exist_ok=True)

        csv_path = export_folder / "buyers.csv"

        with open(
            csv_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Company",
                "Email",
                "Country",
                "Website",
                "Category",
                "Source"
            ])

            for buyer in buyers:

                writer.writerow([
                    buyer.company,
                    buyer.email,
                    buyer.country,
                    buyer.website,
                    buyer.category,
                    buyer.source
                ])

        return csv_path