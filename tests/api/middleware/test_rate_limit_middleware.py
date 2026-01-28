"""Tests for the RateLimitIPValidationMiddleware."""

import json
from unittest.mock import patch

import pytest

from fides.api.util.rate_limit import RateLimitIPValidationMiddleware

from .conftest import (
    Message,
    ResponseCapture,
    Scope,
    create_body_receive,
    create_http_scope,
)


class TestRateLimitIPValidationMiddleware:
    """
    Unit tests for RateLimitIPValidationMiddleware.

    Verifies that:
    - Passes through when rate limiting is disabled
    - Passes through when header is not configured
    - Passes through when header is missing from request
    - Passes through with valid public IP addresses
    - Returns 422 for invalid/private/malformed IPs
    - Non-HTTP scopes pass through unchanged
    """

    async def test_passes_through_when_rate_limiting_disabled(self, mock_asgi_app):
        """Test that requests pass through when rate limiting is disabled."""
        app, app_result = mock_asgi_app()
        middleware = RateLimitIPValidationMiddleware(app)

        scope = create_http_scope()
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        with patch("fides.api.util.rate_limit.is_rate_limit_enabled", False):
            await middleware(scope, receive, capture)

        assert app_result.called, "App should be called when rate limiting is disabled"
        assert capture.status == 200

    async def test_passes_through_when_header_not_configured(self, mock_asgi_app):
        """Test that requests pass through when no IP header is configured."""
        app, app_result = mock_asgi_app()
        middleware = RateLimitIPValidationMiddleware(app)

        scope = create_http_scope()
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        with (
            patch("fides.api.util.rate_limit.is_rate_limit_enabled", True),
            patch(
                "fides.api.util.rate_limit.CONFIG.security.rate_limit_client_ip_header",
                None,
            ),
        ):
            await middleware(scope, receive, capture)

        assert app_result.called, "App should be called when header is not configured"
        assert capture.status == 200

    async def test_passes_through_when_header_missing_from_request(self, mock_asgi_app):
        """Test that requests pass through when the configured header is missing."""
        app, app_result = mock_asgi_app()
        middleware = RateLimitIPValidationMiddleware(app)

        # Request without the X-Real-IP header
        scope = create_http_scope(headers=[(b"host", b"localhost")])
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        with (
            patch("fides.api.util.rate_limit.is_rate_limit_enabled", True),
            patch(
                "fides.api.util.rate_limit.CONFIG.security.rate_limit_client_ip_header",
                "X-Real-IP",
            ),
        ):
            await middleware(scope, receive, capture)

        assert app_result.called, "App should be called when header is missing"
        assert capture.status == 200

    @pytest.mark.parametrize(
        "ip_address",
        [
            "8.8.8.8",  # Google DNS - valid public IPv4
            "150.51.100.10",  # Valid public IPv4
            "2001:4860:4860::8888",  # Google DNS - valid public IPv6
            "150.51.100.10:8080",  # Valid IP with port
            "[2001:4860:4860::8888]:443",  # Valid IPv6 with port
        ],
    )
    async def test_passes_through_with_valid_public_ip(self, mock_asgi_app, ip_address):
        """Test that requests with valid public IPs pass through."""
        app, app_result = mock_asgi_app()
        middleware = RateLimitIPValidationMiddleware(app)

        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"x-real-ip", ip_address.encode("latin-1")),
            ]
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        with (
            patch("fides.api.util.rate_limit.is_rate_limit_enabled", True),
            patch(
                "fides.api.util.rate_limit.CONFIG.security.rate_limit_client_ip_header",
                "X-Real-IP",
            ),
        ):
            await middleware(scope, receive, capture)

        assert app_result.called, f"App should be called for valid IP: {ip_address}"
        assert capture.status == 200

    @pytest.mark.parametrize(
        "invalid_ip,reason",
        [
            ("192.168.1.1", "private IP"),
            ("10.0.0.1", "private IP"),
            ("172.16.0.1", "private IP"),
            ("127.0.0.1", "loopback"),
            ("::1", "IPv6 loopback"),
            ("169.254.1.1", "link-local"),
            ("fe80::1", "IPv6 link-local"),
            ("not-an-ip", "malformed"),
            ("192.168.1.1, 10.0.0.1", "multiple IPs"),
        ],
    )
    async def test_rejects_invalid_ip_with_422(self, mock_asgi_app, invalid_ip, reason):
        """Test that requests with invalid IPs are rejected with 422."""
        app, app_result = mock_asgi_app()
        middleware = RateLimitIPValidationMiddleware(app)

        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"x-real-ip", invalid_ip.encode("latin-1")),
            ]
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        with (
            patch("fides.api.util.rate_limit.is_rate_limit_enabled", True),
            patch(
                "fides.api.util.rate_limit.CONFIG.security.rate_limit_client_ip_header",
                "X-Real-IP",
            ),
        ):
            await middleware(scope, receive, capture)

        assert not app_result.called, (
            f"App should NOT be called for {reason}: {invalid_ip}"
        )
        assert capture.status == 422

        # Verify error response body
        response_body = json.loads(capture.body.decode("utf-8"))
        assert response_body["detail"] == "Invalid client IP header"

    async def test_skips_non_http_scopes(self, mock_asgi_app):
        """Test that non-HTTP scopes (websocket, lifespan) pass through."""
        app, app_result = mock_asgi_app()
        middleware = RateLimitIPValidationMiddleware(app)

        scope: Scope = {
            "type": "websocket",
            "path": "/ws",
        }

        async def receive() -> Message:
            return {"type": "websocket.connect"}

        capture = ResponseCapture()

        with patch("fides.api.util.rate_limit.is_rate_limit_enabled", True):
            await middleware(scope, receive, capture)

        assert app_result.called, "App should be called for non-HTTP scopes"

    async def test_header_name_case_insensitivity(self, mock_asgi_app):
        """Test that the middleware handles header names case-insensitively."""
        app, app_result = mock_asgi_app()
        middleware = RateLimitIPValidationMiddleware(app)

        # ASGI normalizes headers to lowercase, so even if config says "X-Real-IP",
        # the middleware should look for "x-real-ip" in the scope
        scope = create_http_scope(
            headers=[
                (b"host", b"localhost"),
                (b"x-real-ip", b"8.8.8.8"),  # lowercase as ASGI would provide
            ]
        )
        receive = create_body_receive(b"")
        capture = ResponseCapture()

        with (
            patch("fides.api.util.rate_limit.is_rate_limit_enabled", True),
            patch(
                "fides.api.util.rate_limit.CONFIG.security.rate_limit_client_ip_header",
                "X-Real-IP",  # Mixed case in config
            ),
        ):
            await middleware(scope, receive, capture)

        assert app_result.called, "Should handle case-insensitive header lookup"
        assert capture.status == 200
