"""Internet availability detection — Phase 20.

Offline is a state of the *cloud AI dependency*, not of the core system:
metrics, health score and historical analytics never consult this module.
The probe is injectable so tests never touch the public internet.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import Enum

from backend.app.core.settings import settings

logger = logging.getLogger("codesense.connectivity")


class InternetState(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


_cache: dict[str, object] = {"state": InternetState.UNKNOWN, "checked_at": 0.0}


def reset_connectivity_cache() -> None:
    """Clear the cached internet state (tests, forced re-checks)."""
    _cache["state"] = InternetState.UNKNOWN
    _cache["checked_at"] = 0.0


def probe_internet(url: str | None = None, timeout: float | None = None) -> bool:
    """Return True when the probe URL is reachable. Never raises."""
    target = url or settings.OFFLINE_PROBE_URL
    limit = timeout if timeout is not None else settings.OFFLINE_PROBE_TIMEOUT_SECONDS
    try:
        import httpx

        with httpx.Client(timeout=limit, follow_redirects=True) as client:
            response = client.get(target)
        return response.status_code < 500
    except Exception as exc:  # noqa: BLE001 - offline detection must never raise
        logger.debug("Internet probe failed: %s", exc)
        return False


def get_internet_state(
    probe: Callable[[], bool] | None = None, force: bool = False
) -> InternetState:
    """Cached internet state. `probe` overrides the network call."""
    now = time.monotonic()
    checked_at = float(_cache["checked_at"])  # type: ignore[arg-type]
    cached = _cache["state"]
    if (
        not force
        and cached is not InternetState.UNKNOWN
        and (now - checked_at) < settings.OFFLINE_PROBE_INTERVAL_SECONDS
    ):
        return cached  # type: ignore[return-value]
    result = bool(probe() if probe is not None else probe_internet())
    state = InternetState.ONLINE if result else InternetState.OFFLINE
    _cache["state"] = state
    _cache["checked_at"] = now
    return state
