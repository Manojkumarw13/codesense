"""RBAC guards — Phase 22 Task 3.

``require_role`` and ``require_team_access`` are FastAPI dependency factories.
The guard logic itself is a plain function (``check_role`` /
``check_team_access``) that takes ``current_user`` and a DB session and
returns the user or raises ``AuthError``, so it is unit-testable without
FastAPI machinery.

The caller wires ``current_user`` and ``db`` through ``Depends`` when using
these as FastAPI dependencies; unit tests call the returned callable directly.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from backend.app.auth.auth import AuthError
from backend.app.models.core import Role, TeamMember, User, UserRole


def check_role(db: Session, user: User, allowed_roles: list[str]) -> bool:
    """Return True if ``user`` holds at least one of ``allowed_roles``."""
    allowed = set(allowed_roles)
    if not allowed:
        return False
    role_names = {
        name
        for (name,) in db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    }
    return bool(role_names & allowed)


def check_team_access(
    db: Session, user: User, allowed_team_ids: list[uuid.UUID] | None = None
) -> bool:
    """Return True if ``user`` is a member of an allowed team.

    ``allowed_team_ids=None`` means membership in *any* team suffices.
    """
    member_ids = {
        team_id
        for (team_id,) in db.query(TeamMember.team_id)
        .filter(TeamMember.user_id == user.id)
        .all()
    }
    if not member_ids:
        return False
    if allowed_team_ids is None:
        return True
    return bool(member_ids & set(allowed_team_ids))


def require_role(allowed_roles: list[str]):
    """FastAPI dependency: user must hold one of ``allowed_roles``, else 403."""

    def dependency(current_user: User, db: Session):
        if not check_role(db, current_user, allowed_roles):
            raise AuthError(status_code=403, detail="Forbidden: insufficient role")
        return current_user

    return dependency


def require_team_access(
    allowed_team_ids: list[uuid.UUID] | None = None,
):
    """FastAPI dependency: user must be a member of an allowed team, else 403."""

    def dependency(current_user: User, db: Session):
        if not check_team_access(db, current_user, allowed_team_ids):
            raise AuthError(
                status_code=403, detail="Forbidden: insufficient team access"
            )
        return current_user

    return dependency
