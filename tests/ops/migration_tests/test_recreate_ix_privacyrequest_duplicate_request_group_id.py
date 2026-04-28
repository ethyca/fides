"""Upgrade/downgrade cycle test for the migration that recreates
`ix_privacyrequest_duplicate_request_group_id`.

Complements the unit test in
tests/api/migrations/test_post_upgrade_index_creation.py that covers the
deferred `CREATE INDEX CONCURRENTLY` path. This one exercises the inline
branch of the migration itself: confirms the index drops cleanly on
downgrade and is recreated on a subsequent upgrade (idempotency).
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.db.database import downgrade_db, get_alembic_config, upgrade_db
from fides.config import CONFIG

REVISION = "e8f9a0b1c2d3"
DOWN_REVISION = "d71c7d274c04"
INDEX_NAME = "ix_privacyrequest_duplicate_request_group_id"


def _index_exists(db: Session) -> bool:
    return (
        db.execute(
            text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
            {"name": INDEX_NAME},
        ).scalar()
        == 1
    )


class TestRecreateDuplicateRequestGroupIdIndexMigration:
    @pytest.fixture(scope="function")
    def alembic_config(self):
        return get_alembic_config(CONFIG.database.sqlalchemy_test_database_uri)

    @pytest.fixture(autouse=True)
    def restore_head(self, db: Session, alembic_config):
        """Guarantee the DB is back at head after the test — even if it fails —
        so downstream tests in the session aren't left on a downgraded schema."""
        yield
        upgrade_db(alembic_config, "head")
        db.execute(
            text(
                "DELETE FROM post_upgrade_background_migration_tasks "
                "WHERE key = :key AND task_type = 'index'"
            ),
            {"key": INDEX_NAME},
        )
        db.commit()

    def test_downgrade_drops_index_and_upgrade_recreates_it(
        self, db: Session, alembic_config
    ):
        # Downgrade: index (and the registration row, if this were the deferred
        # branch) must go away. The downgrade uses `DROP INDEX IF EXISTS` so
        # this is tolerant of test DBs created via create_all+stamp.
        downgrade_db(alembic_config, DOWN_REVISION)
        db.commit()
        assert not _index_exists(db)
        assert (
            db.execute(
                text(
                    "SELECT 1 FROM post_upgrade_background_migration_tasks "
                    "WHERE key = :key AND task_type = 'index'"
                ),
                {"key": INDEX_NAME},
            ).scalar()
            is None
        )

        # Upgrade: the inline branch runs `op.create_index(...)` (no
        # IF NOT EXISTS) — if `downgrade()` didn't fully clean up, this would
        # fail with "relation already exists".
        upgrade_db(alembic_config, REVISION)
        db.commit()
        assert _index_exists(db)
