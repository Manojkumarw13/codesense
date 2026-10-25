"""Idempotent RBAC seed data — Phase 22 Task 3.

Inserts the six roles and the permission rows referenced by the permission
matrix. There is no ``role_permission`` association table yet, so the matrix
itself (role -> permission codenames) lives in code here and is applied by
callers of :func:`seed_roles_and_permissions`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.core import Permission, Role

ROLES: tuple[str, ...] = (
    "ADMIN",
    "ENGINEERING_LEADER",
    "ENGINEERING_MANAGER",
    "TECH_LEAD",
    "ANALYST",
    "DEVELOPER",
)

PERMISSION_MATRIX: dict[str, list[str]] = {
    "ADMIN": ["*"],
    "ENGINEERING_LEADER": [
        "org:read",
        "org:settings",
        "team:read",
        "team:manage",
        "project:read",
        "project:manage",
        "insights:read",
        "insights:export",
    ],
    "ENGINEERING_MANAGER": [
        "org:read",
        "team:read",
        "team:manage",
        "project:read",
        "project:manage",
        "insights:read",
    ],
    "TECH_LEAD": ["team:read", "project:read", "project:manage", "insights:read"],
    "ANALYST": [
        "org:read",
        "team:read",
        "project:read",
        "insights:read",
        "insights:export",
    ],
    "DEVELOPER": ["team:read", "project:read", "insights:read"],
}


def seed_roles_and_permissions(db: Session) -> None:
    """Insert roles and permissions, idempotently (safe to re-run).

    Names already inserted this call are tracked in memory as well as read
    from the DB, because the session runs with ``autoflush=False`` so pending
    inserts are invisible to later queries in the same loop.
    """
    existing_roles = {row.name for row in db.query(Role.name).all()}
    for name in ROLES:
        if name not in existing_roles:
            db.add(Role(name=name))
            existing_roles.add(name)

    existing_permissions = {row.name for row in db.query(Permission.name).all()}
    for permissions in PERMISSION_MATRIX.values():
        for name in permissions:
            if name == "*" or name in existing_permissions:
                continue
            db.add(Permission(name=name))
            existing_permissions.add(name)

    db.commit()
