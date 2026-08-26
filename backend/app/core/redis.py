import logging
from typing import Optional

from backend.app.core.settings import settings

logger = logging.getLogger("codesense.redis")

_client: Optional[object] = None
_available: Optional[bool] = None


def get_redis_client():
    """Return a Redis client if available, else None.

    Lazy connection; respects ENABLE_REDIS flag.
    Falls back gracefully when redis server unreachable.
    """
    global _client, _available

    if not settings.ENABLE_REDIS:
        logger.debug("Redis disabled via ENABLE_REDIS=false")
        return None

    if _client is not None and _available is True:
        return _client

    try:
        import redis  # type: ignore

        client = redis.Redis.from_url(
            settings.REDIS_URI,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        # probe connection
        client.ping()
        _client = client
        _available = True
        logger.info(f"Redis connected at {settings.REDIS_URI}")
        return _client
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Redis unavailable ({exc}); using in-memory fallback")
        _client = None
        _available = False
        return None


def is_redis_available() -> bool:
    """Check if Redis is reachable."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.ping()  # type: ignore[union-attr]
        return True
    except Exception:
        return False


def reset_redis_client() -> None:
    """Reset cached client (useful for tests)."""
    global _client, _available
    _client = None
    _available = None
