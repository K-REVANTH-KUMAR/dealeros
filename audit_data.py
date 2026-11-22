"""Compare original cell contents and multiplicities with the imported snapshot."""
import csv
import json
from collections import Counter

from storage import ROOT, connection


def signature(row):
    return tuple(sorted(row.items()))


def main():
    with connection() as db:
        for filename, table in [("locations", "location"), ("system_a", "system_a"), ("system_b", "system_b")]:
            with (ROOT / "data" / f"{filename}.csv").open(encoding="utf-8-sig", newline="") as stream:
                source = Counter(signature(row) for row in csv.DictReader(stream))
            saved = Counter(signature(json.loads(raw)) for raw, in db.execute(f"SELECT raw FROM {table}"))
            if source != saved:
                raise SystemExit(f"{filename}: stored rows differ from the source")
            print(f"{filename}: verified {source.total()} original rows and every cell")


if __name__ == "__main__":
    main()
