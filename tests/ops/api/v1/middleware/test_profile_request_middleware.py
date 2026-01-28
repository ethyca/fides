from unittest.mock import patch

import pytest

from fides.api.asgi_middleware import ProfileRequestMiddleware

from .conftest import (
    Message,
    Receive,
    ResponseCapture,
    Scope,
    Send,
    create_http_scope,
    noop_send,
)


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

    async def test_passes_through_without_header(self, mock_asgi_app):
        """Test that requests without profile-request header pass through unchanged."""
        app, app_result = mock_asgi_app(body=b'{"status": "ok"}')
        middleware = ProfileRequestMiddleware(app)

        scope = create_http_scope()
        capture = ResponseCapture()

        await middleware(scope, noop_receive, capture)

        assert app_result.called, "App should have been called"
        assert app_result.response_sent, "Original response should have been sent"
        assert len(capture.messages) == 2, "Should have sent start and body messages"
        assert capture.status == 200
        assert capture.body == b'{"status": "ok"}'

    async def test_returns_profiling_html_with_header(self, mock_asgi_app):
        """Test that requests with profile-request header return profiling HTML."""
        app, app_result = mock_asgi_app(body=b'{"status": "ok"}')
        middleware = ProfileRequestMiddleware(app)

        # Add profile-request header
        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b"true"),
            ]
        )
        capture = ResponseCapture()

        await middleware(scope, noop_receive, capture)

        assert app_result.called, "App should have been called for profiling"

        # Verify profiling response
        assert len(capture.messages) == 2, "Should have sent start and body messages"

        # Check response start
        assert capture.status == 200

        # Check content-type header
        headers_dict = dict(capture.headers)
        assert headers_dict[b"content-type"] == b"text/html; charset=utf-8"
        assert b"content-length" in headers_dict

        # Check response body contains HTML
        assert isinstance(capture.body, bytes)
        # pyinstrument HTML output contains these markers
        assert b"<!DOCTYPE html>" in capture.body or b"<html" in capture.body

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

        await middleware(scope, receive, noop_send)

        assert app_called, "App should be called for non-HTTP scopes"

    async def test_empty_header_value_passes_through(self, mock_asgi_app):
        """Test that empty profile-request header value passes through."""
        app, app_result = mock_asgi_app(body=b'{"status": "ok"}')
        middleware = ProfileRequestMiddleware(app)

        # Empty header value should not trigger profiling
        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b""),
            ]
        )
        capture = ResponseCapture()

        await middleware(scope, noop_receive, capture)

        assert app_result.called, "App should have been called"
        assert app_result.response_sent, "Original response should have been sent"
        # Original JSON response, not HTML profiling
        assert capture.body == b'{"status": "ok"}'

    async def test_discards_original_response_when_profiling(self):
        """Test that the original app response is discarded when profiling."""

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

        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b"1"),
            ]
        )
        capture = ResponseCapture()

        await middleware(scope, noop_receive, capture)

        # Verify we got profiling HTML, not the original 404 response
        assert len(capture.messages) == 2
        assert capture.status == 200  # Profiling always returns 200
        assert capture.headers[0] == (
            b"content-type",
            b"text/html; charset=utf-8",
        )

    @pytest.mark.parametrize(
        "header_value",
        [b"true", b"1", b"yes", b"anything"],
    )
    async def test_any_truthy_header_value_triggers_profiling(
        self, mock_asgi_app, header_value
    ):
        """Test that any truthy header value triggers profiling."""
        app, _ = mock_asgi_app()
        middleware = ProfileRequestMiddleware(app)

        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", header_value),
            ]
        )
        capture = ResponseCapture()

        await middleware(scope, noop_receive, capture)

        # Should return profiling HTML
        assert len(capture.messages) == 2
        headers_dict = dict(capture.headers)
        assert headers_dict[b"content-type"] == b"text/html; charset=utf-8"

    async def test_content_length_matches_body(self, mock_asgi_app):
        """Test that content-length header matches actual body size."""
        app, _ = mock_asgi_app()
        middleware = ProfileRequestMiddleware(app)

        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"profile-request", b"true"),
            ]
        )
        capture = ResponseCapture()

        await middleware(scope, noop_receive, capture)

        headers_dict = dict(capture.headers)
        content_length = int(headers_dict[b"content-length"].decode())
        actual_body_length = len(capture.body)

        assert content_length == actual_body_length, (
            f"Content-Length ({content_length}) doesn't match body size ({actual_body_length})"
        )
