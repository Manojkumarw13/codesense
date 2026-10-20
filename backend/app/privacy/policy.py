"""Small-team privacy policy — Phase 20.

Read-time controls only: stored analytics rows are never mutated. The rules
here decide what an API response may show when a team's contributor
population is small enough that drill-down evidence could deanonymise an
individual.

This module is **not** a substitute for the LLM-bound privacy gateway:
``backend.app.privacy.gateway`` remains the single choke point for anything
bound for an LLM. Never feed a payload masked here to ``/ai/explain`` — a
pseudonym is not recognisable as identity to the gateway's scanner.

Pseudonyms are derived with a keyed HMAC. The key is resolved by
``_effective_secret()``: an explicitly configured salt wins, then a real
(non-placeholder) ``SECRET_KEY``, and only as a last resort a random
per-process secret — so a default deployment never signs with a value that
ships in the repository. A per-process secret is stable for the lifetime of
the process but not across restarts, so a deployment that needs stable
pseudonyms across restarts must set ``PRIVACY_PSEUDONYM_SALT``.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.settings import settings
from backend.app.privacy.gateway import EMAIL_RE

__all__ = [
    "MIN_TEAM_SIZE",
    "count_contributors",
    "is_small_team",
    "mask_evidence",
    "mask_identity",
    "suppression_metadata",
]

MIN_TEAM_SIZE: int = settings.MIN_TEAM_SIZE

REDACTED = "***"
SUPPRESSION_REASON = "small_team_aggregation_threshold"

# Keys whose value identifies an actor: pseudonymised (stable per actor).
ACTOR_KEY_TOKENS = frozenset(
    {
        "actor",
        "actor_ref",
        "author",
        "committer",
        "reviewer",
        "assignee",
        "reporter",
        "developer",
        "user",
        "owner",
        "created_by",
        "submitted_by",
        "merged_by",
    }
)

# Keys whose value is an email address: redacted, never pseudonymised.
EMAIL_KEY_TOKENS = frozenset({"email", "e_mail", "mail"})

# Secrets that ship with the repository or the compose file. Using one of
# them as the pseudonym key would make the mapping reproducible by anyone
# who has seen the source, so they count as "no secret configured".
PLACEHOLDER_SECRETS = frozenset({"supersecretkeyreplaceinproduction", "changeme"})

# Per-process fallback key, generated once at import time. It is never
# regenerated per call, so a pseudonym stays stable for the lifetime of the
# process; it is not stable across restarts.
_PROCESS_SECRET: str = secrets.token_bytes(32).hex()

_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_KEY_SEPARATOR_RE = re.compile(r"[^0-9a-z]+")


def _min_team_size(min_team_size: int | None) -> int:
    return MIN_TEAM_SIZE if min_team_size is None else min_team_size


def _singular(token: str) -> str:
    """Singular stem of a token, so ``actors`` resolves like ``actor``."""
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _key_tokens(key: str) -> set[str]:
    """Normalised token set of a payload key.

    Handles snake_case, kebab-case, dotted and camelCase keys, keeps
    multi-word tokens (e.g. ``created_by``) intact, and adds the singular
    stem of every token so plural payload keys (``actors``, ``reviewers``,
    ``assignees``) resolve to the same branch as their singular form.
    """
    spaced = _CAMEL_BOUNDARY_RE.sub("_", key.strip())
    normalised = _KEY_SEPARATOR_RE.sub("_", spaced.lower()).strip("_")
    tokens = {part for part in normalised.split("_") if part}
    if normalised:
        tokens.add(normalised)
    return tokens | {_singular(token) for token in tokens}


def _is_bare_email(value: str) -> bool:
    """True when the value is exactly one email address and nothing else."""
    return "@" in value and value.count("@") == 1 and " " not in value


def count_contributors(
    db: Session,
    team_id: uuid.UUID | None,
    since: datetime | None = None,
    until: datetime | None = None,
    *,
    organization_id: uuid.UUID | None = None,
) -> int:
    """Distinct non-null ``actor_ref`` count for a scoped population.

    A privacy decision derived from this number is only valid within one
    scope, so the scope is mandatory:

    - ``team_id`` given -> the events of that team.
    - only ``organization_id`` given -> the events of that organisation.
    - neither given -> ``0`` (fail closed). An unscoped count would span
      every tenant and would silently under-mask a small team.

    ``since``/``until`` bound the ``occurred_at`` window inclusively.
    """
    from backend.app.models.core import CanonicalEvent

    if team_id is None and organization_id is None:
        return 0

    query = db.query(CanonicalEvent.actor_ref).filter(
        CanonicalEvent.actor_ref.isnot(None)
    )
    if team_id is not None:
        query = query.filter(CanonicalEvent.team_id == team_id)
    if organization_id is not None:
        query = query.filter(CanonicalEvent.organization_id == organization_id)
    if since is not None:
        query = query.filter(CanonicalEvent.occurred_at >= since)
    if until is not None:
        query = query.filter(CanonicalEvent.occurred_at <= until)
    return len({row[0] for row in query.all() if row[0]})


def is_small_team(contributor_count: int, min_team_size: int | None = None) -> bool:
    """True when the contributor population is below the aggregation threshold."""
    return contributor_count < _min_team_size(min_team_size)


def mask_evidence(evidence: dict[str, Any] | None) -> dict[str, Any]:
    """Mask metric-level evidence values, keeping the shape recognisable."""
    if not evidence:
        return {"suppressed": True, "reason": SUPPRESSION_REASON}
    masked: dict[str, Any] = {}
    for key, value in evidence.items():
        if isinstance(value, dict):
            masked[key] = {k: None for k in value}
        else:
            masked[key] = None
    masked["suppressed"] = True
    masked["reason"] = SUPPRESSION_REASON
    return masked


def _effective_secret() -> str:
    """Resolve the key used to derive actor pseudonyms.

    Precedence:

    1. an explicitly configured ``PRIVACY_PSEUDONYM_SALT`` — stable across
       restarts, and what a deployment should set;
    2. otherwise a real ``SECRET_KEY``, i.e. one that is not a shipped
       placeholder;
    3. otherwise a random per-process secret, so a default deployment never
       signs with a value that is published in the repository.

    A per-process secret keeps pseudonyms stable within the process but not
    across restarts; that trade-off is acceptable because raw event payloads
    are hidden by default and pseudonymisation is defence in depth.
    """
    salt = settings.PRIVACY_PSEUDONYM_SALT
    if salt:
        return salt
    secret_key = settings.SECRET_KEY
    if secret_key and secret_key not in PLACEHOLDER_SECRETS:
        return secret_key
    return _PROCESS_SECRET


def _pseudonymise(actor_ref: str) -> str:
    """Stable, keyed pseudonym for an actor reference.

    The digest is an HMAC over a server-side secret, so the mapping cannot
    be reversed (or brute-forced) without that secret, while remaining
    stable for the same actor across calls, events and processes.
    """
    secret = _effective_secret()
    digest = hmac.new(
        secret.encode("utf-8"), actor_ref.encode("utf-8"), hashlib.sha256
    ).hexdigest()[:8]
    return f"actor-{digest}"


def _mask_identity(value: Any, key: str | None) -> Any:
    """Recursive worker for :func:`mask_identity`, carrying the key context."""
    if isinstance(value, dict):
        return {k: _mask_identity(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mask_identity(item, key) for item in value]
    if not isinstance(value, str):
        return value
    if not EMAIL_RE.search(value):
        return value
    if key is None:
        # No key context to judge by: keep the plain rule — a bare email is
        # treated as an actor reference, an email embedded in text is redacted.
        if _is_bare_email(value):
            return _pseudonymise(value)
        return REDACTED
    tokens = _key_tokens(key)
    if tokens & EMAIL_KEY_TOKENS:
        return REDACTED
    if tokens & ACTOR_KEY_TOKENS:
        return _pseudonymise(value)
    # Free text: redact the whole value rather than leak part of it.
    return REDACTED


def mask_identity(value: Any) -> Any:
    """Recursively pseudonymise actor refs and redact email-shaped strings.

    Only email-shaped values are transformed; anything else is left untouched.
    For an email-shaped value, the key decides the rule:

    - an actor/identity key (``actor_ref``, ``author``, ``owner``, …, also
      their plural and compound forms such as ``actors`` or ``created_by``) ->
      the value is pseudonymised, stably, per actor;
    - an email key (``email``, ``e_mail``, ``mail``) -> the value is redacted;
    - any other key (free text) -> the value is redacted in full.

    A list under an actor key is pseudonymised element-wise, so every actor
    keeps its own stable pseudonym.

    A key that is not recognised as an actor key is redacted rather than
    pseudonymised, so a stray email can never become a joinable per-person
    identifier.
    """
    return _mask_identity(value, None)


def suppression_metadata(
    contributor_count: int, min_team_size: int | None = None
) -> dict[str, Any]:
    """Machine-readable explanation of why a payload was suppressed."""
    return {
        "suppressed": True,
        "min_team_size": _min_team_size(min_team_size),
        "contributors": contributor_count,
        "reason": SUPPRESSION_REASON,
    }
