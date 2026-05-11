"""Tests for the DSR notification task skeleton."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from fides.config import CONFIG
from fides.service.notifications import notification_task
from fides.service.notifications.notification_task import (
    NOTIFICATION_JOB,
    initiate_notification_task,
    register_notification_service,
    send_notifications,
)


class TestRegisterNotificationService:
    def test_register_sets_service_fn(self, monkeypatch):
        mock_fn = MagicMock()
        monkeypatch.setattr(notification_task, "_service_fn", None)
        register_notification_service(mock_fn)
        assert notification_task._service_fn is mock_fn


class TestSendNotificationsTask:
    def test_no_op_when_no_service_registered(self, monkeypatch):
        """Lock is acquired but no service fn is registered — task skips."""
        monkeypatch.setattr(notification_task, "_service_fn", None)

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield MagicMock()  # truthy lock

        with patch.object(notification_task, "redis_lock", _fake_lock):
            send_notifications.apply().get()

    def test_delegates_to_registered_service(self, monkeypatch):
        """Lock is acquired and a service fn is registered — task calls it with a DB session."""
        mock_service = MagicMock()
        monkeypatch.setattr(notification_task, "_service_fn", mock_service)

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
            send_notifications.apply().get()

        mock_service.assert_called_once_with(mock_session)

    def test_skips_when_lock_not_acquired(self, monkeypatch):
        """Another worker holds the lock — task exits without calling the service."""
        mock_service = MagicMock()
        monkeypatch.setattr(notification_task, "_service_fn", mock_service)

        @contextmanager
        def _fake_lock(*_args, **_kwargs):
            yield None  # lock not acquired

        with patch.object(notification_task, "redis_lock", _fake_lock):
            send_notifications.apply().get()

        mock_service.assert_not_called()


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
        assert call_kwargs["func"] == send_notifications.delay
        assert call_kwargs["minutes"] == CONFIG.execution.notification_interval_minutes


class TestNotificationConfig:
    def test_default_notification_interval(self):
        assert CONFIG.execution.notification_interval_minutes == 5
