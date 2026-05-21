# pylint: disable=protected-access

from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from fides.api.tasks import NEW_SESSION_RETRIES, DatabaseTask
from fides.config import CONFIG


class TestDatabaseTask:
    @pytest.fixture
    def mock_config_changed_db_engine_settings(self):
        pool_size = CONFIG.database.task_engine_pool_size
        CONFIG.database.task_engine_pool_size = pool_size + 5
        max_overflow = CONFIG.database.task_engine_max_overflow
        CONFIG.database.task_engine_max_overflow = max_overflow + 5
        pool_recycle = CONFIG.database.pool_recycle
        CONFIG.database.pool_recycle = 1800
        yield
        CONFIG.database.task_engine_pool_size = pool_size
        CONFIG.database.task_engine_max_overflow = max_overflow
        CONFIG.database.pool_recycle = pool_recycle

    @pytest.fixture
    def recovering_session_maker(self):
        """Fixture that fails twice then succeeds"""
        mock_session = mock.Mock()
        mock_maker = mock.Mock()
        mock_maker.side_effect = [
            OperationalError("connection failed", None, None),
            OperationalError("connection failed", None, None),
            mock_session,
        ]
        return mock_maker, mock_session

    @pytest.fixture
    def always_failing_session_maker(self):
        """Fixture that always fails with OperationalError"""
        mock_maker = mock.Mock()
        mock_maker.side_effect = OperationalError("connection failed", None, None)
        return mock_maker

    @pytest.mark.usefixtures("mock_config_changed_db_engine_settings")
    def test_task_engine_pool_recycle(self):
        """pool_recycle from config is applied to the task engine."""
        task = DatabaseTask()
        task._task_engine = None
        task._sessionmaker = None
        task.get_new_session()
        assert task._task_engine.pool._recycle == CONFIG.database.pool_recycle

    def test_retry_on_operational_error(self, recovering_session_maker):
        """Test that session creation retries on OperationalError"""

        mock_maker, mock_session = recovering_session_maker

        task = DatabaseTask()
        with mock.patch.object(task, "_sessionmaker", mock_maker):
            session = task.get_new_session()
            assert session == mock_session
            assert mock_maker.call_count == 3

    def test_max_retries_exceeded(mock_db_task, always_failing_session_maker):
        """Test that retries stop after max attempts"""
        task = DatabaseTask()
        with mock.patch.object(task, "_sessionmaker", always_failing_session_maker):
            with pytest.raises(OperationalError):
                with task.get_new_session():
                    pass
            assert always_failing_session_maker.call_count == NEW_SESSION_RETRIES


class TestDatabaseTaskOnFailure:
    """Tests for the on_failure handler that logs worker-level task deaths."""

    def test_on_failure_skips_non_privacy_request_tasks(self):
        """Tasks without privacy_request_id in kwargs are ignored."""
        task = DatabaseTask()
        task.on_failure(
            exc=RuntimeError("boom"),
            task_id="test-task-id",
            args=(),
            kwargs={"some_other_param": "value"},
            einfo=None,
        )
        # No exception raised, no DB interaction

    @patch.object(DatabaseTask, "get_new_session")
    def test_on_failure_creates_error_log_for_worker_death(self, mock_get_session):
        """When a privacy request task dies at the worker level, an error
        execution log is created and the request is marked as errored."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_privacy_request = MagicMock()
        mock_privacy_request.status = MagicMock()
        mock_privacy_request.status.__eq__ = lambda self, other: False  # not already errored
        mock_privacy_request.policy.get_action_type.return_value = "access"

        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_privacy_request
        )

        task = DatabaseTask()
        task.on_failure(
            exc=RuntimeError("Worker killed by OOM"),
            task_id="test-task-id",
            args=(),
            kwargs={"privacy_request_id": "test-pr-id"},
            einfo=None,
        )

        mock_privacy_request.add_error_execution_log.assert_called_once()
        call_kwargs = mock_privacy_request.add_error_execution_log.call_args
        assert "Worker killed by OOM" in call_kwargs[1]["message"] or "Worker killed by OOM" in str(call_kwargs)
        assert call_kwargs[1]["dataset_name"] == "Worker task failure"

        mock_privacy_request.error_processing.assert_called_once_with(db=mock_session)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch.object(DatabaseTask, "get_new_session")
    def test_on_failure_skips_already_errored_request(self, mock_get_session):
        """If the in-task exception handler already handled the error, on_failure is a no-op."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Simulate PrivacyRequestStatus.error comparison
        from fides.api.schemas.privacy_request import PrivacyRequestStatus

        mock_privacy_request = MagicMock()
        mock_privacy_request.status = PrivacyRequestStatus.error

        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_privacy_request
        )

        task = DatabaseTask()
        task.on_failure(
            exc=RuntimeError("boom"),
            task_id="test-task-id",
            args=(),
            kwargs={"privacy_request_id": "test-pr-id"},
            einfo=None,
        )

        mock_privacy_request.add_error_execution_log.assert_not_called()
        mock_privacy_request.error_processing.assert_not_called()
        mock_session.close.assert_called_once()

    @patch.object(DatabaseTask, "get_new_session")
    def test_on_failure_handles_db_errors_gracefully(self, mock_get_session):
        """If the DB is unavailable during on_failure, the error is logged but not raised."""
        mock_get_session.side_effect = OperationalError("DB down", None, None)

        task = DatabaseTask()
        # Should not raise
        task.on_failure(
            exc=RuntimeError("original error"),
            task_id="test-task-id",
            args=(),
            kwargs={"privacy_request_id": "test-pr-id"},
            einfo=None,
        )
