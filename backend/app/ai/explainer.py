"""Deterministic-first explainer with optional LLM upgrade — Phase 19.

Flow per request:
  aggregates (team-level, from DB) -> PrivacyGateway.sanitize (blocks identity)
  -> LLM attempt -> fallback rules on any LLM failure.

`explain()` never raises for LLM problems; only privacy blocks and bad
input raise. The LLM call lives in `_call_llm()` so tests can monkeypatch
one seam without touching the network.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.ai.client import LlmUnavailableError, complete
from backend.app.models.analytics import Anomaly, Bottleneck, HealthScore, Insight
from backend.app.privacy.gateway import PrivacyGateway

USE_CASES = (
    "score_explanation",
    "anomaly_explanation",
    "bottleneck_explanation",
    "trend_summary",
    "investigation_suggestions",
)

SYSTEM_PROMPT = (
    "You explain team-level software-engineering analytics. "
    "You only ever see aggregate team metrics — never individual developers. "
    "Be concise, factual, and never invent people, names, or numbers not in the context."
)


def _row_score(s: HealthScore) -> dict[str, Any]:
    return {
        "score": s.score,
        "previous_score": s.previous_score,
        "score_change": s.score_change,
        "component_metrics": dict(s.component_metrics or {}),
        "period_start": s.period_start.isoformat() if s.period_start else None,
        "period_end": s.period_end.isoformat() if s.period_end else None,
        "calculated_at": s.calculated_at.isoformat() if s.calculated_at else None,
    }


def _row_insight(i: Insight) -> dict[str, Any]:
    return {
        "insight_type": i.insight_type,
        "category": i.category,
        "severity": i.severity,
        "title": i.title,
        "content": (i.content or "")[:500],
        "confidence": i.confidence,
        "generated_by": i.generated_by,
        "status": i.status,
    }


def _row_anomaly(a: Anomaly) -> dict[str, Any]:
    return {
        "severity": a.severity,
        "baseline_value": a.baseline_value,
        "observed_value": a.observed_value,
        "change_percent": a.change_percent,
        "confidence": a.confidence,
        "detected_at": a.detected_at.isoformat() if a.detected_at else None,
    }


def _row_bottleneck(b: Bottleneck) -> dict[str, Any]:
    return {
        "category": b.category,
        "severity": b.severity,
        "title": b.title,
        "description": (b.description or "")[:500],
        "detected_at": b.detected_at.isoformat() if b.detected_at else None,
    }


def build_context(
    db: Session, team_id: Optional[uuid.UUID] = None, limit: int = 10
) -> dict[str, Any]:
    """Collect team-aggregate analytics. No identity fields are selected."""
    limit = max(1, min(limit, 50))
    sq = db.query(HealthScore)
    iq = db.query(Insight)
    aq = db.query(Anomaly)
    bq = db.query(Bottleneck)
    if team_id is not None:
        sq = sq.filter(HealthScore.team_id == team_id)
        iq = iq.filter(Insight.team_id == team_id)
        aq = aq.filter(Anomaly.team_id == team_id)
        bq = bq.filter(Bottleneck.team_id == team_id)
    scores = sq.order_by(HealthScore.calculated_at.desc()).limit(limit).all()
    return {
        "team_id": str(team_id) if team_id else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "health_scores": [_row_score(s) for s in scores],
        "insights": [
            _row_insight(i)
            for i in iq.order_by(Insight.created_at.desc()).limit(limit).all()
        ],
        "anomalies": [
            _row_anomaly(a)
            for a in aq.order_by(Anomaly.detected_at.desc()).limit(limit).all()
        ],
        "bottlenecks": [
            _row_bottleneck(b)
            for b in bq.order_by(Bottleneck.detected_at.desc()).limit(limit).all()
        ],
    }


def fallback_explanation(use_case: str, context: dict[str, Any]) -> str:
    """Deterministic explanation from aggregates — always available offline."""
    scores = context.get("health_scores", [])
    latest = scores[0] if scores else None
    n_insights = len(context.get("insights", []))
    n_anomalies = len(context.get("anomalies", []))
    n_bottlenecks = len(context.get("bottlenecks", []))
    if latest:
        headline = (
            f"Team health score is {latest['score']:.1f}"
            + (
                f" ({latest['score_change']:+.1f} vs previous {latest['previous_score']:.1f})"
                if latest.get("score_change") is not None and latest.get("previous_score") is not None
                else " (no previous score for comparison)"
            )
            + "."
        )
        dims = latest.get("component_metrics", {}) or {}
        weakest = min(dims, key=lambda k: dims[k]) if dims else None
    else:
        headline = "No health scores are available yet — run the simulator to generate data."
        weakest = None
    bodies = {
        "score_explanation": (
            f"{headline} "
            + (
                f"Weakest dimension: {weakest} ({dims[weakest]:.1f}). "
                if weakest
                else "No dimension breakdown is available. "
            )
            + f"Open signals: {n_bottlenecks} bottlenecks, {n_anomalies} anomalies, {n_insights} insights."
        ),
        "anomaly_explanation": (
            f"{n_anomalies} anomalies are currently recorded. "
            + (
                "The most recent detection deviates from its baseline beyond the statistical threshold — "
                "check the Anomalies page evidence for observed vs baseline values."
                if n_anomalies
                else "No unusual metric movement is currently flagged."
            )
        ),
        "bottleneck_explanation": (
            f"{n_bottlenecks} bottlenecks are currently recorded. "
            + (
                "Each bottleneck lists its flow category (review, CI, deployment, workflow, incident) "
                "with the metric evidence that triggered it — see the Bottlenecks page."
                if n_bottlenecks
                else "Flow looks uncongested across review, CI, deployment, and workflow."
            )
        ),
        "trend_summary": (
            f"{headline} History window holds {len(scores)} scored periods. "
            + (
                "Scores are trending from the earliest to the latest period in the Trends view."
                if len(scores) > 1
                else "A single period cannot show a trend yet — more simulator activity will build history."
            )
        ),
        "investigation_suggestions": (
            "Suggested next checks, in order: "
            "1) weakest health dimension and its contributing metrics; "
            "2) highest-severity open bottleneck and its evidence; "
            "3) newest anomaly's observed-vs-baseline gap; "
            "4) whether the simulator scenario explains the pattern (review/CI/deployment/incident)."
        ),
    }
    return bodies[use_case]


def _call_llm(use_case: str, context: dict[str, Any]) -> tuple[str, str]:
    prompt = (
        f"Use case: {use_case}.\n"
        f"Team-aggregate analytics context (JSON):\n{context}\n"
        "Explain what the data shows and what the team should look at next."
    )
    return complete(prompt, system=SYSTEM_PROMPT)


def explain(
    db: Session,
    use_case: str,
    team_id: Optional[uuid.UUID] = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Synchronous real-time explanation. Privacy blocks raise; LLM failures fall back."""
    if use_case not in USE_CASES:
        raise ValueError(f"Unknown use_case '{use_case}'. Expected one of: {', '.join(USE_CASES)}")
    context = PrivacyGateway().sanitize(build_context(db, team_id, limit))
    try:
        text, model = _call_llm(use_case, context)
        source = "CLOUD_AI"
    except LlmUnavailableError:
        text, model = fallback_explanation(use_case, context), None
        source = "FALLBACK_RULES"
    return {
        "use_case": use_case,
        "explanation": text,
        "source": source,
        "model": model,
        "sanitized_context": context,
    }
