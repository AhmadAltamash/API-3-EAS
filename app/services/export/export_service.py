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
            "Company",
            "Email",
            "Country",
            "Category",
            "Website",
            "Source",
            "Status"
        ])

        for buyer in buyers:

            writer.writerow([
                buyer.get("company", ""),
                buyer.get("email", ""),
                buyer.get("country", ""),
                buyer.get("category", ""),
                buyer.get("website", ""),
                buyer.get("source", ""),
                buyer.get("status", "Sent")
            ])

        text_output.flush()

        # Prevent TextIOWrapper from closing the BytesIO
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