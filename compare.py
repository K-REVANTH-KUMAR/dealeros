"""Compare source rows at import time; emit only fields safe for their owner."""
from collections import defaultdict


def compare(records, entries, owners):
    groups = defaultdict(list)
    for entry in entries:
        groups[entry["ref"]].append(entry)

    findings = []
    for record in records:
        rid = record["record_id"]
        location = record["location"]
        org = owners.get(location)
        total = record["total"]
        matches = groups.pop(rid, [])
        if not org:
            continue  # Unmapped rows stay in source storage, outside all tenant views.

        def flag(reason, b_value=None):
            findings.append((org, reason, rid, location, total, b_value))

        if not matches:
            flag("MISSING_IN_B")
            continue
        if any(owners.get(entry["location"]) != org for entry in matches):
            flag("LOCATION_MISMATCH")
            continue  # No foreign value, date, ID or derived difference is published.

        values = [entry["value"] for entry in matches]
        combined = None if None in values else sum(values)
        if combined is None or total is None:
            flag("VALUE_MISMATCH", combined)
        elif combined != total:
            reason = "DUPLICATE_IN_B" if len(matches) > 1 else "VALUE_MISMATCH"
            flag(reason, combined)
        if any(entry["location"] != location for entry in matches):
            flag("LOCATION_MISMATCH", combined)
        if any(entry["date"] != record["date"] for entry in matches):
            flag("DATE_MISMATCH", combined)

    for unmatched in groups.values():
        for entry in unmatched:
            org = owners.get(entry["location"])
            if org:
                findings.append((org, "ORPHAN_IN_B", entry["ref"] or entry["entry_id"],
                                 entry["location"], None, entry["value"]))
    return findings
