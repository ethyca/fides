# pylint: disable=protected-access

from unittest import mock

import pytest
from celery import Task
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from fides.api.tasks import (
    DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
    DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
    NEW_SESSION_RETRIES,
    DatabaseTask,
)
from fides.config import CONFIG


class TestDatabaseTask:
    @pytest.fixture
    def mock_config_changed_db_engine_settings(self):
        pool_size = CONFIG.database.task_engine_pool_size
        CONFIG.database.task_engine_pool_size = pool_size + 5
        max_overflow = CONFIG.database.task_engine_max_overflow
        CONFIG.database.task_engine_max_overflow = max_overflow + 5
        yield
        CONFIG.database.task_engine_pool_size = pool_size
        CONFIG.database.task_engine_max_overflow = max_overflow

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


class TestDatabaseTaskApplyAsync:
    """Tests for DatabaseTask.apply_async per-queue eager routing."""

    @pytest.fixture(autouse=True)
    def reset_eager_queues(self):
        """Ensure eager_task_queues is empty and task_always_eager is False by default."""
        original_eager_queues = CONFIG.celery.eager_task_queues
        original_always_eager = CONFIG.celery.task_always_eager
        CONFIG.celery.eager_task_queues = set()
        CONFIG.celery.task_always_eager = False
        yield
        CONFIG.celery.eager_task_queues = original_eager_queues
        CONFIG.celery.task_always_eager = original_always_eager

    def _make_task(self, task_queue=None):
        task = DatabaseTask()
        if task_queue is not None:
            task.queue = task_queue
        elif not hasattr(task, "queue"):
            task.queue = None
        return task

    def test_dispatches_via_super_when_no_eager_config(self):
        """With no eager queues and task_always_eager=False, super().apply_async is called."""
        task = self._make_task()
        with mock.patch.object(
            Task, "apply_async", return_value="dispatched"
        ) as mock_super:
            result = task.apply_async(args=("arg1",), queue="some.queue")
        mock_super.assert_called_once_with(("arg1",), None, queue="some.queue")
        assert result == "dispatched"

    def test_always_eager_true_calls_apply(self):
        """task_always_eager=True runs task synchronously via apply()."""
        CONFIG.celery.task_always_eager = True
        task = self._make_task()
        with mock.patch.object(
            task, "apply", return_value="eager_result"
        ) as mock_apply:
            with mock.patch.object(Task, "apply_async") as mock_super:
                result = task.apply_async(
                    args=("a",), kwargs={"k": 1}, queue="any.queue"
                )
        mock_apply.assert_called_once_with(("a",), {"k": 1})
        mock_super.assert_not_called()
        assert result == "eager_result"

    def test_eager_queue_match_calls_apply(self):
        """A queue in eager_task_queues runs eagerly even with task_always_eager=False."""
        CONFIG.celery.eager_task_queues = {DISCOVERY_MONITORS_DETECTION_QUEUE_NAME}
        task = self._make_task()
        with mock.patch.object(
            task, "apply", return_value="eager_result"
        ) as mock_apply:
            with mock.patch.object(Task, "apply_async") as mock_super:
                result = task.apply_async(
                    args=("arg",), queue=DISCOVERY_MONITORS_DETECTION_QUEUE_NAME
                )
        mock_apply.assert_called_once()
        mock_super.assert_not_called()
        assert result == "eager_result"

    def test_non_eager_queue_dispatches_normally(self):
        """A queue NOT in eager_task_queues is dispatched via super().apply_async."""
        CONFIG.celery.eager_task_queues = {DISCOVERY_MONITORS_DETECTION_QUEUE_NAME}
        task = self._make_task()
        with mock.patch.object(
            Task, "apply_async", return_value="dispatched"
        ) as mock_super:
            with mock.patch.object(task, "apply") as mock_apply:
                result = task.apply_async(args=(), queue="some.other.queue")
        mock_super.assert_called_once()
        mock_apply.assert_not_called()
        assert result == "dispatched"

    def test_multiple_eager_queues_both_match(self):
        """Multiple queues can be configured; each triggers eager execution."""
        CONFIG.celery.eager_task_queues = {
            DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
            DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
        }
        task = self._make_task()
        for queue_name in (
            DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
            DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
        ):
            with mock.patch.object(task, "apply", return_value="eager") as mock_apply:
                with mock.patch.object(Task, "apply_async") as mock_super:
                    task.apply_async(args=(), queue=queue_name)
            mock_apply.assert_called_once()
            mock_super.assert_not_called()

    def test_task_queue_attribute_used_when_no_queue_kwarg(self):
        """Falls back to task.queue when no queue kwarg is passed."""
        CONFIG.celery.eager_task_queues = {DISCOVERY_MONITORS_DETECTION_QUEUE_NAME}
        task = self._make_task(task_queue=DISCOVERY_MONITORS_DETECTION_QUEUE_NAME)
        with mock.patch.object(task, "apply", return_value="eager") as mock_apply:
            with mock.patch.object(Task, "apply_async") as mock_super:
                task.apply_async(args=())
        mock_apply.assert_called_once()
        mock_super.assert_not_called()

    def test_explicit_queue_kwarg_overrides_task_queue(self):
        """An explicit queue= kwarg takes precedence over the task's queue attribute."""
        CONFIG.celery.eager_task_queues = {DISCOVERY_MONITORS_DETECTION_QUEUE_NAME}
        # task.queue is the eager queue, but we override with a different queue
        task = self._make_task(task_queue=DISCOVERY_MONITORS_DETECTION_QUEUE_NAME)
        with mock.patch.object(
            Task, "apply_async", return_value="dispatched"
        ) as mock_super:
            with mock.patch.object(task, "apply") as mock_apply:
                result = task.apply_async(args=(), queue="some.other.queue")
        mock_super.assert_called_once()
        mock_apply.assert_not_called()

    def test_comma_separated_env_var_parses_correctly(self):
        """CelerySettings.eager_task_queues accepts a comma-separated string."""
        from fides.config.celery_settings import CelerySettings

        settings = CelerySettings(
            eager_task_queues=(
                f"{DISCOVERY_MONITORS_DETECTION_QUEUE_NAME},"
                f"{DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME}"
            )
        )
        assert settings.eager_task_queues == {
            DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
            DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
        }

    def test_empty_eager_task_queues_default(self):
        """CelerySettings.eager_task_queues defaults to an empty set."""
        from fides.config.celery_settings import CelerySettings

        settings = CelerySettings()
        assert settings.eager_task_queues == set()
