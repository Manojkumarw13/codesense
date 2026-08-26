from fastapi import APIRouter

from backend.app.core.observability import metrics_response

router = APIRouter()


@router.get("/metrics")
def get_metrics():
    """Expose Prometheus metrics."""
    return metrics_response()
