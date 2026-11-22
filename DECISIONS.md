# Engineering decisions

## Compare System B with the A total
Alternative considered — use A’s base amount.
Reason — the A total includes the adjustment. Clean pairs agree at the total.

## Store money as integer cents
Alternative considered — store SQLite floating-point numbers.
Reason — cents make sums and differences exact for these two-decimal exports. Invalid or blank amounts stay null. The original text stays in the raw snapshot.

## Normalize only recognized reference formats
Alternative considered — take the first digits in any string.
Reason — accepting numeric IDs with an optional REC prefix handles the real variations while avoiding accidental matches from unrelated text.

## Recognize valid splits
Alternative considered — flag every repeated reference as a duplicate.
Reason — REC-1055’s two amounts sum to its total. Multiple known entries that fail this sum check are reported as a duplicate, with their combined value.

## Compare voided records normally
Alternative considered — flag every entry linked to a voided A record.
Reason — B has no status field or documented reversal semantics. A matching amount alone cannot establish a voiding error.

## Report dates and locations
Alternative considered — inspect amounts only.
Reason — an incorrect branch or posting date can matter even when amounts agree. Each rule has a dedicated test.

## Publish cross-organization matches only to the A owner
Alternative considered — send both locations to the UI.
Reason — report the location conflict using only the A record. Withhold the B side, including its value and any derived difference. B-only orphans belong to their own branch’s organization.

## Replace the snapshot atomically
Alternative considered — append every time the import runs.
Reason — complete exports can be reloaded without multiplying rows or keeping stale findings. One SQLite transaction publishes the source rows and their organization-scoped findings together.
