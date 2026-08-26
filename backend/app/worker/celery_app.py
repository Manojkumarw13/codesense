"""Celery application configuration.

 broker = Redis (or in-memory fallback)
 result backend = Redis

Importing this module should NOT fail when celery/redis not installed or not reachable.
Tasks should still be importable for unit tests.
"""
import logging

from backend.app.core.settings import settings

logger = logging.getLogger("codesense.worker")

try:
    from celery import Celery  # type: ignore

    celery_app = Celery(
        "codesense",
        broker=settings.CELERY_BROKER_URI,
        backend=settings.CELERY_BACKEND_URI,
        include=["backend.app.worker.tasks"],
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        broker_connection_retry_on_startup=True,
    )
    # Auto-discover tasks
    celery_app.autodiscover_tasks(["backend.app.worker"])
    logger.info(f"Celery configured broker={settings.CELERY_BROKER_URI}")
except Exception as exc:  # noqa: BLE001
    logger.warning(f"Celery not available ({exc}); worker will use asyncio fallback")
    celery_app = None  # type: ignore[assignment]
