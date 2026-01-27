from typing import Any, Awaitable, Callable, MutableMapping
from unittest.mock import patch

import pytest

from fides.api.asgi_middleware import ProfileRequestMiddleware

# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]


class MockAppResult:
    """Container for mock app execution results."""

    def __init__(self):
        self.called: bool = False
        self.response_sent: bool = False


def create_mock_app() -> tuple[Callable, MockAppResult]:
    """
    Factory function to create a mock ASGI app.

    Returns:
        Tuple of (mock_app callable, MockAppResult for inspection)
    """
    result = MockAppResult()

    async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
        result.called = True
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": b'{"status": "ok"}'})
        result.response_sent = True

    return mock_app, result


def create_scope(
    method: str = "GET", path: str = "/api/v1/test", headers: list = None
) -> Scope:
    """Create a basic HTTP scope."""
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers or [(b"host", b"localhost")],
    }


async def noop_receive() -> Message:
    """A no-op receive callable."""
    return {"type": "http.request", "body": b"", "more_body": False}


class TestProfileRequestMiddleware:
    """
    Unit tests for ProfileRequestMiddleware.

    Verifies that:
    - Requests without profile-request header pass through unchanged
    - Requests with profile-request header return profiling HTML
    - Non-HTTP scopes pass through unchanged
    - Profiling response has correct content-type and status
    """

    async def test_passes_through_without_header(self):
        """Test that requests without profile-request header pass through unchanged."""
        mock_app, app_result = create_mock_app()
        middleware = ProfileRequestMiddleware(mock_app)

        scope = create_scope()
        messages_sent = []

        async def tracking_send(message: Message) -> None:
            messages_sent.append(message)

        await middleware(scope, noop_receive, tracking_send)

        assert app_result.called, "App should have been called"
        assert app_result.response_sent, "Original response should have been sent"
        assert len(messages_sent) == 2, "Should have sent start and body messages"
        assert messages_sent[0]["status"] == 200
        assert messages_sent[1]["body"] == b'{"status": "ok"}'

    async def test_returns_profiling_html_with_header(self):
        """Test that requests with profile-request header return profiling HTML."""
        mock_app, app_result = create_mock_app()
        middleware = ProfileRequestMiddleware(mock_app)

        # Add profile-request header
        scope = create_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b"true"),
            ]
        )
        messages_sent = []

        async def tracking_send(message: Message) -> None:
            messages_sent.append(message)

        await middleware(scope, noop_receive, tracking_send)

        assert app_result.called, "App should have been called for profiling"

        # Verify profiling response
        assert len(messages_sent) == 2, "Should have sent start and body messages"

        # Check response start
        start_message = messages_sent[0]
        assert start_message["type"] == "http.response.start"
        assert start_message["status"] == 200

        # Check content-type header
        headers_dict = dict(start_message["headers"])
        assert headers_dict[b"content-type"] == b"text/html; charset=utf-8"
        assert b"content-length" in headers_dict

        # Check response body contains HTML
        body_message = messages_sent[1]
        assert body_message["type"] == "http.response.body"
        body = body_message["body"]
        assert isinstance(body, bytes)
        # pyinstrument HTML output contains these markers
        assert b"<!DOCTYPE html>" in body or b"<html" in body

    async def test_skips_non_http_scopes(self):
        """Test that non-HTTP scopes (websocket, lifespan) pass through."""
        app_called = False

        async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal app_called
            app_called = True

        middleware = ProfileRequestMiddleware(mock_app)

        scope: Scope = {
            "type": "websocket",
            "path": "/ws",
        }

        async def receive() -> Message:
            return {"type": "websocket.connect"}

        async def send(message: Message) -> None:
            pass

        await middleware(scope, receive, send)

        assert app_called, "App should be called for non-HTTP scopes"

    async def test_empty_header_value_passes_through(self):
        """Test that empty profile-request header value passes through."""
        mock_app, app_result = create_mock_app()
        middleware = ProfileRequestMiddleware(mock_app)

        # Empty header value should not trigger profiling
        scope = create_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b""),
            ]
        )
        messages_sent = []

        async def tracking_send(message: Message) -> None:
            messages_sent.append(message)

        await middleware(scope, noop_receive, tracking_send)

        assert app_result.called, "App should have been called"
        assert app_result.response_sent, "Original response should have been sent"
        # Original JSON response, not HTML profiling
        assert messages_sent[1]["body"] == b'{"status": "ok"}'

    async def test_discards_original_response_when_profiling(self):
        """Test that the original app response is discarded when profiling."""
        original_response_captured = []

        async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error": "not found"}'}
            )

        middleware = ProfileRequestMiddleware(mock_app)

        scope = create_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b"1"),
            ]
        )
        messages_sent = []

        async def tracking_send(message: Message) -> None:
            messages_sent.append(message)

        await middleware(scope, noop_receive, tracking_send)

        # Verify we got profiling HTML, not the original 404 response
        assert len(messages_sent) == 2
        assert messages_sent[0]["status"] == 200  # Profiling always returns 200
        assert messages_sent[0]["headers"][0] == (
            b"content-type",
            b"text/html; charset=utf-8",
        )

    @pytest.mark.parametrize(
        "header_value",
        [b"true", b"1", b"yes", b"anything"],
    )
    async def test_any_truthy_header_value_triggers_profiling(self, header_value):
        """Test that any truthy header value triggers profiling."""
        mock_app, _ = create_mock_app()
        middleware = ProfileRequestMiddleware(mock_app)

        scope = create_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", header_value),
            ]
        )
        messages_sent = []

        async def tracking_send(message: Message) -> None:
            messages_sent.append(message)

        await middleware(scope, noop_receive, tracking_send)

        # Should return profiling HTML
        assert len(messages_sent) == 2
        headers_dict = dict(messages_sent[0]["headers"])
        assert headers_dict[b"content-type"] == b"text/html; charset=utf-8"

    async def test_content_length_matches_body(self):
        """Test that content-length header matches actual body size."""
        mock_app, _ = create_mock_app()
        middleware = ProfileRequestMiddleware(mock_app)

        scope = create_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b"true"),
            ]
        )
        messages_sent = []

        async def tracking_send(message: Message) -> None:
            messages_sent.append(message)

        await middleware(scope, noop_receive, tracking_send)

        headers_dict = dict(messages_sent[0]["headers"])
        content_length = int(headers_dict[b"content-length"].decode())
        actual_body_length = len(messages_sent[1]["body"])

        assert content_length == actual_body_length, (
            f"Content-Length ({content_length}) doesn't match body size ({actual_body_length})"
        )
