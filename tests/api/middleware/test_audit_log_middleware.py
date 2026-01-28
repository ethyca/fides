from typing import Optional
from unittest.mock import patch

import pytest

from fides.api.asgi_middleware import AuditLogMiddleware

from .conftest import (
    Message,
    Receive,
    Scope,
    Send,
    create_body_receive,
    create_chunked_receive,
    create_http_scope,
    noop_send,
)


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

    async def test_audits_post_request(
        self, mock_asgi_app, audit_tracker: AuditTracker
    ):
        """Test that POST requests trigger audit logging."""
        app, app_result = mock_asgi_app(capture_body=True)
        middleware = AuditLogMiddleware(app)

        request_body = b'{"test": "data"}'
        scope = create_http_scope(method="POST", path="/api/v1/privacy-request")
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

    async def test_skips_get_requests(self, mock_asgi_app, audit_tracker: AuditTracker):
        """Test that GET requests do not trigger audit logging."""
        app, _ = mock_asgi_app()
        middleware = AuditLogMiddleware(app)

        scope = create_http_scope(method="GET", path="/api/v1/privacy-request")
        receive = create_body_receive(b"")

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

    async def test_skips_ignored_paths(
        self, mock_asgi_app, audit_tracker: AuditTracker
    ):
        """Test that requests to ignored paths do not trigger audit logging."""
        app, _ = mock_asgi_app()
        middleware = AuditLogMiddleware(app)

        # /api/v1/login is in the default ignored paths
        scope = create_http_scope(method="POST", path="/api/v1/login")
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

    async def test_skips_when_config_disabled(
        self, mock_asgi_app, audit_tracker: AuditTracker
    ):
        """Test that audit logging is skipped when config flag is disabled."""
        app, _ = mock_asgi_app()
        middleware = AuditLogMiddleware(app)

        scope = create_http_scope(method="POST", path="/api/v1/privacy-request")
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
        self, mock_asgi_app, audit_tracker: AuditTracker, method: str, path: str
    ):
        """Test that PUT, DELETE, and PATCH requests trigger audit logging."""
        app, _ = mock_asgi_app()
        middleware = AuditLogMiddleware(app)

        scope = create_http_scope(method=method, path=path)
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

    async def test_body_buffering_with_chunked_data(
        self, mock_asgi_app, audit_tracker: AuditTracker
    ):
        """Test that request body is correctly buffered even when received in chunks."""
        app, app_result = mock_asgi_app(capture_body=True)
        middleware = AuditLogMiddleware(app)

        # Simulate chunked body delivery
        chunks = [b'{"chunk1": "', b'data", "chunk2": ', b'"more_data"}']
        expected_body = b"".join(chunks)

        scope = create_http_scope(method="POST", path="/api/v1/data")
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

    async def test_custom_ignored_paths(
        self, mock_asgi_app, audit_tracker: AuditTracker
    ):
        """Test that custom ignored paths are respected."""
        app, _ = mock_asgi_app()

        # Create middleware with custom ignored paths
        custom_ignored = {"/api/v1/login", "/api/v1/custom-skip"}
        middleware = AuditLogMiddleware(app, ignored_paths=custom_ignored)

        scope = create_http_scope(method="POST", path="/api/v1/custom-skip")
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

    async def test_handles_audit_exception_gracefully(self, mock_asgi_app):
        """Test that exceptions in audit logging don't break the request flow."""
        app, app_result = mock_asgi_app(capture_body=True)
        middleware = AuditLogMiddleware(app)

        async def failing_handle_audit(request):
            raise ValueError("Simulated audit failure")

        scope = create_http_scope(method="POST", path="/api/v1/test")
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

        assert app_result.called, "App should have completed processing"
        assert response_sent, "Response should have been sent despite audit failure"
