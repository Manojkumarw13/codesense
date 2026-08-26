"""Cache abstraction over Redis with in-memory fallback.

MVP: DB is sufficient; Redis is an optimization.
Must not break when Redis is down (offline mode).
"""
import json
import logging
import time
from typing import Any

from backend.app.core.redis import get_redis_client
from backend.app.core.settings import settings

logger = logging.getLogger("codesense.cache")

# In-memory fallback store: key -> (value_json, expires_at)
_memory_store: dict[str, tuple[str, float | None]] = {}


def _serialize(value: Any) -> str:
    try:
        return json.dumps(value, default=str)
    except Exception:
        return json.dumps(str(value))


def _deserialize(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return raw


def cache_get(key: str) -> Any | None:
    client = get_redis_client()
    if client is not None:
        try:
            raw = client.get(key)  # type: ignore[union-attr]
            if raw is None:
                return None
            return _deserialize(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"cache_get redis error {exc}; fallback to memory")
    # memory fallback
    entry = _memory_store.get(key)
    if entry is None:
        return None
    val, expires_at = entry
    if expires_at is not None and time.time() > expires_at:
        _memory_store.pop(key, None)
        return None
    return _deserialize(val)


def cache_set(key: str, value: Any, ttl: int | None = None) -> bool:
    ttl = ttl if ttl is not None else settings.CACHE_TTL_SECONDS
    payload = _serialize(value)
    client = get_redis_client()
    if client is not None:
        try:
            client.setex(key, ttl, payload)  # type: ignore[union-attr]
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"cache_set redis error {exc}; fallback to memory")
    expires_at = time.time() + ttl if ttl else None
    _memory_store[key] = (payload, expires_at)
    return True


def cache_delete(key: str) -> bool:
    client = get_redis_client()
    if client is not None:
        try:
            client.delete(key)  # type: ignore[union-attr]
        except Exception:
            pass
    _memory_store.pop(key, None)
    return True


def cache_flush() -> None:
    """Flush in-memory fallback (and attempt redis flush for tests)."""
    _memory_store.clear()
    client = get_redis_client()
    if client is not None:
        try:
            client.flushdb()  # type: ignore[union-attr]
        except Exception:
            pass


def cache_invalidate_pattern(pattern: str) -> int:
    """Invalidate keys matching pattern. Works for memory; best-effort for redis."""
    import fnmatch

    count = 0
    # memory
    for k in list(_memory_store.keys()):
        if fnmatch.fnmatch(k, pattern):
            _memory_store.pop(k, None)
            count += 1
    client = get_redis_client()
    if client is not None:
        try:
            for k in client.scan_iter(match=pattern):  # type: ignore[union-attr]
                client.delete(k)  # type: ignore[union-attr]
                count += 1
        except Exception:
            pass
    return count
