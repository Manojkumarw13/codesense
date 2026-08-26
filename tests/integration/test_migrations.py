from alembic import command
from alembic.config import Config
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.core.settings import settings


def test_migration_upgrade_and_downgrade():
    """Verify that Alembic can perform a full downgrade to base and upgrade back to head."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

    # Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Verify no tables in custom schemas
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('raw', 'core', 'analytics', 'configuration', 'audit')")
        )
        count = result.scalar()
        assert count == 0

    # Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Verify all 34 tables are restored
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('raw', 'core', 'analytics', 'configuration', 'audit')")
        )
        count = result.scalar()
        assert count == 34
