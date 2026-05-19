"""Tests for the reply mailbox polling task skeleton."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from fides.config import CONFIG
from fides.service.correspondence import reply_polling_task
from fides.service.correspondence.reply_polling_task import (
    REPLY_POLLING_JOB,
    initiate_reply_polling,
    poll_reply_mailbox,
    register_reply_poll_service,
)


class TestRegisterReplyPollService:
    def test_register_sets_service_fn(self, monkeypatch):
        mock_fn = MagicMock()
        monkeypatch.setattr(reply_polling_task, "_service_fn", None)
        register_reply_poll_service(mock_fn)
        assert reply_polling_task._service_fn is mock_fn


class TestPollReplyMailboxTask:
    def test_no_op_when_no_service_registered(self, monkeypatch):
        """Lock is acquired but no service fn is registered — task skips."""
        monkeypatch.setattr(reply_polling_task, "_service_fn", None)

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield MagicMock()  # truthy lock

        with patch.object(reply_polling_task, "redis_lock", _fake_lock):
            poll_reply_mailbox.apply().get()

    def test_delegates_to_registered_service(self, monkeypatch):
        """Lock is acquired and a service fn is registered — task calls it with a DB session."""
        mock_service = MagicMock()
        monkeypatch.setattr(reply_polling_task, "_service_fn", mock_service)

        mock_session = MagicMock()

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield MagicMock()

        @contextmanager
        def _fake_get_new_session(_self):
            yield mock_session

        with (
            patch.object(reply_polling_task, "redis_lock", _fake_lock),
            patch(
                "fides.service.correspondence.reply_polling_task.DatabaseTask.get_new_session",
                _fake_get_new_session,
            ),
        ):
            poll_reply_mailbox.apply().get()

        mock_service.assert_called_once_with(mock_session)

    def test_skips_when_lock_not_acquired(self, monkeypatch):
        """Another worker holds the lock — task exits without calling the service."""
        mock_service = MagicMock()
        monkeypatch.setattr(reply_polling_task, "_service_fn", mock_service)

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield None  # lock not acquired

        with patch.object(reply_polling_task, "redis_lock", _fake_lock):
            poll_reply_mailbox.apply().get()

        mock_service.assert_not_called()

    def test_service_exception_propagates(self, monkeypatch):
        """Exception from the registered service fn propagates as a Celery task failure."""
        monkeypatch.setattr(
            reply_polling_task,
            "_service_fn",
            MagicMock(side_effect=RuntimeError("boom")),
        )

        mock_session = MagicMock()

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield MagicMock()

        @contextmanager
        def _fake_get_new_session(_self):
            yield mock_session

        with (
            patch.object(reply_polling_task, "redis_lock", _fake_lock),
            patch(
                "fides.service.correspondence.reply_polling_task.DatabaseTask.get_new_session",
                _fake_get_new_session,
            ),
            pytest.raises(RuntimeError, match="boom"),
        ):
            poll_reply_mailbox.apply().get()


class TestInitiateReplyPolling:
    def test_skips_in_test_mode(self, monkeypatch):
        monkeypatch.setattr(CONFIG, "test_mode", True)
        mock_scheduler = MagicMock()
        with patch.object(reply_polling_task, "scheduler", mock_scheduler):
            initiate_reply_polling()
        mock_scheduler.add_job.assert_not_called()

    def test_raises_when_scheduler_not_running(self, monkeypatch):
        monkeypatch.setattr(CONFIG, "test_mode", False)
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        with (
            patch.object(reply_polling_task, "scheduler", mock_scheduler),
            pytest.raises(RuntimeError, match="Scheduler is not running"),
        ):
            initiate_reply_polling()

    def test_adds_scheduler_job(self, monkeypatch):
        monkeypatch.setattr(CONFIG, "test_mode", False)
        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        with patch.object(reply_polling_task, "scheduler", mock_scheduler):
            initiate_reply_polling()

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs["id"] == REPLY_POLLING_JOB
        assert call_kwargs["trigger"] == "interval"
        assert call_kwargs["func"] == poll_reply_mailbox.delay
        assert call_kwargs["minutes"] == CONFIG.execution.reply_polling_interval_minutes


class TestReplyPollingConfig:
    def test_default_polling_interval(self):
        assert CONFIG.execution.reply_polling_interval_minutes == 3
