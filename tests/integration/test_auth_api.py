# tests/integration/test_auth_api.py
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.core import Organization, Role, Team, TeamMember, User, UserRole

client = TestClient(app)


def _seed_user(email="alice@example.com", password="Password1!", role_name="DEVELOPER"):
    import uuid

    import bcrypt

    db = SessionLocal()
    org = Organization(id=uuid.uuid4(), name="Auth Org")
    team = Team(id=uuid.uuid4(), organization_id=org.id, name="Auth Team")
    role = Role(id=uuid.uuid4(), name=role_name)
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


def test_login_returns_tokens_and_user():
    _user_id, _team_id = _seed_user()
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "Password1!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and "refresh_token" in body
    assert body["user"]["email"] == "alice@example.com"


def test_login_wrong_password_401_no_enumeration():
    _seed_user()
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    resp2 = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "x"}
    )
    assert resp2.status_code == 401
    assert resp.json() == resp2.json()


def test_refresh_issues_new_access_token():
    _user_id, _ = _seed_user()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "Password1!"},
    )
    refresh_token = login.json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me_requires_authentication():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
