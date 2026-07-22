import csv
from io import BytesIO, TextIOWrapper


class ExportService:

    def campaign_csv(self, buyers):

        output = BytesIO()
        text_output = TextIOWrapper(output, encoding="utf-8", newline="")

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
        output.seek(0)

        return output