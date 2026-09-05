import csv
import io
import re

from types import SimpleNamespace

from app.services.database.buyer_repository import BuyerRepository


class LeadCSVImporter:
    """
    Accepts a CSV/TSV of leads from ANY source - a colleague's
    spreadsheet, a manual ChatGPT/Gemini/Grok chat session copy-pasted
    into a sheet, a paid third-party scraper's export - and turns it
    into real Buyer records.

    Deliberately tolerant of messy input:
    - Works with comma, tab, or semicolon-separated files.
    - Recognizes a real header row if it finds one (company/email/
      website/country/phone under any common name).
    - Falls back to content-based column detection for headerless
      data (exactly the shape of the raw pastes you and your
      colleague have both shared in this chat: date, company, email,
      url, no header row) - it looks at what's actually IN each
      column rather than assuming a fixed order.

    Every row still goes through the same email-format check and the
    same dedup-aware BuyerRepository.save() as every other lead source
    in this app, so an import can't create duplicate rows or bypass
    validation.
    """

    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    DATE_PATTERN = re.compile(
        r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$"
    )

    HEADER_SYNONYMS = {
        "company": {
            "company", "company_name", "companyname", "name",
            "business", "business_name", "buyer", "buyer_name"
        },
        "email": {
            "email", "email_address", "e-mail", "contact_email",
            "emailid", "email_id"
        },
        "website": {
            "website", "url", "site", "web", "domain", "link"
        },
        "country": {
            "country", "country_name", "location"
        },
        "phone": {
            "phone", "phone_number", "contact_number", "mobile",
            "telephone"
        }
    }

    def parse(self, file_text):
        """
        Returns a list of dicts: {"company", "email", "website",
        "country", "phone"} (blank string for anything not found).
        Empty list if the file has no usable rows.
        """

        dialect = self._sniff_dialect(file_text)

        reader = csv.reader(io.StringIO(file_text), dialect)

        rows = [
            row for row in reader
            if any(cell.strip() for cell in row)
        ]

        if not rows:
            return []

        header_map = self._match_header(rows[0])

        if header_map:
            data_rows = rows[1:]
            col_map = header_map
        else:
            data_rows = rows
            col_map = self._infer_columns(rows[:15])

        parsed = []

        for row in data_rows:

            def cell(col_idx):

                if col_idx is None or col_idx >= len(row):
                    return ""

                return row[col_idx].strip()

            parsed.append({
                "company": cell(col_map.get("company")),
                "email": cell(col_map.get("email")),
                "website": cell(col_map.get("website")),
                "country": cell(col_map.get("country")),
                "phone": cell(col_map.get("phone"))
            })

        return parsed

    def import_rows(self, parsed_rows):
        """
        Returns {"new_count", "duplicate_count", "invalid_count",
        "details": [{"company","email","website","status"}, ...]}.
        status is "saved" / "duplicate" / "invalid".
        """

        buyers = BuyerRepository()

        new_count = 0
        duplicate_count = 0
        invalid_count = 0

        details = []

        for row in parsed_rows:

            company = row.get("company", "").strip()

            email = row.get("email", "").strip().lower()

            website = row.get("website", "").strip()

            if not company or not email or not self.EMAIL_PATTERN.match(email):

                details.append({
                    "company": company or "(missing)",
                    "email": email or "(missing)",
                    "website": website or None,
                    "status": "invalid"
                })

                invalid_count += 1

                continue

            buyer_stub = SimpleNamespace(
                company=company,
                buyer_name=None,
                email=email,
                # Explicitly None (not "") for a blank website - the
                # website column has a database-level UNIQUE
                # constraint, and two blank STRINGS would collide on
                # the second row without a URL where two NULLs would not.
                website=website or None,
                snippet=None,
                country=row.get("country", "").strip() or None,
                source="CSV Import",
                category="Imported",
                phone=row.get("phone", "").strip() or None,
                email_live_verified=False
            )

            saved, is_new = buyers.save(buyer_stub)

            details.append({
                "company": saved.company,
                "email": saved.email,
                "website": saved.website,
                "status": "saved" if is_new else "duplicate"
            })

            if is_new:
                new_count += 1
            else:
                duplicate_count += 1

        return {
            "new_count": new_count,
            "duplicate_count": duplicate_count,
            "invalid_count": invalid_count,
            "details": details
        }

    # -------------------------------------------------------------
    # Column detection
    # -------------------------------------------------------------

    def _sniff_dialect(self, file_text):

        sample = file_text[:4096]

        try:
            return csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:

            dialect = csv.excel

            # Simple fallback: whichever of , / tab / ; appears more
            # often in the sample is probably the real delimiter.
            counts = {
                d: sample.count(d) for d in (",", "\t", ";")
            }

            best = max(counts, key=counts.get)

            dialect.delimiter = best if counts[best] else ","

            return dialect

    def _match_header(self, header_row):

        normalized = [
            h.strip().lower().replace(" ", "_")
            for h in header_row
        ]

        col_map = {}

        for idx, cell in enumerate(normalized):

            for field, synonyms in self.HEADER_SYNONYMS.items():

                if cell in synonyms and field not in col_map:
                    col_map[field] = idx

        # Require at least company + email to trust this as a real
        # header row, rather than a coincidental text match on a
        # headerless first data row.
        if "company" in col_map and "email" in col_map:
            return col_map

        return None

    def _infer_columns(self, sample_rows):
        """
        Headerless data: figure out each column's role from what's
        actually in it rather than assuming a fixed position, since
        different sources order their columns differently.
        """

        if not sample_rows:
            return {}

        num_cols = max(len(r) for r in sample_rows)

        stats = []

        for c in range(num_cols):

            values = [
                r[c].strip()
                for r in sample_rows
                if c < len(r) and r[c].strip()
            ]

            if not values:
                stats.append({"email": 0, "website": 0, "date": 0})
                continue

            stats.append({
                "email": sum(
                    1 for v in values if self.EMAIL_PATTERN.match(v)
                ) / len(values),
                "website": sum(
                    1 for v in values if v.lower().startswith("http")
                ) / len(values),
                "date": sum(
                    1 for v in values if self.DATE_PATTERN.match(v)
                ) / len(values)
            })

        col_map = {}

        email_col = max(range(num_cols), key=lambda c: stats[c]["email"])

        if stats[email_col]["email"] > 0.5:
            col_map["email"] = email_col

        website_col = max(range(num_cols), key=lambda c: stats[c]["website"])

        if stats[website_col]["website"] > 0.5:
            col_map["website"] = website_col

        date_cols = {
            c for c in range(num_cols) if stats[c]["date"] > 0.5
        }

        remaining = [
            c for c in range(num_cols)
            if c not in date_cols
            and c != col_map.get("email")
            and c != col_map.get("website")
        ]

        if remaining:
            col_map["company"] = remaining[0]

        return col_map
