"""
One-time migration: adds the new columns introduced across recent
updates to an EXISTING sqlite database, without losing any data
already in it.

  - buyers.state                   (US state / Canada province, for timezone lookup)
  - buyers.lead_score               \
  - buyers.outreach_priority        |
  - buyers.lead_score_reasons       |
  - buyers.product_match_percent    |
  - buyers.relevant_categories      |  Phase 3 lead intelligence fields
  - buyers.style_estimate           |
  - buyers.positioning_estimate     |
  - buyers.recommended_products     |
  - buyers.decision_maker_name      |
  - buyers.decision_maker_title     |
  - buyers.email_domain_verified    |
  - buyers.analyzed_at             /
  - email_logs.website             (used by the Sent Companies page)

NOTE: the app also runs this same check automatically on every startup
(see _ensure_new_columns in app/__init__.py), using its own database
connection - so you normally don't need to run this script at all
anymore. It's kept here as a manual fallback/inspection tool.

Usage (from the project root, same folder as config.py):

    python add_new_columns.py
"""

import sqlite3
from pathlib import Path

from config import Config


# (table, column, sqlite type)
NEW_COLUMNS = [
    ("buyers", "state", "VARCHAR(50)"),
    ("buyers", "lead_score", "INTEGER"),
    ("buyers", "outreach_priority", "VARCHAR(20)"),
    ("buyers", "lead_score_reasons", "TEXT"),
    ("buyers", "product_match_percent", "INTEGER"),
    ("buyers", "relevant_categories", "VARCHAR(500)"),
    ("buyers", "style_estimate", "VARCHAR(150)"),
    ("buyers", "positioning_estimate", "VARCHAR(100)"),
    ("buyers", "recommended_products", "TEXT"),
    ("buyers", "decision_maker_name", "VARCHAR(150)"),
    ("buyers", "decision_maker_title", "VARCHAR(150)"),
    ("buyers", "email_domain_verified", "BOOLEAN"),
    ("buyers", "analyzed_at", "DATETIME"),
    ("buyers", "pipeline_stage", "VARCHAR(50)"),
    ("email_logs", "website", "VARCHAR(300)"),
]


def get_relative_db_filename():

    uri = Config.SQLALCHEMY_DATABASE_URI

    if not uri.startswith("sqlite:///"):
        raise RuntimeError(
            "This helper only supports the default local SQLite database. "
            "If you're using another database (Postgres, MySQL, etc.), add "
            "the new columns manually - see NEW_COLUMNS at the top of this "
            "script for the full list."
        )

    return uri.replace("sqlite:///", "", 1)


def find_db_path():
    """
    A relative sqlite:/// URI (the default here) is resolved by
    Flask-SQLAlchemy relative to the app's *instance* folder, not the
    project root or current working directory. For this project's
    layout (a Flask app living in the "app" package), Flask's default
    instance folder is a sibling of that package: <project_root>/instance.

    Checks that location first, then a couple of reasonable fallbacks,
    so this works whether or not you're running it from the project root.
    """

    filename = get_relative_db_filename()

    project_root = Path(__file__).resolve().parent

    candidates = [
        project_root / "instance" / filename,
        project_root / filename,
        Path.cwd() / "instance" / filename,
        Path.cwd() / filename,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate, candidates

    return None, candidates


def column_exists(cursor, table, column):

    cursor.execute(f"PRAGMA table_info({table})")

    return any(row[1] == column for row in cursor.fetchall())


def table_exists(cursor, table):

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )

    return cursor.fetchone() is not None


def main():

    db_path, checked = find_db_path()

    if not db_path:

        print("No existing database file found. Checked:")

        for c in checked:
            print(f"  - {c}")

        print(
            "\nIf you've already run the app at least once (python run.py "
            "or similar), it should have created the database automatically "
            "- including these columns, since the app now self-heals its "
            "own schema on startup. If you're still seeing 'no such "
            "column' errors, double check where your database file "
            "actually is and re-run this script from that folder."
        )

        return

    print(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    changed = False

    for table, column, col_type in NEW_COLUMNS:

        if not table_exists(cursor, table):
            print(f"Table '{table}' doesn't exist yet - skipping "
                  f"{table}.{column} (it'll be created automatically "
                  f"next time the app starts).")
            continue

        if not column_exists(cursor, table, column):
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
            )
            print(f"Added {table}.{column}")
            changed = True
        else:
            print(f"{table}.{column} already exists - skipped")

    if changed:
        conn.commit()

        if table_exists(cursor, "buyers"):
            cursor.execute(
                "UPDATE buyers SET pipeline_stage = 'Discovered' "
                "WHERE pipeline_stage IS NULL"
            )
            conn.commit()

        print("Migration complete.")
    else:
        print("Nothing to do - database already up to date.")

    conn.close()


if __name__ == "__main__":
    main()
