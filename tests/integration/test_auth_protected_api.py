# tests/integration/test_auth_protected_api.py
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.core import Organization, Role, Team, TeamMember, User, UserRole

client = TestClient(app)


def _seed_user(email, password, role_name, team_name):
    import uuid

    import bcrypt

    db = SessionLocal()
    org = Organization(id=uuid.uuid4(), name="Org")
    team = Team(id=uuid.uuid4(), organization_id=org.id, name=team_name)
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(id=uuid.uuid4(), name=role_name)
        db.add(role)
    user = User(
        id=uuid.uuid4(),
        organization_id=org.id,
        email=email,
        password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        status="ACTIVE",
    )
    db.add_all([org, team, role, user])
    db.commit()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.add(TeamMember(team_id=team.id, user_id=user.id))
    db.commit()
    db.refresh(user)
    # Read identifiers while the session is still open: commit() expires all
    # attributes, and db.close() detaches the instances, so returning
    # user.id / team.id after close raises DetachedInstanceError.
    user_id, team_id = user.id, team.id
    db.close()
    return user_id, team_id


def _login(email, password):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


def test_health_score_requires_auth():
    resp = client.get("/api/v1/health-score")
    assert resp.status_code == 401


def test_health_score_requires_team_access():
    _seed_user("a@example.com", "P1!", "DEVELOPER", "team-a")
    _, team_b = _seed_user("b@example.com", "P2!", "DEVELOPER", "team-b")
    token_a = _login("a@example.com", "P1!").json()["access_token"]
    resp = client.get(
        "/api/v1/health-score",
        params={"team_id": str(team_b)},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 403


def test_health_score_allows_own_team():
    _, team_a = _seed_user("a@example.com", "P1!", "DEVELOPER", "team-a")
    token_a = _login("a@example.com", "P1!").json()["access_token"]
    resp = client.get(
        "/api/v1/health-score",
        params={"team_id": str(team_a)},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
