"""Small-team privacy policy — Phase 20.

Read-time controls only: stored analytics rows are never mutated. The rules
here decide what an API response may show when a team's contributor
population is small enough that drill-down evidence could deanonymise an
individual.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.settings import settings

MIN_TEAM_SIZE: int = settings.MIN_TEAM_SIZE

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
REDACTED = "***"
SUPPRESSION_REASON = "small_team_aggregation_threshold"


def _min_team_size(min_team_size: int | None) -> int:
    return MIN_TEAM_SIZE if min_team_size is None else min_team_size


def count_contributors(
    db: Session,
    team_id: uuid.UUID | None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> int:
    """Distinct non-null actor_ref count for a team in the given window."""
    from backend.app.models.core import CanonicalEvent

    query = db.query(CanonicalEvent.actor_ref).filter(
        CanonicalEvent.actor_ref.isnot(None)
    )
    if team_id is not None:
        query = query.filter(CanonicalEvent.team_id == team_id)
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


def _pseudonymise(actor_ref: str) -> str:
    digest = hashlib.sha256(actor_ref.encode("utf-8")).hexdigest()[:8]
    return f"actor-{digest}"


def mask_identity(value: Any) -> Any:
    """Recursively pseudonymise actor refs and redact email-shaped strings."""
    if isinstance(value, dict):
        return {key: mask_identity(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_identity(item) for item in value]
    if not isinstance(value, str):
        return value
    if EMAIL_RE.search(value):
        if "@" in value and value.count("@") == 1 and " " not in value:
            return _pseudonymise(value)
        return REDACTED
    return value


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
