"""AI explainer API — Phase 19 (optional, synchronous, privacy-gated)."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.ai.explainer import USE_CASES, explain
from backend.app.core.database import get_db
from backend.app.core.settings import settings
from backend.app.privacy.gateway import PrivacyBlockedError

router = APIRouter()


@router.post("/ai/explain")
def explain_analytics(
    use_case: str = Query(..., description=f"One of: {', '.join(USE_CASES)}"),
    team_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Generate a synchronous real-time AI explanation of team analytics.

    Privacy-gated: developer identity is stripped before any LLM call and
    blocked payloads return 422. Falls back to rule-based explanations when
    the LLM is unavailable, so core analytics never break.
    """
    try:
        return explain(db, use_case, team_id, limit)
    except PrivacyBlockedError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/ai/status")
def ai_status():
    """Report whether cloud AI is configured (honest fallback signalling)."""
    configured = bool(settings.OPENROUTER_API_KEY)
    return {
        "configured": configured,
        "model": settings.LLM_MODEL if configured else None,
        "mode": "cloud_ai" if configured else "fallback_rules",
    }
