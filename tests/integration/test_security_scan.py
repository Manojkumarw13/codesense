# tests/integration/test_security_scan.py
import os


def test_no_hardcoded_secret_defaults():
    # settings must not ship with insecure defaults in production mode
    from backend.app.core.settings import settings

    assert settings.SECRET_KEY != "changeme"
    assert settings.SECRET_KEY != "supersecretkeyreplaceinproduction"
