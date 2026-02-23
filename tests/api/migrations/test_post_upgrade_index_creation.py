from unittest.mock import MagicMock, patch

import pytest

from fides.api.migrations.post_upgrade_index_creation import (
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

        post_upgrade_index_creation_task()

        mock_check_and_create_objects.assert_called_once()
        # Check that reacquire was called
        mock_lock.reacquire.assert_called()
