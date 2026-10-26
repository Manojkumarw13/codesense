"""Shared auth dependencies for the analytics read endpoints.

Consolidates the auth-guard boilerplate (``_current_user``, role check,
team access check, ``REQUIRED_ROLES``) that was duplicated across
``health_score.py``, ``insights.py``, ``anomalies.py`` and
``bottlenecks.py`` into one module so a single fix covers every endpoint.

``auth.py`` and ``auth/dependencies.py`` stay read-only; this module only
imports from them and wires ``get_current_user``, ``require_role`` and
``require_team_access`` through FastAPI ``Depends``.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.auth import AuthError, get_current_user
from backend.app.auth.dependencies import require_role, require_team_access
from backend.app.auth.seeds import ROLES
from backend.app.core.database import get_db
from backend.app.models.core import User

REQUIRED_ROLES = list(ROLES)


def _current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    """Resolve ``Authorization: Bearer <token>`` to the current active user.

    Returns HTTP 401 when the header is missing or the token is invalid.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    token = authorization[len("Bearer ") :].strip()
    try:
        return get_current_user(db, token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


def require_auth(allowed_roles: list[str] = REQUIRED_ROLES):
    """FastAPI dependency: authenticate + require one of ``allowed_roles``.

    Auth failure (missing/invalid token) -> 401; insufficient role -> 403.
    Returns the resolved :class:`~backend.app.models.core.User`.
    """

    def dependency(
        current_user: User = Depends(_current_user),
        db: Session = Depends(get_db),  # noqa: B008
    ) -> User:
        try:
            require_role(allowed_roles)(current_user, db)
        except AuthError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail)
        return current_user

    return dependency


def require_team_access_if(
    current_user: User, db: Session, team_id: Optional[uuid.UUID]
) -> None:
    """Body-callable guard: require team membership when ``team_id`` is present.

    A no-op when ``team_id is None`` (role guard only), matching the brief:
    the team guard applies only when the ``team_id`` query filter is present.
    Raises HTTP 403 on insufficient team access.

    Called in the endpoint body so the endpoint's own ``team_id`` query
    parameter can be reused for both the guard and the DB filter (one
    parameter's default cannot reference another parameter in the same
    FastAPI signature).
    """
    if team_id is None:
        return
    try:
        require_team_access([team_id])(current_user, db)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
