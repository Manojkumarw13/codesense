"""Auth API — login, refresh, me (Phase 22 Task 2).

Endpoints live under ``API_V1_STR/auth``. ``login`` performs constant-work
verification so a missing user and a wrong password are indistinguishable
(timing-safe, no user enumeration). ``refresh`` validates a ``type=refresh``
JWT and issues a new access token. ``me`` requires an
``Authorization: Bearer <token>`` header resolved through ``get_current_user``.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.auth.auth import (
    AuthError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    verify_password,
)
from backend.app.core.database import get_db
from backend.app.models.core import Role, Team, TeamMember, User, UserRole

router = APIRouter()

# Hash of a value no real user ever has. Login always runs bcrypt once, using
# this hash when the email is unknown, so missing vs present user takes the
# same path and cannot be distinguished by timing (no user enumeration).
_DUMMY_PASSWORD_HASH = "$2b$12$wC5xVlxVu7C.BFNstS5oxuCAxDQa1YZjG5QS8.HJJCZU9AgRLc9qy"


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _user_context(db: Session, user: User) -> dict[str, Any]:
    roles = [
        name
        for (name,) in db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    ]
    teams = [
        name
        for (name,) in db.query(Team.name)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == user.id)
        .all()
    ]
    return {
        "id": str(user.id),
        "email": user.email,
        "roles": roles,
        "teams": teams,
    }


def _current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    """Resolve ``Authorization: Bearer <token>`` to the current active user."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = authorization[len("Bearer ") :].strip()
    try:
        return get_current_user(db, token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/auth/login")
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),  # noqa: B008
):
    user = db.query(User).filter(User.email == payload.email).first()

    # Constant work: always run bcrypt so a missing user and a wrong password
    # are indistinguishable by timing.
    if user is not None and user.password_hash:
        ok = verify_password(payload.password, cast(str, user.password_hash))
    else:
        ok = verify_password(payload.password, _DUMMY_PASSWORD_HASH)

    if not ok or user is None or user.status != "ACTIVE":
        # Deterministic body (no request id) so a wrong password and a missing
        # user produce byte-identical responses — no user enumeration.
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid credentials"},
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_context(db, user),
    }


@router.post("/auth/refresh")
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),  # noqa: B008
):
    try:
        token_payload: dict[str, Any] = decode_token(payload.refresh_token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    sub = token_payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    try:
        user_id = uuid.UUID(sub)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or not found",
        )

    return {"access_token": create_access_token({"sub": str(user.id)})}


@router.get("/auth/me")
def me(
    user: User = Depends(_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    return _user_context(db, user)
