# Privacy package — the single choke point before any LLM-bound data.
from backend.app.privacy.gateway import PrivacyBlockedError, PrivacyGateway

__all__ = ["PrivacyBlockedError", "PrivacyGateway"]
