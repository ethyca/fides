"""Tests for X-Request-ID log correlation."""

import asyncio
import re

import pytest
from loguru import logger

from fides.api.asgi_middleware import LogRequestMiddleware
from fides.api.request_context import (
    get_request_id,
    get_user_id,
    reset_request_context,
    set_request_context,
    set_request_id,
)
from fides.api.tasks import (
    _clear_request_id,
    _propagate_request_id,
    _restore_request_id,
)

from .conftest import (
    ResponseCapture,
    create_body_receive,
    create_http_scope,
)


@pytest.fixture(autouse=True)
def _clean_request_context():
    """Reset request context before and after each test."""
    reset_request_context()
    yield
    reset_request_context()


UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


class TestRequestContext:
    """Tests for request_id get/set/reset on RequestContext."""

    def test_get_request_id_default(self):
        """Default request_id is None."""
        assert get_request_id() is None

    def test_set_and_get_request_id(self):
        """Setting request_id makes it retrievable."""
        set_request_id("test-123")
        assert get_request_id() == "test-123"

    def test_reset_clears_request_id(self):
        """Resetting context clears request_id."""
        set_request_id("test-123")
        assert get_request_id() == "test-123"
        reset_request_context()
        assert get_request_id() is None

    async def test_set_request_id_isolation(self):
        """Setting request_id in one async context does not affect another."""
        results = {}

        async def task_a():
            set_request_id("aaa")
            await asyncio.sleep(0.01)
            results["a"] = get_request_id()

        async def task_b():
            await asyncio.sleep(0.02)
            results["b"] = get_request_id()

        await asyncio.gather(task_a(), task_b())

        assert results["a"] == "aaa"
        assert results["b"] is None


class TestRequestIdMiddleware:
    """Tests for X-Request-ID handling in LogRequestMiddleware."""

    async def test_generates_request_id_when_absent(self, mock_asgi_app):
        """When no X-Request-ID header is sent, middleware generates a UUID."""
        app, _ = mock_asgi_app()
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(method="GET", path="/test")
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        assert capture.status == 200

        # Response should include X-Request-ID header with a valid UUID
        request_id_headers = [
            v.decode("latin-1") for k, v in capture.headers if k == b"x-request-id"
        ]
        assert len(request_id_headers) == 1
        assert UUID_PATTERN.match(request_id_headers[0])

    async def test_uses_client_supplied_request_id(self, mock_asgi_app):
        """When X-Request-ID header is sent, middleware uses it."""
        app, _ = mock_asgi_app()
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(
            method="GET",
            path="/test",
            headers=[(b"x-request-id", b"client-supplied-123")],
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        assert capture.status == 200

        # Response should echo back the client-supplied ID
        request_id_headers = [
            v.decode("latin-1") for k, v in capture.headers if k == b"x-request-id"
        ]
        assert len(request_id_headers) == 1
        assert request_id_headers[0] == "client-supplied-123"

    async def test_rejects_malformed_request_id(self, mock_asgi_app):
        """When X-Request-ID header contains invalid characters, middleware generates a UUID instead."""
        app, _ = mock_asgi_app()
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(
            method="GET",
            path="/test",
            headers=[(b"x-request-id", b"bad\nvalue\r\ninjection")],
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        assert capture.status == 200

        request_id_headers = [
            v.decode("latin-1") for k, v in capture.headers if k == b"x-request-id"
        ]
        assert len(request_id_headers) == 1
        # Should be a generated UUID, not the malformed input
        assert UUID_PATTERN.match(request_id_headers[0])

    async def test_rejects_oversized_request_id(self, mock_asgi_app):
        """When X-Request-ID header exceeds 128 chars, middleware generates a UUID instead."""
        app, _ = mock_asgi_app()
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(
            method="GET",
            path="/test",
            headers=[(b"x-request-id", b"a" * 200)],
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        assert capture.status == 200

        request_id_headers = [
            v.decode("latin-1") for k, v in capture.headers if k == b"x-request-id"
        ]
        assert len(request_id_headers) == 1
        assert UUID_PATTERN.match(request_id_headers[0])

    async def test_request_id_in_log_output(self, mock_asgi_app, loguru_caplog):
        """Request ID appears in log records via the patcher."""
        app, _ = mock_asgi_app()
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(
            method="GET",
            path="/test",
            headers=[(b"x-request-id", b"log-test-456")],
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        # Find the "Request received" log and check it has request_id
        log_record = next(
            record
            for record in loguru_caplog.records
            if "Request received" in record.message
        )
        assert log_record.extra.get("request_id") == "log-test-456"

    async def test_error_response_includes_request_id(self, mock_asgi_app):
        """When the app raises an exception, the 500 response still includes X-Request-ID."""
        app, _ = mock_asgi_app(exception=ValueError("boom"))
        middleware = LogRequestMiddleware(app)

        scope = create_http_scope(
            method="GET",
            path="/test",
            headers=[(b"x-request-id", b"error-test-789")],
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        await middleware(scope, receive, capture)

        assert capture.status == 500

        request_id_headers = [
            v.decode("latin-1") for k, v in capture.headers if k == b"x-request-id"
        ]
        assert len(request_id_headers) == 1
        assert request_id_headers[0] == "error-test-789"

    async def test_concurrent_requests_get_different_ids(self, mock_asgi_app):
        """Two requests without X-Request-ID get different generated UUIDs."""
        app, _ = mock_asgi_app()
        middleware = LogRequestMiddleware(app)

        capture1 = ResponseCapture()
        capture2 = ResponseCapture()

        await middleware(
            create_http_scope(method="GET", path="/a"),
            create_body_receive(b""),
            capture1,
        )
        await middleware(
            create_http_scope(method="GET", path="/b"),
            create_body_receive(b""),
            capture2,
        )

        id1 = next(
            v.decode("latin-1") for k, v in capture1.headers if k == b"x-request-id"
        )
        id2 = next(
            v.decode("latin-1") for k, v in capture2.headers if k == b"x-request-id"
        )
        assert id1 != id2


class TestLoggerPatcher:
    """Tests for the Loguru patcher that injects request_id."""

    def test_patcher_injects_request_id(self, loguru_caplog):
        """When request_id is set, it appears in log records."""
        set_request_id("patcher-test-abc")
        logger.info("test message")

        record = loguru_caplog.records[-1]
        assert record.extra.get("request_id") == "patcher-test-abc"

    def test_patcher_omits_request_id_when_none(self, loguru_caplog):
        """When no request_id is set, it's not added to log records."""
        logger.info("test message without context")

        record = loguru_caplog.records[-1]
        assert "request_id" not in record.extra


class TestCelerySignals:
    """Tests for Celery request_id propagation signals."""

    def test_propagate_request_id_attaches_to_headers(self):
        """before_task_publish attaches request_id to task headers."""
        set_request_id("celery-test-123")
        headers = {}
        _propagate_request_id(headers=headers)

        assert headers["request_id"] == "celery-test-123"

    def test_propagate_request_id_skips_when_none(self):
        """before_task_publish does not add header when no request_id."""
        headers = {}
        _propagate_request_id(headers=headers)

        assert "request_id" not in headers

    def test_restore_request_id_sets_context(self):
        """task_prerun restores request_id from task headers."""
        mock_task = type(
            "MockTask",
            (),
            {"request": type("MockRequest", (), {"request_id": "worker-test-456"})()},
        )()

        _restore_request_id(task=mock_task)

        assert get_request_id() == "worker-test-456"

    def test_restore_request_id_skips_when_absent(self):
        """task_prerun does nothing when task has no request_id header."""
        mock_task = type("MockTask", (), {"request": type("MockRequest", (), {})()})()

        _restore_request_id(task=mock_task)

        assert get_request_id() is None

    def test_clear_request_id_after_task(self):
        """task_postrun clears only the request_id, not other context."""
        set_request_context(request_id="should-be-cleared", user_id="keep-me")
        _clear_request_id()

        assert get_request_id() is None
        assert get_user_id() == "keep-me"
