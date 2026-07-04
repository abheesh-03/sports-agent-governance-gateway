"""Initialize the database and verify fake data files are present.

The fake business data lives as static JSON files in the ``data`` directory, so
"seeding" here means: create the audit/approval tables and report a summary of
the fake data the tools will read. Run with:

    python -m scripts.seed_data
"""
import sys
from pathlib import Path

# Ensure the project root is importable when run as a script.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import init_db  # noqa: E402
from tools import load_data  # noqa: E402

DATA_FILES = {
    "schedule.json": "events",
    "policies.json": "policies",
    "tickets.json": "ticket listings",
    "fans.json": "fan profiles",
    "content_library.json": "content records",
}


def main() -> None:
    print("Initializing database (audit_logs, approval_requests)...")
    init_db()
    print("Database tables ready.\n")

    print("Fake data summary:")
    for filename, label in DATA_FILES.items():
        try:
            records = load_data(filename)
            print(f"  - {filename}: {len(records)} {label}")
        except FileNotFoundError:
            print(f"  - {filename}: MISSING")

    print("\nSeed complete. All data is fictional (Northstar Athletics).")


if __name__ == "__main__":
    main()
