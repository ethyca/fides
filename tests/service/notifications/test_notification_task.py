"""Tests for the DSR notification task skeleton (Option C: event-driven + sweep)."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from fides.config import CONFIG
from fides.service.notifications import notification_task
from fides.service.notifications.notification_task import (
    NOTIFICATION_JOB,
    initiate_notification_task,
    register_notification_handler,
    register_notification_sweep,
    send_dsr_notification,
    sweep_notifications,
)

# ── Registration ─────────────────────────────────────────────────────


class TestRegisterNotificationSweep:
    def test_register_sets_sweep_fn(self, monkeypatch):
        mock_fn = MagicMock()
        monkeypatch.setattr(notification_task, "_sweep_fn", None)
        register_notification_sweep(mock_fn)
        assert notification_task._sweep_fn is mock_fn


class TestRegisterNotificationHandler:
    def test_register_sets_notify_fn(self, monkeypatch):
        mock_fn = MagicMock()
        monkeypatch.setattr(notification_task, "_notify_fn", None)
        register_notification_handler(mock_fn)
        assert notification_task._notify_fn is mock_fn


# ── Event-driven notify task ─────────────────────────────────────────


class TestSendDsrNotificationTask:
    def test_no_op_when_no_handler_registered(self, monkeypatch):
        """No handler registered — task skips without touching the DB."""
        monkeypatch.setattr(notification_task, "_notify_fn", None)
        send_dsr_notification.apply(args=["req-123", "request_completed"]).get()

    def test_delegates_to_registered_handler(self, monkeypatch):
        """Handler registered — task calls it with session, request ID, and event type."""
        mock_handler = MagicMock()
        monkeypatch.setattr(notification_task, "_notify_fn", mock_handler)

        mock_session = MagicMock()

        @contextmanager
        def _fake_get_new_session(_self):
            yield mock_session

        with patch(
            "fides.service.notifications.notification_task.DatabaseTask.get_new_session",
            _fake_get_new_session,
        ):
            send_dsr_notification.apply(args=["req-123", "request_completed"]).get()

        mock_handler.assert_called_once_with(
            mock_session, "req-123", "request_completed"
        )

    def test_handler_exception_propagates(self, monkeypatch):
        """Exception from the registered handler propagates as a Celery task failure."""
        monkeypatch.setattr(
            notification_task,
            "_notify_fn",
            MagicMock(side_effect=RuntimeError("boom")),
        )

        mock_session = MagicMock()

        @contextmanager
        def _fake_get_new_session(_self):
            yield mock_session

        with (
            patch(
                "fides.service.notifications.notification_task.DatabaseTask.get_new_session",
                _fake_get_new_session,
            ),
            pytest.raises(RuntimeError, match="boom"),
        ):
            send_dsr_notification.apply(args=["req-123", "request_completed"]).get()


# ── Sweep task ───────────────────────────────────────────────────────


class TestSweepNotificationsTask:
    def test_no_op_when_no_sweep_registered(self, monkeypatch):
        """Lock is acquired but no sweep fn is registered — task skips."""
        monkeypatch.setattr(notification_task, "_sweep_fn", None)

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield MagicMock()  # truthy lock

        with patch.object(notification_task, "redis_lock", _fake_lock):
            sweep_notifications.apply().get()

    def test_delegates_to_registered_sweep(self, monkeypatch):
        """Lock is acquired and a sweep fn is registered — task calls it with a DB session."""
        mock_sweep = MagicMock()
        monkeypatch.setattr(notification_task, "_sweep_fn", mock_sweep)

        mock_session = MagicMock()

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield MagicMock()

        @contextmanager
        def _fake_get_new_session(_self):
            yield mock_session

        with (
            patch.object(notification_task, "redis_lock", _fake_lock),
            patch(
                "fides.service.notifications.notification_task.DatabaseTask.get_new_session",
                _fake_get_new_session,
            ),
        ):
            sweep_notifications.apply().get()

        mock_sweep.assert_called_once_with(mock_session)

    def test_skips_when_lock_not_acquired(self, monkeypatch):
        """Another worker holds the lock — task exits without calling the sweep."""
        mock_sweep = MagicMock()
        monkeypatch.setattr(notification_task, "_sweep_fn", mock_sweep)

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield None  # lock not acquired

        with patch.object(notification_task, "redis_lock", _fake_lock):
            sweep_notifications.apply().get()

        mock_sweep.assert_not_called()

    def test_sweep_exception_propagates(self, monkeypatch):
        """Exception from the registered sweep fn propagates as a Celery task failure."""
        monkeypatch.setattr(
            notification_task,
            "_sweep_fn",
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
            patch.object(notification_task, "redis_lock", _fake_lock),
            patch(
                "fides.service.notifications.notification_task.DatabaseTask.get_new_session",
                _fake_get_new_session,
            ),
            pytest.raises(RuntimeError, match="boom"),
        ):
            sweep_notifications.apply().get()


# ── Scheduler wiring ─────────────────────────────────────────────────


class TestInitiateNotificationTask:
    def test_skips_in_test_mode(self, monkeypatch):
        monkeypatch.setattr(CONFIG, "test_mode", True)
        mock_scheduler = MagicMock()
        with patch.object(notification_task, "scheduler", mock_scheduler):
            initiate_notification_task()
        mock_scheduler.add_job.assert_not_called()

    def test_raises_when_scheduler_not_running(self, monkeypatch):
        monkeypatch.setattr(CONFIG, "test_mode", False)
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        with (
            patch.object(notification_task, "scheduler", mock_scheduler),
            pytest.raises(RuntimeError, match="Scheduler is not running"),
        ):
            initiate_notification_task()

    def test_adds_scheduler_job(self, monkeypatch):
        monkeypatch.setattr(CONFIG, "test_mode", False)
        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        with patch.object(notification_task, "scheduler", mock_scheduler):
            initiate_notification_task()

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs["id"] == NOTIFICATION_JOB
        assert call_kwargs["trigger"] == "interval"
        assert call_kwargs["func"] == sweep_notifications.delay
        assert call_kwargs["minutes"] == CONFIG.execution.notification_interval_minutes


# ── Config ───────────────────────────────────────────────────────────


class TestNotificationConfig:
    def test_default_notification_interval(self):
        assert CONFIG.execution.notification_interval_minutes == 5
