"""Organization-scoped read API and locally built React screen."""
from decimal import Decimal
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from storage import DATABASE, ROOT, connection

Reason = Literal["MISSING_IN_B", "ORPHAN_IN_B", "DUPLICATE_IN_B",
                 "VALUE_MISMATCH", "LOCATION_MISMATCH", "DATE_MISMATCH"]


def money(value):
    return None if value is None else format(Decimal(value).scaleb(-2), ".2f")


def create_app(path=DATABASE):
    app = FastAPI(title="DealerOS")

    @app.get("/api/organizations/")
    def organizations():
        with connection(path) as db:
            return [row[0] for row in db.execute("SELECT DISTINCT org FROM location ORDER BY org")]

    @app.get("/api/disagreements/")
    def disagreements(org: str, reason: Reason | None = None,
                      sort: Literal["value", "-value"] = "-value"):
        # Sort on the A amount, using B for orphan entries.
        direction = "DESC" if sort == "-value" else "ASC"
        sql = "SELECT * FROM finding WHERE org = ?"
        params = [org]
        if reason:
            sql += " AND reason = ?"
            params.append(reason)
        sql += f" ORDER BY COALESCE(a_value, b_value) {direction} NULLS LAST, record_id, reason"
        with connection(path) as db:
            if not db.execute("SELECT 1 FROM location WHERE org = ?", (org,)).fetchone():
                raise HTTPException(404, "Unknown organization")
            result = []
            for row in db.execute(sql, params):
                a, b = row["a_value"], row["b_value"]
                result.append(dict(reason=row["reason"], record_id=row["record_id"],
                                   location=row["location"], a_value=money(a), b_value=money(b),
                                   difference=money(b - a) if a is not None and b is not None else None))
            return result

    dist = ROOT / "web" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="screen")
    return app


app = create_app()
