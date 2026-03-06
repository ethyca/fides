from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.utils import get_registered_index_keys
from fides.api.migrations.post_upgrade_index_creation import (
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
    """Tests that check_and_create_objects skips entries whose migration_key is not registered."""

    @patch("fides.api.migrations.post_upgrade_index_creation.get_registered_index_keys")
    @patch("fides.api.migrations.post_upgrade_index_creation.check_object_exists")
    @patch("fides.api.migrations.post_upgrade_index_creation.create_object")
    def test_skips_entry_when_migration_key_not_registered(
        self, mock_create_object, mock_check_object_exists, mock_get_registered_keys
    ):
        """Entry with unregistered migration_key is skipped entirely."""
        mock_get_registered_keys.return_value = set()
        mock_lock = MagicMock()

        table_map = {
            "test_table": [
                {
                    "name": "ix_test_index",
                    "statement": "CREATE INDEX CONCURRENTLY ix_test_index ON test_table (col)",
                    "type": "index",
                    "migration_key": "ix_test_index",
                }
            ]
        }

        result = check_and_create_objects(MagicMock(), table_map, mock_lock)

        mock_check_object_exists.assert_not_called()
        mock_create_object.assert_not_called()
        assert result == {}

    @patch("fides.api.migrations.post_upgrade_index_creation.get_registered_index_keys")
    @patch("fides.api.migrations.post_upgrade_index_creation.check_object_exists")
    @patch("fides.api.migrations.post_upgrade_index_creation.create_object")
    def test_processes_entry_when_migration_key_is_registered(
        self, mock_create_object, mock_check_object_exists, mock_get_registered_keys
    ):
        """Entry with registered migration_key is processed normally."""
        mock_get_registered_keys.return_value = {"ix_test_index"}
        mock_check_object_exists.return_value = False  # index doesn't exist yet
        mock_lock = MagicMock()

        table_map = {
            "test_table": [
                {
                    "name": "ix_test_index",
                    "statement": "CREATE INDEX CONCURRENTLY ix_test_index ON test_table (col)",
                    "type": "index",
                    "migration_key": "ix_test_index",
                }
            ]
        }

        result = check_and_create_objects(MagicMock(), table_map, mock_lock)

        mock_check_object_exists.assert_called_once()
        mock_create_object.assert_called_once()
        assert result == {"ix_test_index": "created"}

    @patch("fides.api.migrations.post_upgrade_index_creation.get_registered_index_keys")
    def test_raises_on_entry_without_migration_key(self, mock_get_registered_keys):
        """Entry with no migration_key raises ValueError."""
        mock_get_registered_keys.return_value = set()
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
            check_and_create_objects(MagicMock(), table_map, mock_lock)


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
        """Verify get_registered_index_keys() returns only index-type keys."""
        test_key = "test-index-key-for-get-registered"

        # Initially not present
        keys = get_registered_index_keys(db)
        assert test_key not in keys

        # Insert as index type
        db.execute(
            text(
                "INSERT INTO post_upgrade_background_migration_tasks (key, task_type) "
                "VALUES (:key, 'index')"
            ),
            {"key": test_key},
        )
        db.commit()

        keys = get_registered_index_keys(db)
        assert test_key in keys

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
