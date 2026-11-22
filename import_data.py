"""Load all three files and publish their findings as one transaction."""
from compare import compare
from storage import DATABASE, ROOT, SCHEMA, connection, load_sources


def import_data(path=DATABASE, folder=ROOT / "data"):
    with connection(path) as db:
        db.executescript(SCHEMA)
        for table in ("finding", "system_b", "system_a", "location"):
            db.execute(f"DELETE FROM {table}")
        issues = load_sources(db, folder)
        owners = dict(db.execute("SELECT location_id, org FROM location"))
        records = db.execute("SELECT * FROM system_a")
        entries = db.execute("SELECT * FROM system_b")
        db.executemany("INSERT INTO finding VALUES (?, ?, ?, ?, ?, ?)",
                       compare(records, entries, owners))
        for issue in issues:
            print(issue)
        for table in ("location", "system_a", "system_b", "finding"):
            count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count}")


if __name__ == "__main__":
    import_data()
