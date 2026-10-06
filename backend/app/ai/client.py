"""OpenRouter-compatible LLM client — Phase 19.

Optional leaf dependency: any failure (missing key, timeout, HTTP error)
is surfaced as LlmUnavailableError so the explainer can fall back to
deterministic rules. Core analytics never depend on this module.
"""
import logging

import requests

from backend.app.core.settings import settings

logger = logging.getLogger("codesense.ai")

DEFAULT_TIMEOUT_SECONDS = 20


class LlmUnavailableError(RuntimeError):
    """The LLM could not produce a completion (down, slow, or misconfigured)."""


def _endpoint() -> str:
    base = (settings.AI_GATEWAY_URL or "https://openrouter.ai/api/v1").rstrip("/")
    return f"{base}/chat/completions"


def complete(prompt: str, *, system: str | None = None) -> tuple[str, str]:
    """Return (text, model). Raises LlmUnavailableError on any failure."""
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise LlmUnavailableError("LLM not configured (OPENROUTER_API_KEY unset)")
    model = settings.LLM_MODEL or "google/antigravity-gemini-3.5-flash"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = requests.post(
            _endpoint(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise LlmUnavailableError(f"LLM request failed: {exc}") from exc
    if resp.status_code != 200:
        raise LlmUnavailableError(f"LLM returned HTTP {resp.status_code}")
    try:
        text = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise LlmUnavailableError("LLM returned an unreadable response") from exc
    logger.info("LLM completion ok (model=%s)", model)
    return str(text), model
