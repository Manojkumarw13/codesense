"""Unit tests for RBAC guards (Phase 22 Task 3).

The guards are unit-tested without FastAPI machinery: the dependency returned
by ``require_role`` / ``require_team_access`` is called directly with a
``current_user`` and a DB session. It returns the user on success and raises
``AuthError`` (HTTP 403) on denial.
"""

from __future__ import annotations

import uuid

import bcrypt
import pytest
from sqlalchemy.orm import Session

from backend.app.auth.auth import AuthError
from backend.app.auth.dependencies import require_role, require_team_access
from backend.app.core.database import SessionLocal
from backend.app.models.core import (
    Organization,
    Role,
    Team,
    TeamMember,
    User,
    UserRole,
)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _seed_user_with_role(
    db: Session, role_name: str = "DEVELOPER", with_team: bool = True
) -> tuple[User, uuid.UUID | None]:
    """Create org + user + role (+ team membership) and return (user, team_id)."""
    org = Organization(name="RBAC Org")
    db.add(org)
    db.flush()

    user = User(
        id=uuid.uuid4(),
        organization_id=org.id,
        email=f"rbac-{uuid.uuid4().hex}@example.com",
        password_hash=bcrypt.hashpw(b"password", bcrypt.gensalt()).decode(),
        status="ACTIVE",
    )
    db.add(user)

    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))

    team_id: uuid.UUID | None = None
    if with_team:
        team = Team(id=uuid.uuid4(), organization_id=org.id, name="RBAC Team")
        db.add(team)
        db.flush()
        db.add(TeamMember(team_id=team.id, user_id=user.id))
        team_id = team.id

    db.commit()
    # commit() expires attributes; re-fetch a fresh instance for callers.
    user = db.query(User).filter(User.id == user.id).one()
    return user, team_id


def test_require_role_allows_member_and_denies_other(db: Session) -> None:
    user, _ = _seed_user_with_role(db, "DEVELOPER")

    assert require_role(["DEVELOPER"])(user, db) is user
    assert require_role(["DEVELOPER", "ADMIN"])(user, db) is user

    with pytest.raises(AuthError) as exc:
        require_role(["ADMIN"])(user, db)
    assert exc.value.status_code == 403


def test_require_role_user_without_roles_denied(db: Session) -> None:
    org = Organization(name="No Role Org")
    db.add(org)
    db.flush()
    user = User(
        id=uuid.uuid4(),
        organization_id=org.id,
        email=f"rbac-{uuid.uuid4().hex}@example.com",
        password_hash=bcrypt.hashpw(b"password", bcrypt.gensalt()).decode(),
        status="ACTIVE",
    )
    db.add(user)
    db.commit()
    user = db.query(User).filter(User.id == user.id).one()

    with pytest.raises(AuthError) as exc:
        require_role(["DEVELOPER"])(user, db)
    assert exc.value.status_code == 403


def test_require_team_access_allows_member_and_denies_other(db: Session) -> None:
    user, team_id = _seed_user_with_role(db, "DEVELOPER", with_team=True)
    assert team_id is not None

    assert require_team_access([team_id])(user, db) is user
    # None means "any team" suffices.
    assert require_team_access()(user, db) is user

    with pytest.raises(AuthError) as exc:
        require_team_access([uuid.uuid4()])(user, db)
    assert exc.value.status_code == 403


def test_require_team_access_no_membership_denied(db: Session) -> None:
    user, _ = _seed_user_with_role(db, "DEVELOPER", with_team=False)

    with pytest.raises(AuthError) as exc:
        require_team_access()(user, db)
    assert exc.value.status_code == 403


def test_seed_roles_and_permissions_idempotent(db: Session) -> None:
    from backend.app.auth.seeds import seed_roles_and_permissions
    from backend.app.models.core import Permission, Role

    seed_roles_and_permissions(db)
    seed_roles_and_permissions(db)  # re-running must not fail or duplicate

    roles = {row.name for row in db.query(Role).all()}
    expected = {
        "ADMIN",
        "ENGINEERING_LEADER",
        "ENGINEERING_MANAGER",
        "TECH_LEAD",
        "ANALYST",
        "DEVELOPER",
    }
    assert expected.issubset(roles)

    permissions = {row.name for row in db.query(Permission).all()}
    assert permissions  # at least one permission row seeded
