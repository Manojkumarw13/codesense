from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import get_db
from backend.app.core.exceptions import DatabaseError
from backend.app.core.redis import is_redis_available
from backend.app.core.observability import METRICS_ENABLED
from backend.app.worker.base import get_worker_stats

router = APIRouter()

@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        raise DatabaseError(message=f"Database connection failed: {str(e)}")

    # Infrastructure checks – never raise, just report degraded
    redis_status = "connected" if is_redis_available() else "degraded (fallback)"
    worker = get_worker_stats()
    return {
        "status": "ok",
        "database": db_status,
        "redis": redis_status,
        "worker": {
            "healthy": worker.is_healthy,
            "jobs_processed": worker.jobs_processed,
            "jobs_failed": worker.jobs_failed,
            "last_run_at": worker.last_run_at,
        },
        "metrics": "enabled" if METRICS_ENABLED else "disabled",
    }


@router.get("/health/detailed")
def get_detailed_health(db: Session = Depends(get_db)):
    """Detailed health for observability / k8s probes."""
    return get_health(db)

