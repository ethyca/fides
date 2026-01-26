"""Tests for the request logging middleware."""

import asyncio
from typing import Any, Awaitable, Callable, MutableMapping

import pytest

from fides.api.util.asgi_middleware import LogRequestMiddleware

# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class TestLogRequest:
    """Tests for the request logging middleware timing functionality."""

    @pytest.mark.asyncio
    async def test_log_request_timing(self, loguru_caplog):
        """Test that the log_request middleware correctly calculates request handling time."""

        # Create a mock ASGI app with artificial delay
        async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
            await asyncio.sleep(0.1)  # 100ms delay
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b"{}"})

        # Create the middleware
        middleware = LogRequestMiddleware(mock_app)

        # Create scope for the request
        scope: Scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }

        # Create mock receive (not used in this test)
        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        # Track sent messages
        sent_messages = []

        async def send(message: Message) -> None:
            sent_messages.append(message)

        # Call the middleware
        await middleware(scope, receive, send)

        # Verify the response was sent
        assert len(sent_messages) >= 1
        assert sent_messages[0]["type"] == "http.response.start"
        assert sent_messages[0]["status"] == 200

        # Verify the log message and its contents
        assert "Request received" in loguru_caplog.text
        log_record = next(
            record for record in loguru_caplog.records if "method" in record.extra
        )
        assert log_record.extra["method"] == "GET"
        assert log_record.extra["status_code"] == 200
        assert log_record.extra["path"] == "/test"
        assert "handler_time" in log_record.extra
        assert log_record.extra["handler_time"].endswith("ms")

        # Extract the handler_time value and convert it to float for comparison
        handler_time_str = log_record.extra["handler_time"]
        actual_ms = float(handler_time_str[:-2])  # Remove "ms" and convert to float

        # Timing should be at least 100ms since we added an artificial delay
        assert actual_ms >= 100

    @pytest.mark.asyncio
    async def test_log_request_timing_slow_request(self, loguru_caplog):
        """
        Test that the log_request middleware correctly calculates request handling time
        for "slow" requests, i.e requests that take longer than 1 second to process.
        """

        # Create a mock ASGI app with artificial delay
        async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
            await asyncio.sleep(1.5)  # 1500ms delay
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b"{}"})

        # Create the middleware
        middleware = LogRequestMiddleware(mock_app)

        # Create scope for the request
        scope: Scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }

        # Create mock receive (not used in this test)
        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        # Track sent messages
        sent_messages = []

        async def send(message: Message) -> None:
            sent_messages.append(message)

        # Call the middleware
        await middleware(scope, receive, send)

        # Verify the response was sent
        assert len(sent_messages) >= 1
        assert sent_messages[0]["type"] == "http.response.start"
        assert sent_messages[0]["status"] == 200

        # Verify the log message and its contents
        assert "Request received" in loguru_caplog.text
        log_record = next(
            record for record in loguru_caplog.records if "method" in record.extra
        )
        assert log_record.extra["method"] == "GET"
        assert log_record.extra["status_code"] == 200
        assert log_record.extra["path"] == "/test"
        assert "handler_time" in log_record.extra
        assert log_record.extra["handler_time"].endswith("ms")

        # Extract the handler_time value and convert it to float for comparison
        handler_time_str = log_record.extra["handler_time"]
        actual_ms = float(handler_time_str[:-2])  # Remove "ms" and convert to float

        # Timing should be at least 1000ms since we added an artificial delay
        assert actual_ms >= 1000

    @pytest.mark.asyncio
    async def test_log_request_error(self, loguru_caplog):
        """Test that the log_request middleware correctly handles errors."""

        # Create a mock ASGI app that raises an exception
        async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
            raise ValueError("Test error")

        # Create the middleware
        middleware = LogRequestMiddleware(mock_app)

        # Create scope for the request
        scope: Scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }

        # Create mock receive (not used in this test)
        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        # Track sent messages
        sent_messages = []

        async def send(message: Message) -> None:
            sent_messages.append(message)

        # Call the middleware - it should catch the exception and send a 500 response
        await middleware(scope, receive, send)

        # Verify we get a 500 response for the error
        assert len(sent_messages) >= 2
        assert sent_messages[0]["type"] == "http.response.start"
        assert sent_messages[0]["status"] == 500

        # Verify the log message and its contents
        unhandled_exception_log_record = loguru_caplog.records[0]
        assert (
            "Unhandled exception processing request"
            in unhandled_exception_log_record.message
        )
        assert "Test error" in unhandled_exception_log_record.message

        request_received_logs = [
            line for line in loguru_caplog.records if "Request received" in line.message
        ]
        assert len(request_received_logs) > 0

        assert any(log.extra.get("method") == "GET" for log in request_received_logs)
        assert any(log.extra.get("status_code") == 500 for log in request_received_logs)
        assert any(log.extra.get("path") == "/test" for log in request_received_logs)
        assert any(log.extra.get("handler_time") for log in request_received_logs)
        assert any(
            log.extra.get("handler_time", "").endswith("ms")
            for log in request_received_logs
        )
