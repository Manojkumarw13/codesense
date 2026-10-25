"""Per-test database isolation for integration tests.

``tests/integration/test_auth_api.py`` seeds fixed data (the ``DEVELOPER``
role and ``alice@example.com`` user) without cleanup, so it cannot run twice
against a shared database: the second seed hits a unique constraint. Truncate
the small set of core tables it touches before every integration test so each
test starts from a clean slate. Every other integration test seeds its own
data and does not depend on rows persisting across tests, so this is safe
project-wide.
"""

import pytest
from sqlalchemy import text

from backend.app.core.database import SessionLocal

_TABLES = (
    "core.user_roles",
    "core.team_members",
    "core.users",
    "core.teams",
    "core.organizations",
    "core.roles",
)


def _truncate_core_tables() -> None:
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE " + ", ".join(_TABLES) + " CASCADE"))
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_core_tables() -> None:
    """Give every integration test a clean set of core tables."""
    _truncate_core_tables()
