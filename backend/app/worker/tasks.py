"""Background tasks – processed via Celery if available, else via asyncio loop.

Tasks must be idempotent and not modify raw events beyond status.
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("codesense.worker.tasks")

# Import celery_app lazily to avoid circular when celery not installed
try:
    from backend.app.worker.celery_app import celery_app

    has_celery = celery_app is not None
except Exception:  # noqa: BLE001
    celery_app = None  # type: ignore
    has_celery = False


def _get_task_decorator():
    """Return celery task decorator if available, else a no-op."""
    if has_celery:
        return celery_app.task  # type: ignore[union-attr]
    # no-op decorator that preserves function and adds .delay for fallback

    def decorator(*dargs, **dkwargs):  # type: ignore[no-untyped-def]
        def wrapper(func):  # type: ignore[no-untyped-def]
            # add dummy .delay that executes inline (or via queue)
            def delay(*a, **kw):  # type: ignore[no-untyped-def]
                try:
                    # enqueue for later execution via queue abstraction

                    # avoid infinite recursion: call function directly via fallback
                    # if we are already in fallback path, execute inline
                    result = func(*a, **kw)
                    class _Res:
                        id = "fallback-inline"

                    return _Res()
                except Exception as exc:
                    logger.error(f"Fallback task inline execution failed: {exc}")
                    raise

            func.delay = delay  # type: ignore[attr-defined]
            func.name = f"backend.app.worker.tasks.{func.__name__}"  # type: ignore[attr-defined]
            return func

        # handle @task vs @task()
        if len(dargs) == 1 and callable(dargs[0]) and not dkwargs:
            return wrapper(dargs[0])
        return wrapper

    return decorator


task = _get_task_decorator()


@task(bind=True, max_retries=2, name="process_pending_events")  # type: ignore[misc]
def process_pending_events(self, limit: int = 50):  # type: ignore[no-untyped-def]
    """Celery task: normalize pending raw events."""
    try:
        from backend.app.core.database import SessionLocal
        from backend.app.services.processing import EventProcessor

        db = SessionLocal()
        try:
            processor = EventProcessor(db)
            count = processor.process_pending_events(limit=limit)
            logger.info(f"[worker] processed {count} pending events")
            return {"processed": count}
        finally:
            db.close()
    except Exception as exc:
        logger.exception(f"process_pending_events failed: {exc}")
        # Retry via Celery if available
        if has_celery and hasattr(self, "retry"):
            raise self.retry(exc=exc, countdown=5)  # type: ignore[union-attr]
        raise


@task(name="ping")  # type: ignore[misc]
def ping(x: int = 0):  # type: ignore[no-untyped-def]
    """Simple test task for Phase 2 verification."""
    logger.info(f"ping task executed x={x}")
    return {"pong": x, "status": "ok"}


@task(name="cache_warmup")  # type: ignore[misc]
def cache_warmup(key: str, value: Any):  # type: ignore[no-untyped-def]
    """Warm up cache via worker."""
    from backend.app.core.cache import cache_set

    cache_set(key, value)
    logger.info(f"cache warmup key={key}")
    return {"key": key}


@task(name="telemetry_heartbeat")  # type: ignore[misc]
def telemetry_heartbeat():  # type: ignore[no-untyped-def]
    """Emit worker heartbeat metric."""
    try:
        from backend.app.core.observability import WORKER_HEARTBEAT  # type: ignore

        WORKER_HEARTBEAT.inc()
    except Exception:
        pass
    logger.debug("worker heartbeat")
    return {"heartbeat": datetime.now(timezone.utc).isoformat()}


@task(name="extract_ml_features")  # type: ignore[misc]
def extract_ml_features(days_back: int = 7):  # type: ignore[no-untyped-def]
    """Extract ML features for the given past days."""
    try:
        from datetime import datetime, timedelta, timezone

        from backend.app.core.database import SessionLocal
        from backend.app.ml.features.pipeline import FeatureExtractor

        db = SessionLocal()
        try:
            extractor = FeatureExtractor(db)
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days_back)
            
            count = extractor.run_extraction_for_period(start, end)
            logger.info(f"[worker] extracted ML features for {count} teams")
            return {"extracted": count}
        finally:
            db.close()
    except Exception as exc:
        logger.exception(f"extract_ml_features failed: {exc}")
        raise
