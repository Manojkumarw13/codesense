"""AI explainer API — Phase 19 (optional, synchronous, privacy-gated)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.ai.explainer import (
    USE_CASES,
    build_context,
    explain,
    fallback_explanation,
)
from backend.app.core.connectivity import InternetState, get_internet_state
from backend.app.core.database import get_db
from backend.app.core.settings import settings
from backend.app.privacy.gateway import PrivacyBlockedError

router = APIRouter()


@router.post("/ai/explain")
def explain_analytics(
    use_case: str = Query(..., description=f"One of: {', '.join(USE_CASES)}"),
    team_id: uuid.UUID | None = Query(None),  # noqa: B008
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),  # noqa: B008
):
    """Generate a synchronous real-time AI explanation of team analytics.

    Privacy-gated: developer identity is stripped before any LLM call and
    blocked payloads return 422. Falls back to rule-based explanations when
    the LLM is unavailable, so core analytics never break.

    When the cloud AI dependency is offline, short-circuits to the
    rule-based explanation without attempting any network call.
    """
    try:
        if use_case not in USE_CASES:
            raise ValueError(
                f"Unknown use_case '{use_case}'. Expected one of: {', '.join(USE_CASES)}"
            )

        internet = get_internet_state()
        if internet is not InternetState.ONLINE:
            context = build_context(db, team_id, limit)
            return {
                "use_case": use_case,
                "explanation": fallback_explanation(use_case, context),
                "source": "FALLBACK_RULES",
                "model": None,
                "reason": "internet_unavailable",
            }

        return explain(db, use_case, team_id, limit)
    except PrivacyBlockedError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/ai/status")
def ai_status():
    """Report whether cloud AI is usable (honest fallback signalling)."""
    internet = get_internet_state()
    configured = bool(settings.OPENROUTER_API_KEY)
    if internet is not InternetState.ONLINE:
        return {
            "configured": False,
            "model": None,
            "mode": "fallback_rules",
            "internet": internet.value,
            "reason": "internet_unavailable",
        }
    return {
        "configured": configured,
        "model": settings.LLM_MODEL if configured else None,
        "mode": "cloud_ai" if configured else "fallback_rules",
        "internet": internet.value,
        "reason": None if configured else "not_configured",
    }
