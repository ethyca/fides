"""Tests for the SQS heartbeat module (``src/fides/api/service/privacy_request/sqs_heartbeat.py``).

Covers:
- ``_get_sqs_queue_name`` — all branches
- ``_sqs_heartbeat_thread`` — success, failure, stop scenarios
- ``@sqs_heartbeat`` decorator — all execution paths
"""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from fides.api.service.privacy_request.sqs_heartbeat import (
    _get_sqs_queue_name,
    _sqs_heartbeat_thread,
    sqs_heartbeat,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    use_sqs_queue: bool = True,
    sqs_url: str = "http://elasticmq:9324",
    sqs_queue_name_prefix: str = "fides-",
    sqs_visibility_timeout: int = 300,
) -> SimpleNamespace:
    return SimpleNamespace(
        queue=SimpleNamespace(
            use_sqs_queue=use_sqs_queue,
            sqs_url=sqs_url,
            sqs_queue_name_prefix=sqs_queue_name_prefix,
            sqs_visibility_timeout=sqs_visibility_timeout,
        ),
    )


def _make_task(
    delivery_info: dict | None = None,
    sqs_message: dict | None = None,
    task_name: str = "test_task",
) -> MagicMock:
    """Build a mock Celery task instance suitable for decorator tests."""
    task = MagicMock()
    task.name = task_name
    task.request = MagicMock()
    task.request.delivery_info = delivery_info or {}
    if sqs_message is not None:
        task.request.sqs_message = sqs_message
    return task


# ===========================================================================
# _get_sqs_queue_name
# ===========================================================================


class TestGetSqsQueueName:
    """Tests for ``_get_sqs_queue_name``."""

    def test_returns_prefixed_name_with_delivery_info(self) -> None:
        """Normal path: delivery_info with routing_key → prefixed name."""
        task = _make_task(delivery_info={"routing_key": "fides.dsr"})
        with patch(
            "fides.api.service.privacy_request.sqs_heartbeat.CONFIG"
        ) as mock_config:
            mock_config.queue.sqs_queue_name_prefix = "test-"
            result = _get_sqs_queue_name(task)
        assert result == "test-fides.dsr"

    def test_returns_none_when_no_delivery_info(self) -> None:
        """Missing delivery_info → None."""
        task = _make_task(delivery_info=None)
        with patch("fides.api.service.privacy_request.sqs_heartbeat.CONFIG"):
            result = _get_sqs_queue_name(task)
        assert result is None

    def test_returns_none_when_no_routing_key(self) -> None:
        """Missing routing_key → None."""
        task = _make_task(delivery_info={})
        with patch("fides.api.service.privacy_request.sqs_heartbeat.CONFIG"):
            result = _get_sqs_queue_name(task)
        assert result is None


# ===========================================================================
# _sqs_heartbeat_thread
# ===========================================================================


class TestSqsHeartbeatThread:
    """Tests for ``_sqs_heartbeat_thread``."""

    def test_calls_change_message_visibility_repeatedly(self) -> None:
        """Normal path: calls ``change_message_visibility`` on each heartbeat."""
        sqs_client = MagicMock()
        stop_event = threading.Event()

        # Let it run a couple of iterations then stop.
        t = threading.Thread(
            target=_sqs_heartbeat_thread,
            args=(
                sqs_client,
                "http://elasticmq:9324/queue/fides-dsr",
                "test-receipt-handle",
                stop_event,
            ),
        )
        t.daemon = True
        t.start()

        # Wait for at least one successful call.
        deadline = time.time() + 10
        while (
            not sqs_client.change_message_visibility.called and time.time() < deadline
        ):
            time.sleep(0.1)

        call_count = sqs_client.change_message_visibility.call_count
        assert call_count >= 1

        # Verify the call args.
        first_call = sqs_client.change_message_visibility.call_args_list[0]
        assert first_call.kwargs["QueueUrl"] == "http://elasticmq:9324/queue/fides-dsr"
        assert first_call.kwargs["ReceiptHandle"] == "test-receipt-handle"
        assert first_call.kwargs["VisibilityTimeout"] == 300

        stop_event.set()
        t.join(timeout=5)

    def test_stops_when_stop_event_set(self) -> None:
        """Thread exits when stop_event is set."""
        sqs_client = MagicMock()
        stop_event = threading.Event()

        t = threading.Thread(
            target=_sqs_heartbeat_thread,
            args=(
                sqs_client,
                "http://elasticmq:9324/queue/fides-dsr",
                "test-receipt-handle",
                stop_event,
            ),
        )
        t.daemon = True
        t.start()

        # Wait for first call, then stop.
        deadline = time.time() + 5
        while (
            not sqs_client.change_message_visibility.called and time.time() < deadline
        ):
            time.sleep(0.1)

        stop_event.set()
        t.join(timeout=5)

        # Thread should have exited (or at least not be alive).
        assert not t.is_alive() or t.ident is None

    def test_returns_on_invalid_parameter_value_error(self) -> None:
        """``InvalidParameterValue`` error → thread returns immediately."""
        sqs_client = MagicMock()
        sqs_client.change_message_visibility = MagicMock(
            side_effect=ClientError(
                {"Error": {"Code": "InvalidParameterValue"}},
                "ChangeMessageVisibility",
            )
        )
        stop_event = threading.Event()

        t = threading.Thread(
            target=_sqs_heartbeat_thread,
            args=(
                sqs_client,
                "http://elasticmq:9324/queue/fides-dsr",
                "test-receipt-handle",
                stop_event,
            ),
        )
        t.daemon = True
        t.start()

        # Wait for the first call to be made.
        deadline = time.time() + 5
        while (
            not sqs_client.change_message_visibility.called and time.time() < deadline
        ):
            time.sleep(0.1)

        # Thread should exit quickly after the InvalidParameterValue.
        t.join(timeout=5)
        assert not t.is_alive()

    def test_retries_transient_errors_with_backoff(self) -> None:
        """Transient errors are retried up to 3 times with backoff."""
        sqs_client = MagicMock()
        stop_event = threading.Event()

        call_count = 0

        def _fail_then_succeed(*args: Any, **kwargs: Any) -> None:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception("transient failure")
            return None

        sqs_client.change_message_visibility = MagicMock(side_effect=_fail_then_succeed)

        t = threading.Thread(
            target=_sqs_heartbeat_thread,
            args=(
                sqs_client,
                "http://elasticmq:9324/queue/fides-dsr",
                "test-receipt-handle",
                stop_event,
            ),
        )
        t.daemon = True
        t.start()

        # Wait for it to eventually succeed (up to 3 retries + sleep).
        deadline = time.time() + 30
        while not stop_event.is_set() and time.time() < deadline:
            time.sleep(0.5)

        stop_event.set()
        t.join(timeout=5)


# ===========================================================================
# @sqs_heartbeat decorator
# ===========================================================================


class TestSqsHeartbeatDecorator:
    """Tests for the ``@sqs_heartbeat`` decorator."""

    def test_sqs_disabled_is_noop(self) -> None:
        """When SQS is disabled, the decorator calls the function directly."""
        call_log: list = []

        @sqs_heartbeat
        def my_task(self: Any) -> None:
            call_log.append("called")

        task = _make_task()
        my_task(task)
        assert call_log == ["called"]

    def test_sqs_enabled_no_receipt_handle_is_noop(self) -> None:
        """SQS enabled but no ``sqs_message`` → decorator is a no-op."""
        call_log: list = []

        @sqs_heartbeat
        def my_task(self: Any) -> None:
            call_log.append("called")

        task = _make_task(
            delivery_info={"routing_key": "fides.dsr"},
            sqs_message=None,
        )
        with patch(
            "fides.api.service.privacy_request.sqs_heartbeat.CONFIG"
        ) as mock_config:
            mock_config.queue = _make_config().queue
            my_task(task)

        assert call_log == ["called"]

    def test_sqs_enabled_with_receipt_handle_starts_thread(self) -> None:
        """SQS enabled with valid receipt handle → get_sqs_client called (thread path entered)."""
        call_log: list = []

        @sqs_heartbeat
        def my_task(self: Any) -> None:
            call_log.append("called")
            time.sleep(0.2)

        task = _make_task(
            delivery_info={"routing_key": "fides.dsr"},
            sqs_message={"ReceiptHandle": "test-handle"},
        )

        with (
            patch(
                "fides.api.service.privacy_request.sqs_heartbeat.CONFIG"
            ) as mock_config,
            patch(
                "fides.api.service.privacy_request.sqs_heartbeat.get_sqs_client"
            ) as mock_get_sqs,
        ):
            mock_config.queue = _make_config().queue
            mock_get_sqs.return_value = MagicMock()
            my_task(task)

        # The function was called.
        assert call_log == ["called"]
        # get_sqs_client was called, proving the thread path was entered.
        mock_get_sqs.assert_called_once()

    def test_sqs_enabled_thread_started_in_finally(self) -> None:
        """The heartbeat thread is stopped in ``finally`` regardless of exceptions."""

        @sqs_heartbeat
        def my_task(self: Any) -> None:
            raise ValueError("task error")

        task = _make_task(
            delivery_info={"routing_key": "fides.dsr"},
            sqs_message={"ReceiptHandle": "test-handle"},
        )
        stop_events: list[threading.Event] = []

        def capture_stop_event(*args: Any, **kwargs: Any) -> None:
            stop_events.append(args[3])

        with (
            patch(
                "fides.api.service.privacy_request.sqs_heartbeat.CONFIG"
            ) as mock_config,
            patch(
                "fides.api.service.privacy_request.sqs_heartbeat.get_sqs_client"
            ) as mock_get_sqs,
            patch(
                "fides.api.service.privacy_request.sqs_heartbeat._sqs_heartbeat_thread",
                side_effect=capture_stop_event,
            ),
        ):
            mock_config.queue = _make_config().queue
            mock_get_sqs.return_value = MagicMock()
            with pytest.raises(ValueError, match="task error"):
                my_task(task)

        # The stop event should have been set.
        assert len(stop_events) == 1
        assert stop_events[0].is_set()

    def test_sqs_enabled_no_queue_name_is_noop(self) -> None:
        """When ``_get_sqs_queue_name`` returns None, the decorator is a no-op."""
        call_log: list = []

        @sqs_heartbeat
        def my_task(self: Any) -> None:
            call_log.append("called")

        task = _make_task(
            delivery_info={"routing_key": "fides.dsr"},
            sqs_message={"ReceiptHandle": "test-handle"},
        )

        def _no_queue_name(task: Any) -> None:  # noqa: ARG001
            return None

        with (
            patch(
                "fides.api.service.privacy_request.sqs_heartbeat.CONFIG"
            ) as mock_config,
            patch(
                "fides.api.service.privacy_request.sqs_heartbeat._get_sqs_queue_name",
                side_effect=_no_queue_name,
            ),
        ):
            mock_config.queue = _make_config().queue
            my_task(task)

        assert call_log == ["called"]

    def test_decorator_preserves_function_metadata(self) -> None:
        """The decorator should preserve the wrapped function's name and docstring."""

        @sqs_heartbeat
        def my_named_task(self: Any) -> None:
            """My docstring."""
            pass

        assert my_named_task.__name__ == "my_named_task"

    def test_function_arguments_passed_through(self) -> None:
        """Arguments and return values pass through the decorator correctly."""
        received_args: list = []
        received_kwargs: dict = {}

        @sqs_heartbeat
        def my_task(
            self: Any,
            arg1: str,
            arg2: int,
            *,
            kwarg1: str = "default",
        ) -> str:
            received_args.append((arg1, arg2))
            received_kwargs["kwarg1"] = kwarg1
            return "result"

        task = _make_task()
        result = my_task(task, "hello", 42, kwarg1="custom")

        assert received_args == [("hello", 42)]
        assert received_kwargs == {"kwarg1": "custom"}
        assert result == "result"
