from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.utils import get_registered_index_keys
from fides.api.migrations.post_upgrade_index_creation import (
    TABLE_OBJECT_MAP,
    check_and_create_objects,
    post_upgrade_index_creation_task,
)


class TestPostUpgradeIndexCreation:
    @patch("fides.api.migrations.post_upgrade_index_creation.redis_lock")
    @patch("fides.api.migrations.post_upgrade_index_creation.check_and_create_objects")
    def test_post_upgrade_index_creation_task_lock_not_acquired(
        self, mock_check_and_create_objects, mock_redis_lock
    ):
        """
        Tests that if the redis lock is not acquired, the index creation logic is not run.
        """
        # Simulate lock not being acquired
        mock_redis_lock.return_value.__enter__.return_value = None

        post_upgrade_index_creation_task()

        mock_check_and_create_objects.assert_not_called()

    @patch("fides.api.migrations.post_upgrade_index_creation.get_db_session")
    @patch("fides.api.migrations.post_upgrade_index_creation.redis_lock")
    @patch("fides.api.migrations.post_upgrade_index_creation.check_and_create_objects")
    def test_post_upgrade_index_creation_task_lock_acquired(
        self, mock_check_and_create_objects, mock_redis_lock, mock_get_db_session
    ):
        """
        Tests that if the redis lock is acquired, the index creation logic is run.
        """
        # Simulate lock being acquired
        mock_lock = MagicMock()
        mock_redis_lock.return_value.__enter__.return_value = mock_lock

        # Mock database session
        mock_db_session = MagicMock()
        mock_get_db_session.return_value.return_value = mock_db_session

        mock_check_and_create_objects.return_value = {"test_index": "created"}

        post_upgrade_index_creation_task()

        mock_check_and_create_objects.assert_called_once()


class TestCheckAndCreateObjectsMigrationKeyFiltering:
    """Tests that check_and_create_objects respects migration_key registration."""

    TABLE_MAP = {
        "test_table": [
            {
                "name": "ix_test_index",
                "statement": "CREATE INDEX CONCURRENTLY ix_test_index ON test_table (col)",
                "type": "index",
                "migration_key": "ix_test_index",
            }
        ]
    }

    @pytest.fixture(autouse=True)
    def clean_migration_tasks(self, db: Session):
        db.execute(
            text(
                "DELETE FROM post_upgrade_background_migration_tasks "
                "WHERE key LIKE 'test-%' OR key = 'ix_test_index'"
            )
        )
        db.commit()
        yield
        db.execute(
            text(
                "DELETE FROM post_upgrade_background_migration_tasks "
                "WHERE key LIKE 'test-%' OR key = 'ix_test_index'"
            )
        )
        db.commit()

    @patch("fides.api.migrations.post_upgrade_index_creation.create_object")
    def test_skips_entry_when_migration_key_not_registered(
        self, mock_create_object, db: Session
    ):
        """Entry with unregistered migration_key is skipped entirely."""
        mock_lock = MagicMock()

        result = check_and_create_objects(db, self.TABLE_MAP, mock_lock)

        mock_create_object.assert_not_called()
        assert result == {}

    @patch("fides.api.migrations.post_upgrade_index_creation.create_object")
    def test_processes_entry_when_migration_key_is_registered(
        self, mock_create_object, db: Session
    ):
        """Entry with registered migration_key is processed and marked completed."""
        # Register the migration key
        db.execute(
            text(
                "INSERT INTO post_upgrade_background_migration_tasks (key, task_type) "
                "VALUES ('ix_test_index', 'index')"
            )
        )
        db.commit()

        mock_lock = MagicMock()

        result = check_and_create_objects(db, self.TABLE_MAP, mock_lock)

        mock_create_object.assert_called_once()
        assert result == {"ix_test_index": "created"}

        # Verify completed_at was set
        row = db.execute(
            text(
                "SELECT completed_at FROM post_upgrade_background_migration_tasks "
                "WHERE key = 'ix_test_index' AND task_type = 'index'"
            )
        ).first()
        assert row[0] is not None

    def test_raises_on_entry_without_migration_key(self, db: Session):
        """Entry with no migration_key raises ValueError."""
        mock_lock = MagicMock()

        table_map = {
            "test_table": [
                {
                    "name": "ix_legacy_index",
                    "statement": "CREATE INDEX CONCURRENTLY ix_legacy_index ON test_table (col)",
                    "type": "index",
                    # no migration_key
                }
            ]
        }

        with pytest.raises(ValueError, match="missing a migration_key"):
            check_and_create_objects(db, table_map, mock_lock)


class TestRegisteredIndexKeys:
    """Tests for index key registration functions."""

    @pytest.fixture(autouse=True)
    def clean_migration_tasks(self, db: Session):
        db.execute(
            text(
                "DELETE FROM post_upgrade_background_migration_tasks "
                "WHERE key LIKE 'test-%'"
            )
        )
        db.commit()
        yield
        db.execute(
            text(
                "DELETE FROM post_upgrade_background_migration_tasks "
                "WHERE key LIKE 'test-%'"
            )
        )
        db.commit()

    def test_get_registered_index_keys(self, db: Session):
        """Verify get_registered_index_keys() returns index keys with completion status."""
        test_key = "test-index-key-for-get-registered"

        # Initially not present
        keys = get_registered_index_keys(db)
        assert test_key not in keys

        # Insert as index type with NULL completed_at (pending)
        db.execute(
            text(
                "INSERT INTO post_upgrade_background_migration_tasks (key, task_type) "
                "VALUES (:key, 'index')"
            ),
            {"key": test_key},
        )
        # Insert an already-completed index key
        completed_key = "test-index-key-already-completed"
        db.execute(
            text(
                "INSERT INTO post_upgrade_background_migration_tasks (key, task_type, completed_at) "
                "VALUES (:key, 'index', now())"
            ),
            {"key": completed_key},
        )
        db.commit()

        keys = get_registered_index_keys(db)
        assert test_key in keys
        assert keys[test_key]["completed_at"] is None
        assert completed_key in keys
        assert keys[completed_key]["completed_at"] is not None

        # Mark the pending one completed
        db.execute(
            text(
                "UPDATE post_upgrade_background_migration_tasks "
                "SET completed_at = now() "
                "WHERE key = :key AND task_type = 'index'"
            ),
            {"key": test_key},
        )
        db.commit()

        keys = get_registered_index_keys(db)
        assert test_key in keys
        assert keys[test_key]["completed_at"] is not None

        # A backfill-type row should NOT appear in index keys
        backfill_key = "test-backfill-key-for-get-registered"
        db.execute(
            text(
                "INSERT INTO post_upgrade_background_migration_tasks (key, task_type) "
                "VALUES (:key, 'backfill')"
            ),
            {"key": backfill_key},
        )
        db.commit()

        keys = get_registered_index_keys(db)
        assert backfill_key not in keys


class TestDeferredDuplicateRequestGroupIdIndex:
    """End-to-end test for the deferred branch of
    xx_2026_04_20_1200_e8f9a0b1c2d3_recreate_ix_privacyrequest_duplicate_request_group_id.py.

    The other tests in this module mock `create_object` because they use a
    fake table. This one uses the real `privacyrequest` table so the actual
    `CREATE INDEX CONCURRENTLY` statement is executed, catching typos or
    column-name drift in our `TABLE_OBJECT_MAP` entry."""

    INDEX_NAME = "ix_privacyrequest_duplicate_request_group_id"

    @pytest.fixture(autouse=True)
    def clean_index_and_registration(self, db: Session):
        def cleanup():
            # Drop with IF EXISTS via AUTOCOMMIT — CONCURRENTLY-created indexes
            # can't be dropped inside a transaction either.
            with db.bind.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as conn:
                conn.execute(text(f"DROP INDEX IF EXISTS {self.INDEX_NAME}"))
            db.execute(
                text(
                    "DELETE FROM post_upgrade_background_migration_tasks "
                    "WHERE key = :key AND task_type = 'index'"
                ),
                {"key": self.INDEX_NAME},
            )
            db.commit()

        cleanup()
        yield
        cleanup()

    def test_creates_index_from_real_table_object_map_entry(self, db: Session):
        db.execute(
            text(
                "INSERT INTO post_upgrade_background_migration_tasks (key, task_type) "
                "VALUES (:key, 'index')"
            ),
            {"key": self.INDEX_NAME},
        )
        db.commit()

        check_and_create_objects(db, TABLE_OBJECT_MAP, MagicMock())

        index_exists = db.execute(
            text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
            {"name": self.INDEX_NAME},
        ).scalar()
        assert index_exists == 1
