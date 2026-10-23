"""Shared serialisation for detection rows — Phase 20.

Insights, anomalies and bottlenecks are the same kind of row: a severity,
some evidence and a timestamp. They therefore share one serialiser and one
privacy decision, so a policy change cannot land in one endpoint and miss
another.

Privacy rule
-------------
A detection is masked when the *effective* contributor count is below
``MIN_TEAM_SIZE``. That count is the most conservative of two scopes:

- the **all-time** count of the row's team (or organisation for an
  organisation-level row);
- the **window** count: the distinct contributors of a trailing window that
  ends at the row's detection timestamp and is
  ``settings.PRIVACY_DETECTION_WINDOW_DAYS`` long.

Taking the minimum closes the leak where a team has many lifetime
contributors but only one person was actually active around the detection:
that detection describes one person and must not be readable.

A row without a usable timestamp has no window and is judged on its
all-time count alone — never on an unbounded window.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.settings import settings
from backend.app.privacy.policy import (
    Scope,
    count_contributors_by_scope,
    is_small_team,
    mask_evidence,
    suppression_metadata,
)

__all__ = [
    "detection_scope",
    "detection_window_scope",
    "serialise_detection",
    "serialise_detections",
]


def _optional_id(value: Any) -> str | None:
    """Render an optional UUID column as a string."""
    return str(value) if value is not None else None


def detection_scope(row: Any) -> Scope:
    """The team / organisation a detection row belongs to, over all time."""
    return (
        getattr(row, "team_id", None),
        getattr(row, "organization_id", None),
        None,
        None,
    )


def _detection_timestamp(row: Any) -> datetime | None:
    """The timestamp the trailing window ends at.

    Anomalies and bottlenecks are detected at ``detected_at``; an insight
    falls back to ``created_at``.
    """
    for attribute in ("detected_at", "created_at"):
        value = getattr(row, attribute, None)
        if value is not None:
            return value
    return None


def detection_window_scope(row: Any) -> Scope | None:
    """The trailing window ending at the row's detection timestamp.

    ``None`` when the row carries no usable timestamp.
    """
    timestamp = _detection_timestamp(row)
    if timestamp is None:
        return None
    team_id, organization_id, _since, _until = detection_scope(row)
    return (
        team_id,
        organization_id,
        timestamp - timedelta(days=settings.PRIVACY_DETECTION_WINDOW_DAYS),
        timestamp,
    )


def _effective_contributors(scope_counts: dict[Scope, int], row: Any) -> int:
    """The most conservative contributor count used for masking.

    ``min(all-time count, window count)`` — see the module docstring.
    """
    all_time = scope_counts[detection_scope(row)]
    window = detection_window_scope(row)
    if window is None:
        return all_time
    return min(all_time, scope_counts[window])


def _page_counts(db: Session, rows: Sequence[Any]) -> dict[Any, int]:
    """Effective contributor count per row, from a single query for the page."""
    scopes: list[Scope] = []
    for row in rows:
        scopes.append(detection_scope(row))
        window = detection_window_scope(row)
        if window is not None:
            scopes.append(window)
    scope_counts = count_contributors_by_scope(db, scopes)
    return {row.id: _effective_contributors(scope_counts, row) for row in rows}


def _serialise(row: Any, contributors: int) -> dict[str, Any]:
    """Convert a detection row into its API shape, with masking applied."""
    privacy: dict[str, Any] = {"suppressed": False}
    evidence = getattr(row, "evidence", None)
    if is_small_team(contributors):
        evidence = mask_evidence(evidence)
        privacy = suppression_metadata(contributors)
    # `source_metrics` and `metric_id` are read by the shipped dashboard
    # (InsightDetail.tsx / AnomalyDetail.tsx) - do not trim this key set.
    return {
        "id": str(row.id),
        "organization_id": _optional_id(getattr(row, "organization_id", None)),
        "team_id": _optional_id(getattr(row, "team_id", None)),
        "project_id": _optional_id(getattr(row, "project_id", None)),
        "request_id": _optional_id(getattr(row, "request_id", None)),
        "metric_id": _optional_id(getattr(row, "metric_id", None)),
        "insight_type": getattr(row, "insight_type", None),
        "category": getattr(row, "category", None),
        "severity": getattr(row, "severity", None),
        "title": getattr(row, "title", None),
        "description": getattr(row, "description", None),
        "content": getattr(row, "content", None),
        "confidence": getattr(row, "confidence", None),
        "generated_by": getattr(row, "generated_by", None),
        "status": getattr(row, "status", None),
        "baseline_value": getattr(row, "baseline_value", None),
        "observed_value": getattr(row, "observed_value", None),
        "change_percent": getattr(row, "change_percent", None),
        "evidence": evidence,
        "source_metrics": getattr(row, "source_metrics", None),
        "detected_at": getattr(row, "detected_at", None),
        "created_at": getattr(row, "created_at", None),
        "privacy": privacy,
    }


def serialise_detection(row: Any, db: Session) -> dict[str, Any]:
    """Serialise an Insight/Anomaly/Bottleneck row with privacy masking applied."""
    counts = _page_counts(db, [row])
    return _serialise(row, counts[row.id])


def serialise_detections(rows: Sequence[Any], db: Session) -> list[dict[str, Any]]:
    """Serialise a page of detection rows with one contributor-count query."""
    counts = _page_counts(db, rows)
    return [_serialise(row, counts[row.id]) for row in rows]
