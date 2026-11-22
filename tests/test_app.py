import json

import pytest
from fastapi.testclient import TestClient

from app import create_app
from import_data import import_data
from storage import connection


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "test.sqlite3"
    import_data(path)
    return path


def test_reimport_preserves_data(database):
    import_data(database)
    with connection(database) as db:
        for table, count in [("location", 5), ("system_a", 120), ("system_b", 121), ("finding", 11)]:
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == count
        raw, parsed = db.execute("SELECT raw, value FROM system_b WHERE value IS NULL").fetchone()
        assert json.loads(raw)["value"] == ""
        assert parsed is None
        assert db.execute("SELECT actor FROM system_a WHERE record_id='REC-1050'").fetchone()[0] is None


@pytest.mark.parametrize("org", ["ORG-A", "ORG-B"])
def test_tenant_boundary(database, org):
    client = TestClient(create_app(database))
    response = client.get("/api/disagreements/", params={"org": org})
    assert response.status_code == 200
    rows = response.json()
    with connection(database) as db:
        own_locations = {r[0] for r in db.execute("SELECT location_id FROM location WHERE org=?", (org,))}
        foreign_records = {r[0] for r in db.execute(
            "SELECT record_id FROM system_a JOIN location ON location=location_id WHERE org<>?", (org,))}
    assert all(row["location"] in own_locations and row["record_id"] not in foreign_records for row in rows)
    cross = [r for r in rows if r["record_id"] == "REC-1077"]
    if org == "ORG-A":
        assert cross == [dict(reason="LOCATION_MISMATCH", record_id="REC-1077", location="LOC-102",
                              a_value="83361.40", b_value=None, difference=None)]
    else:
        assert cross == []


def test_api_controls(database):
    client = TestClient(create_app(database))
    url = "/api/disagreements/"
    assert client.get(url).status_code == 422
    assert client.get(url, params={"org": "unknown"}).status_code == 404
    for sort, first in [("value", "REC-1027"), ("-value", "REC-1064")]:
        rows = client.get(url, params={"org": "ORG-A", "reason": "VALUE_MISMATCH", "sort": sort}).json()
        assert rows[0]["record_id"] == first
        assert {row["reason"] for row in rows} == {"VALUE_MISMATCH"}
