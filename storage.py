"""SQLite source snapshots. Each raw JSON object preserves the original CSV cells."""
import csv
import json
import re
import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "dealeros.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS location (
    location_id TEXT PRIMARY KEY, org TEXT NOT NULL, name TEXT, raw TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS system_a (
    record_id TEXT PRIMARY KEY, location TEXT, date TEXT, total INTEGER,
    actor TEXT, state TEXT, raw TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS system_b (
    entry_id TEXT PRIMARY KEY, ref TEXT, location TEXT, date TEXT,
    value INTEGER, raw TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS finding (
    org TEXT NOT NULL, reason TEXT NOT NULL, record_id TEXT, location TEXT,
    a_value INTEGER, b_value INTEGER
);
"""


@contextmanager
def connection(path=DATABASE):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def normalize_ref(raw):
    match = re.fullmatch(r"(?:REC\s*-?\s*)?(\d+)", raw.strip(), re.IGNORECASE)
    return f"REC-{match[1]}" if match else None


def cents(raw):
    # Accept ungrouped, Western-grouped and Indian-grouped currency.
    amount = raw.strip()
    pattern = r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})+,\d{3})(?:\.\d{1,2})?"
    if not re.fullmatch(pattern, amount):
        return None
    number = int(Decimal(amount.replace(",", "")) * 100)
    return number if -(2**63) <= number < 2**63 else None


def source_rows(folder, filename):
    with (folder / filename).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            yield {key: (value or "").strip() for key, value in row.items()}, json.dumps(row)


def load_sources(db, folder):
    issues = []
    for row, raw in source_rows(folder, "locations.csv"):
        db.execute("INSERT INTO location VALUES (?, ?, ?, ?)",
                   (row["location_id"], row["org_id"], row["location_name"], raw))
    for row, raw in source_rows(folder, "system_a.csv"):
        total = cents(row["total_value"])
        if total is None or not row["actor_id"]:
            issues.append(f"{row['record_id']}: empty actor or unknown total")
        db.execute("INSERT INTO system_a VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (row["record_id"], row["location_id"], row["event_date"], total,
                    row["actor_id"] or None, row["state"], raw))
    for row, raw in source_rows(folder, "system_b.csv"):
        ref = normalize_ref(row["record_ref"])
        amount = cents(row["value"])
        if ref != row["record_ref"] or amount is None:
            issues.append(f"{row['entry_id']}: reference normalized or amount unknown")
        db.execute("INSERT INTO system_b VALUES (?, ?, ?, ?, ?, ?)",
                   (row["entry_id"], ref, row["location_id"], row["recorded_on"], amount, raw))
    return issues
