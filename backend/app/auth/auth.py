"""Authentication primitives — Phase 22.

Password hashing (bcrypt), JWT access/refresh tokens, and the
get_current_user dependency. Tokens carry user_id + team/org scopes only;
they never carry developer identity beyond what the schema already stores.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

import bcrypt
import jwt
from jwt import PyJWTError
from sqlalchemy.orm import Session

from backend.app.core.settings import settings
from backend.app.models.core import User


class AuthError(Exception):
    """Raised on auth failure; carries the HTTP status to return."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(settings.BCRYPT_ROUNDS)
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:  # noqa: BLE001 - malformed hash is a verify failure
        return False


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def create_access_token(
    data: dict[str, Any], expires_delta: _dt.timedelta | None = None
) -> str:
    to_encode = dict(data)
    expire = _now() + (
        expires_delta or _dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": _now(), "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = dict(data)
    expire = _now() + _dt.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": _now(), "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except PyJWTError as exc:
        raise AuthError(
            status_code=401, detail="Could not validate credentials"
        ) from exc


def get_current_user(db: Session, token: str) -> User:
    payload = decode_token(token)
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AuthError(status_code=401, detail="Could not validate credentials")
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise AuthError(status_code=401, detail="Could not validate credentials")
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None or user.status != "ACTIVE":
        raise AuthError(status_code=401, detail="User inactive or not found")
    return user
