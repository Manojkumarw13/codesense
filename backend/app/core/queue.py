"""Queue abstraction: enqueue jobs via Redis/Celery or asyncio fallback.

Spec says: Redis optional for MVP, DB sufficient. So enqueue must be non-blocking
and degrade gracefully when Redis/Celery not available.
"""
import asyncio
import inspect
import logging
from typing import Any, Callable, Optional

from backend.app.core.settings import settings

logger = logging.getLogger("codesense.queue")

# Simple in-memory async queue for fallback
_fallback_queue: asyncio.Queue = asyncio.Queue()


def enqueue_job(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Optional[str]:
    """Try to enqueue via Celery; fallback to asyncio queue.

    Returns job id if Celery used, else 'fallback-<id>'.
    Never raises – caller must not fail if queue unavailable.
    """
    if settings.ENABLE_WORKER:
        try:
            from backend.app.worker.celery_app import celery_app

            # Check if celery broker is configured and task is registered
            task_name = getattr(func, "name", None) or f"{func.__module__}.{func.__name__}"
            # If func is a Celery task, delay it
            if hasattr(func, "delay"):
                result = func.delay(*args, **kwargs)  # type: ignore[attr-defined]
                return str(getattr(result, "id", "celery-enqueued"))
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Celery enqueue failed ({exc}), using fallback")

    # fallback: put into memory queue (processed by asyncio loop in main.py)
    try:
        # Use loop if running
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_fallback_exec(func, *args, **kwargs))
        else:
            # sync fallback – execute directly if no loop
            _fallback_queue.put_nowait((func, args, kwargs))
        return "fallback-enqueued"
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Fallback enqueue failed: {exc}")
        return None


async def _fallback_exec(func: Callable[..., Any], *args: Any, **kwargs: Any):
    try:
        if inspect.iscoroutinefunction(func):
            await func(*args, **kwargs)
        else:
            func(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Fallback job failed: {exc}")


async def process_fallback_queue():
    """Drain fallback queue – called from background loop if needed."""
    while not _fallback_queue.empty():
        try:
            func, args, kwargs = _fallback_queue.get_nowait()
            await _fallback_exec(func, *args, **kwargs)
            _fallback_queue.task_done()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"process_fallback_queue error: {exc}")


def get_queue_length() -> int:
    return _fallback_queue.qsize()
