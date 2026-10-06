"""AI privacy gateway — Phase 19.

The single choke point for every LLM-bound payload. It enforces the locked
principle: **developer identity is never sent to any LLM** (cloud or local).

Contract:
- Only team-aggregate data may pass (scores, dimensions, detection rows).
- Any detected identity (email, username/name keys, actor refs, raw payloads
  carrying identity) raises PrivacyBlockedError -> HTTP 422 REQUEST BLOCKED.
- Raw provider payloads are dropped by construction, never forwarded.
"""
import re
from typing import Any

# Keys that must never reach an LLM (case-insensitive substring match).
IDENTITY_KEYS = frozenset(
    {
        "email",
        "e-mail",
        "mail",
        "username",
        "user_name",
        "login",
        "developer",
        "author",
        "committer",
        "assignee",
        "reporter",
        "actor",
        "actor_ref",
        "user_id",
        "developer_id",
        "person",
        "full_name",
        "first_name",
        "last_name",
        "display_name",
    }
)

# Raw blobs that are dropped (not blocked) — they carry provider originals.
RAW_KEYS = frozenset({"payload", "raw_payload", "raw", "original_payload"})

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class PrivacyBlockedError(ValueError):
    """Raised when a payload contains developer identity. Message is public-safe."""


def _is_identity_key(key: str) -> bool:
    lowered = key.strip().lower()
    return any(token in lowered for token in IDENTITY_KEYS)


def _scan(value: Any, path: str = "$") -> None:
    """Recursively scan for identity; raise on first hit."""
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                continue
            if k.strip().lower() in RAW_KEYS:
                continue  # dropped later, not identity per se
            if _is_identity_key(k):
                raise PrivacyBlockedError(f"REQUEST BLOCKED: identity field '{path}.{k}'")
            _scan(v, f"{path}.{k}")
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            _scan(item, f"{path}[{i}]")
    elif isinstance(value, str):
        if EMAIL_RE.search(value):
            raise PrivacyBlockedError(f"REQUEST BLOCKED: email address at '{path}'")


def _strip_raw(value: Any) -> Any:
    """Recursively drop raw provider payload blobs."""
    if isinstance(value, dict):
        return {
            k: _strip_raw(v)
            for k, v in value.items()
            if not (isinstance(k, str) and k.strip().lower() in RAW_KEYS)
        }
    if isinstance(value, list):
        return [_strip_raw(item) for item in value]
    return value


class PrivacyGateway:
    """Validates and sanitizes LLM-bound contexts."""

    def sanitize(self, context: dict[str, Any]) -> dict[str, Any]:
        """Scan for identity (block) then strip raw blobs. Returns safe copy."""
        if not isinstance(context, dict):
            raise PrivacyBlockedError("REQUEST BLOCKED: context must be an object")
        _scan(context)
        return _strip_raw(context)  # type: ignore[return-value]
