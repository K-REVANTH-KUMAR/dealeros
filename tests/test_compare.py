import pytest

from compare import compare
from storage import cents, normalize_ref

OWNERS = {"L1": "org", "L2": "org"}
A = {"record_id": "REC-1", "location": "L1", "date": "2026-03-01", "total": 10000}


def entry(value=10000, **overrides):
    return dict({"entry_id": "E1", "ref": "REC-1", "location": "L1",
                 "date": "2026-03-01", "value": value}, **overrides)


def reasons(entries):
    return [row[1] for row in compare([A], entries, OWNERS)]


def test_missing():
    assert reasons([]) == ["MISSING_IN_B"]


def test_orphan():
    assert compare([], [entry()], OWNERS) == [("org", "ORPHAN_IN_B", "REC-1", "L1", None, 10000)]


def test_duplicate():
    assert reasons([entry(), entry(entry_id="E2")]) == ["DUPLICATE_IN_B"]


def test_different_amount():
    assert reasons([entry(9999)]) == ["VALUE_MISMATCH"]


def test_blank_is_unknown_even_when_a_is_zero():
    findings = compare([dict(A, total=0)], [entry(cents(""))], OWNERS)
    assert findings == [("org", "VALUE_MISMATCH", "REC-1", "L1", 0, None)]


def test_split():
    assert reasons([entry(4000), entry(6000, entry_id="E2")]) == []


def test_clean():
    assert reasons([entry()]) == []


def test_date():
    assert reasons([entry(date="2026-03-02")]) == ["DATE_MISMATCH"]


def test_branch():
    assert reasons([entry(location="L2")]) == ["LOCATION_MISMATCH"]


@pytest.mark.parametrize("raw,expected", [("rec1034", "REC-1034"), (" REC - 1070 ", "REC-1070"),
                                          ("1112", "REC-1112")])
def test_normalized_references_match(raw, expected):
    assert compare([dict(A, record_id=expected)], [entry(ref=normalize_ref(raw))], OWNERS) == []


def test_amount_parsing():
    assert cents("1,25,400.00") == 12540000
    assert cents("0.00") == 0
    assert cents("junk") is None
