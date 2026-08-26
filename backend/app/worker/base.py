"""Base worker abstraction and telemetry.

Provides:
- BaseWorker interface
- WorkerStats dataclass for observability
- run_once helper for tests/background loop
"""
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from backend.app.core.cache import cache_set

logger = logging.getLogger("codesense.worker.base")


@dataclass
class WorkerStats:
    jobs_processed: int = 0
    jobs_failed: int = 0
    last_run_at: str | None = None
    last_duration_ms: float = 0.0
    is_healthy: bool = True


_stats = WorkerStats()


def get_worker_stats() -> WorkerStats:
    return _stats


def record_success(duration_ms: float):
    _stats.jobs_processed += 1
    _stats.last_duration_ms = duration_ms
    _stats.is_healthy = True
    try:
        from datetime import datetime, timezone

        _stats.last_run_at = datetime.now(timezone.utc).isoformat()
    except Exception:
        pass
    # also cache last run for observability endpoint
    cache_set("worker:last_run", _stats.__dict__, ttl=600)


def record_failure():
    _stats.jobs_failed += 1
    _stats.is_healthy = False


def run_once(job: Callable[[], int], job_name: str = "worker_job") -> int:
    """Execute a job callable, capturing telemetry."""
    start = time.perf_counter()
    try:
        count = job()
        duration_ms = (time.perf_counter() - start) * 1000
        record_success(duration_ms)
        # push metric if observability available
        try:
            from backend.app.core.observability import WORKER_JOBS_PROCESSED

            WORKER_JOBS_PROCESSED.inc(count)
            from backend.app.core.observability import WORKER_DURATION

            WORKER_DURATION.observe(duration_ms / 1000)
        except Exception:
            pass
        logger.info(f"[{job_name}] processed {count} items in {duration_ms:.1f}ms")
        return count
    except Exception as exc:
        record_failure()
        logger.exception(f"[{job_name}] failed: {exc}")
        return 0
