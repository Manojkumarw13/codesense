"""INT-01 regression: list ordering is stable when timestamps tie.

Needs a live Postgres (same precondition as test_database.py):
  POSTGRES_SERVER=localhost POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres \\
    POSTGRES_DB=codesense pytest tests/unit/test_ordering_stability.py

Two marker health scores share one calculated_at; limit=1 and limit=100 must
agree on the first row, repeatedly.
"""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.endpoints import health_score as health_score_endpoint
from backend.app.core.database import SessionLocal
from backend.app.models.analytics import HealthScore
from backend.app.models.core import Organization, Team

STAMP = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_health_score_order_stable_on_ties():
    app = FastAPI()
    app.include_router(health_score_endpoint.router)
    client = TestClient(app, raise_server_exceptions=False)
    db = SessionLocal()
    created_ids = []
    try:
        org = Organization(name="Ordering Stability Org", slug="ordering-stability-org")
        db.add(org)
        db.flush()
        team = Team(organization_id=org.id, name="Ordering Stability Team")
        db.add(team)
        db.flush()
        for score in (11.1, 22.2):
            row = HealthScore(
                organization_id=org.id,
                team_id=team.id,
                period_start=STAMP,
                period_end=STAMP,
                score=score,
                calculated_at=STAMP,  # tie on purpose
                component_metrics={},
            )
            db.add(row)
            db.flush()
            created_ids.append(str(row.id))
        db.commit()

        team_id = str(team.id)
        firsts = set()
        for _ in range(3):
            for limit in (1, 100):
                resp = client.get(
                    "/health-score", params={"limit": limit, "team_id": team_id}
                )
                assert resp.status_code == 200, resp.text
                items = resp.json()["items"]
                mine = [i for i in items if i["id"] in created_ids]
                assert mine, "marker rows missing from response"
                firsts.add(mine[0]["id"])
        assert len(firsts) == 1, f"tie order unstable across limits/calls: {firsts}"
    finally:
        for row_id in created_ids:
            row = db.query(HealthScore).get(row_id)
            if row is not None:
                db.delete(row)
        team = db.query(Team).filter(Team.name == "Ordering Stability Team").first()
        if team is not None:
            db.delete(team)
        org = (
            db.query(Organization)
            .filter(Organization.slug == "ordering-stability-org")
            .first()
        )
        if org is not None:
            db.delete(org)
        db.commit()
        db.close()
