from typing import Any, Awaitable, Callable, MutableMapping, Optional
from unittest.mock import patch

import pytest

from fides.api.asgi_middleware import AuditLogMiddleware

# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]


class MockAppResult:
    """Container for mock app execution results."""

    def __init__(self):
        self.received_body: Optional[bytes] = None
        self.completed: bool = False


class AuditTracker:
    """Tracks audit logging calls and captured data."""

    def __init__(self):
        self.called: bool = False
        self.captured_body: Optional[bytes] = None

    async def handler(self, request):
        """Mock audit handler that tracks calls."""
        self.called = True

    async def body_capturing_handler(self, request):
        """Mock audit handler that captures the request body."""
        self.called = True
        self.captured_body = await request.body()


def create_mock_app(
    status_code: int = 200, capture_body: bool = False
) -> tuple[Callable, MockAppResult]:
    """
    Factory function to create a mock ASGI app.

    Args:
        status_code: HTTP status code to return
        capture_body: Whether to consume and capture the request body

    Returns:
        Tuple of (mock_app callable, MockAppResult for inspection)
    """
    result = MockAppResult()

    async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
        if capture_body:
            body_parts = []
            while True:
                message = await receive()
                body = message.get("body", b"")
                if body:
                    body_parts.append(body)
                if not message.get("more_body", False):
                    break
            result.received_body = b"".join(body_parts)

        result.completed = True
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": b"{}"})

    return mock_app, result


def create_scope(method: str = "POST", path: str = "/api/v1/test") -> Scope:
    """Create a basic HTTP scope."""
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(b"host", b"localhost")],
    }


def create_body_receive(body: bytes = b"") -> Receive:
    """Create a receive callable that returns a single body message."""
    sent = False

    async def receive() -> Message:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive


def create_chunked_receive(chunks: list[bytes]) -> Receive:
    """Create a receive callable that returns body in chunks."""
    chunk_index = 0

    async def receive() -> Message:
        nonlocal chunk_index
        if chunk_index < len(chunks):
            body = chunks[chunk_index]
            more_body = chunk_index < len(chunks) - 1
            chunk_index += 1
            return {"type": "http.request", "body": body, "more_body": more_body}
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive


async def noop_send(message: Message) -> None:
    """A no-op send callable."""
    pass


@pytest.fixture
def audit_tracker() -> AuditTracker:
    """Fixture that provides a fresh AuditTracker for each test."""
    return AuditTracker()


class TestAuditLogMiddleware:
    """
    Unit tests for AuditLogMiddleware.

    Verifies that:
    - Non-GET requests are audited
    - GET requests are skipped
    - Ignored paths are skipped
    - Request body is properly buffered for audit logging
    - Downstream app still receives the full request body
    - Audit logging is disabled when config flag is off
    """

    async def test_audits_post_request(self, audit_tracker: AuditTracker):
        """Test that POST requests trigger audit logging."""
        mock_app, app_result = create_mock_app(capture_body=True)
        middleware = AuditLogMiddleware(mock_app)

        request_body = b'{"test": "data"}'
        scope = create_scope(method="POST", path="/api/v1/privacy-request")
        receive = create_body_receive(request_body)

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                True,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                audit_tracker.handler,
            ),
        ):
            await middleware(scope, receive, noop_send)

        assert audit_tracker.called, (
            "Audit logging should have been called for POST request"
        )
        assert app_result.received_body == request_body, (
            "Downstream app should have received the full request body"
        )

    async def test_skips_get_requests(self, audit_tracker: AuditTracker):
        """Test that GET requests do not trigger audit logging."""
        mock_app, _ = create_mock_app()
        middleware = AuditLogMiddleware(mock_app)

        scope = create_scope(method="GET", path="/api/v1/privacy-request")
        receive = create_body_receive()

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                True,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                audit_tracker.handler,
            ),
        ):
            await middleware(scope, receive, noop_send)

        assert not audit_tracker.called, (
            "Audit logging should NOT be called for GET requests"
        )

    async def test_skips_ignored_paths(self, audit_tracker: AuditTracker):
        """Test that requests to ignored paths do not trigger audit logging."""
        mock_app, _ = create_mock_app()
        middleware = AuditLogMiddleware(mock_app)

        # /api/v1/login is in the default ignored paths
        scope = create_scope(method="POST", path="/api/v1/login")
        receive = create_body_receive(b'{"username": "test"}')

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                True,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                audit_tracker.handler,
            ),
        ):
            await middleware(scope, receive, noop_send)

        assert not audit_tracker.called, (
            "Audit logging should NOT be called for ignored paths"
        )

    async def test_skips_when_config_disabled(self, audit_tracker: AuditTracker):
        """Test that audit logging is skipped when config flag is disabled."""
        mock_app, _ = create_mock_app()
        middleware = AuditLogMiddleware(mock_app)

        scope = create_scope(method="POST", path="/api/v1/privacy-request")
        receive = create_body_receive(b'{"test": "data"}')

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                False,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                audit_tracker.handler,
            ),
        ):
            await middleware(scope, receive, noop_send)

        assert not audit_tracker.called, (
            "Audit logging should NOT be called when config is disabled"
        )

    @pytest.mark.parametrize(
        "method,path",
        [
            ("PUT", "/api/v1/system"),
            ("DELETE", "/api/v1/system/test-system"),
            ("PATCH", "/api/v1/user/preferences"),
        ],
    )
    async def test_audits_mutating_requests(
        self, audit_tracker: AuditTracker, method: str, path: str
    ):
        """Test that PUT, DELETE, and PATCH requests trigger audit logging."""
        mock_app, _ = create_mock_app()
        middleware = AuditLogMiddleware(mock_app)

        scope = create_scope(method=method, path=path)
        receive = create_body_receive(b'{"test": "data"}')

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                True,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                audit_tracker.handler,
            ),
        ):
            await middleware(scope, receive, noop_send)

        assert audit_tracker.called, (
            f"Audit logging should have been called for {method} request"
        )

    async def test_body_buffering_with_chunked_data(self, audit_tracker: AuditTracker):
        """Test that request body is correctly buffered even when received in chunks."""
        mock_app, app_result = create_mock_app(capture_body=True)
        middleware = AuditLogMiddleware(mock_app)

        # Simulate chunked body delivery
        chunks = [b'{"chunk1": "', b'data", "chunk2": ', b'"more_data"}']
        expected_body = b"".join(chunks)

        scope = create_scope(method="POST", path="/api/v1/data")
        receive = create_chunked_receive(chunks)

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                True,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                audit_tracker.body_capturing_handler,
            ),
        ):
            await middleware(scope, receive, noop_send)

        assert app_result.received_body == expected_body, (
            f"Downstream app should have received full body. Got: {app_result.received_body}"
        )
        assert audit_tracker.captured_body == expected_body, (
            f"Audit handler should have received full body. Got: {audit_tracker.captured_body}"
        )

    async def test_custom_ignored_paths(self, audit_tracker: AuditTracker):
        """Test that custom ignored paths are respected."""
        mock_app, _ = create_mock_app()

        # Create middleware with custom ignored paths
        custom_ignored = {"/api/v1/login", "/api/v1/custom-skip"}
        middleware = AuditLogMiddleware(mock_app, ignored_paths=custom_ignored)

        scope = create_scope(method="POST", path="/api/v1/custom-skip")
        receive = create_body_receive(b'{"test": "data"}')

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                True,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                audit_tracker.handler,
            ),
        ):
            await middleware(scope, receive, noop_send)

        assert not audit_tracker.called, (
            "Audit logging should NOT be called for custom ignored path"
        )

    async def test_skips_non_http_scopes(self, audit_tracker: AuditTracker):
        """Test that non-HTTP scopes (websocket, lifespan) are passed through."""
        app_called = False

        async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal app_called
            app_called = True

        middleware = AuditLogMiddleware(mock_app)

        # Test websocket scope
        scope: Scope = {
            "type": "websocket",
            "path": "/ws",
        }

        async def receive() -> Message:
            return {"type": "websocket.connect"}

        with patch(
            "fides.api.asgi_middleware.handle_audit_log_resource",
            audit_tracker.handler,
        ):
            await middleware(scope, receive, noop_send)

        assert app_called, "App should be called for non-HTTP scopes"
        assert not audit_tracker.called, (
            "Audit logging should NOT be triggered for non-HTTP scopes"
        )

    async def test_handles_audit_exception_gracefully(self):
        """Test that exceptions in audit logging don't break the request flow."""
        mock_app, app_result = create_mock_app(capture_body=True)
        middleware = AuditLogMiddleware(mock_app)

        async def failing_handle_audit(request):
            raise ValueError("Simulated audit failure")

        scope = create_scope(method="POST", path="/api/v1/test")
        receive = create_body_receive(b'{"test": "data"}')

        messages_sent = []
        response_sent = False

        async def tracking_send(message: Message) -> None:
            nonlocal response_sent
            messages_sent.append(message)
            if message["type"] == "http.response.body":
                response_sent = True

        with (
            patch(
                "fides.api.asgi_middleware.CONFIG.security.enable_audit_log_resource_middleware",
                True,
            ),
            patch(
                "fides.api.asgi_middleware.handle_audit_log_resource",
                failing_handle_audit,
            ),
        ):
            # Should not raise an exception
            await middleware(scope, receive, tracking_send)

        assert app_result.completed, "App should have completed processing"
        assert response_sent, "Response should have been sent despite audit failure"
