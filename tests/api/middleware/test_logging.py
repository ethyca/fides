"""Tests for the request logging middleware."""

import pytest

from fides.api.asgi_middleware import LogRequestMiddleware

from .conftest import (
    ResponseCapture,
    create_body_receive,
    create_http_scope,
)


class TestLogRequest:
    """Tests for the request logging middleware timing functionality."""

    @pytest.mark.asyncio
    async def test_log_request_timing(self, mock_asgi_app, loguru_caplog):
        """Test that the log_request middleware correctly calculates request handling time."""
        app, _ = mock_asgi_app(delay=0.1)  # 100ms delay
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(method="GET", path="/test")
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        # Verify the response was sent
        assert len(capture.messages) >= 1
        assert capture.status == 200

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
    async def test_log_request_timing_slow_request(self, mock_asgi_app, loguru_caplog):
        """
        Test that the log_request middleware correctly calculates request handling time
        for "slow" requests, i.e requests that take longer than 1 second to process.
        """
        app, _ = mock_asgi_app(delay=1.5)  # 1500ms delay
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(method="GET", path="/test")
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        # Verify the response was sent
        assert len(capture.messages) >= 1
        assert capture.status == 200

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
    async def test_log_request_error(self, mock_asgi_app, loguru_caplog):
        """Test that the log_request middleware correctly handles errors."""
        app, _ = mock_asgi_app(exception=ValueError("Test error"))
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(method="GET", path="/test")
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        # Call the middleware - it should catch the exception and send a 500 response
        await middleware(scope, receive, capture)

        # Verify we get a 500 response for the error
        assert len(capture.messages) >= 2
        assert capture.status == 500

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
