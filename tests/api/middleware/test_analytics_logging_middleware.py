# pylint: disable=missing-docstring, redefined-outer-name
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from fides.api.app_setup import create_fides_app
from fides.api.asgi_middleware import AnalyticsLoggingMiddleware
from fides.config import CONFIG

from .conftest import (
    Message,
    create_http_scope,
    noop_send,
)


class TestAnalyticsLoggingMiddleware:
    """
    Unit tests that directly verify the header extraction logic in AnalyticsLoggingMiddleware.

    ASGI servers normalize header names to lowercase as bytes, so this tests that
    the middleware correctly reads headers using the lowercased byte key.
    """

    def test_header_extraction_logic(self):
        """
        Direct test of the header extraction logic used in AnalyticsLoggingMiddleware.

        This replicates the exact code from the middleware to verify it works correctly
        with ASGI-style headers (lowercase bytes).
        """
        # Simulate ASGI headers as they would appear after normalization
        # ASGI spec: headers are a list of [name, value] pairs where both are bytes
        # Header names are lowercase per ASGI spec
        asgi_headers = [
            (b"host", b"localhost:8080"),
            (b"x-fides-source", b"privacy-center"),
            (b"content-type", b"application/json"),
        ]

        # This is the exact header extraction code from AnalyticsLoggingMiddleware.__call__
        headers = dict(asgi_headers)
        fides_source = headers.get(b"x-fides-source", b"").decode("latin-1") or None

        assert fides_source == "privacy-center", (
            f"Expected 'privacy-center', got '{fides_source}'. "
            "Header extraction logic is broken."
        )

    def test_header_extraction_missing_header(self):
        """Test that missing X-Fides-Source header returns None."""
        asgi_headers = [
            (b"host", b"localhost:8080"),
            (b"content-type", b"application/json"),
        ]

        headers = dict(asgi_headers)
        fides_source = headers.get(b"x-fides-source", b"").decode("latin-1") or None

        assert fides_source is None

    def test_header_extraction_empty_header(self):
        """Test that empty X-Fides-Source header returns None."""
        asgi_headers = [
            (b"host", b"localhost:8080"),
            (b"x-fides-source", b""),
        ]

        headers = dict(asgi_headers)
        fides_source = headers.get(b"x-fides-source", b"").decode("latin-1") or None

        assert fides_source is None

    async def test_middleware_extracts_header_directly(self, mock_asgi_app):
        """
        Integration test: Call the middleware directly with a mock ASGI app
        to verify X-Fides-Source header is extracted correctly.

        This bypasses TestClient complexity and tests the middleware in isolation.
        """
        captured_fides_source = None

        app, _ = mock_asgi_app()

        # Patch _log_analytics to capture the fides_source
        async def capturing_log_analytics(
            self,
            endpoint,
            hostname,
            status_code,
            event_created_at,
            fides_source,
            error_class,
        ):
            nonlocal captured_fides_source
            captured_fides_source = fides_source

        # Collect coroutines passed to create_task so we can await them after
        pending_coroutines = []

        def collect_coroutine(coro, *args, **kwargs):
            pending_coroutines.append(coro)
            # Return a dummy task-like object
            future = asyncio.get_event_loop().create_future()
            future.set_result(None)
            return future

        middleware = AnalyticsLoggingMiddleware(app)

        # Create an ASGI scope with X-Fides-Source header (lowercase, as ASGI normalizes)
        scope = create_http_scope(
            method="GET",
            path="/api/v1/config",
            headers=[
                (b"host", b"localhost:8080"),
                (b"x-fides-source", b"privacy-center"),  # ASGI normalizes to lowercase
            ],
        )

        messages_sent = []

        async def mock_receive():
            return {"type": "http.request", "body": b""}

        async def mock_send(message):
            messages_sent.append(message)

        with (
            patch.object(
                AnalyticsLoggingMiddleware, "_log_analytics", capturing_log_analytics
            ),
            patch("asyncio.create_task", side_effect=collect_coroutine),
        ):
            await middleware(scope, mock_receive, mock_send)

        # Now await the collected coroutines to run our capturing function
        for coro in pending_coroutines:
            await coro

        # Verify the header was correctly extracted
        assert captured_fides_source == "privacy-center", (
            f"Expected fides_source='privacy-center', got '{captured_fides_source}'. "
            "The middleware is not correctly extracting the X-Fides-Source header."
        )

    async def test_extracts_x_fides_source_header(self, mock_asgi_app):
        """
        Test that the middleware correctly extracts the X-Fides-Source header
        and includes it in the analytics event.
        """
        captured_analytics_event = None

        app, _ = mock_asgi_app()
        middleware = AnalyticsLoggingMiddleware(app)

        # Create scope with X-Fides-Source header (ASGI requires lowercase header names)
        scope = create_http_scope(
            method="POST",
            path="/api/v1/privacy-request",
            scheme="https",
            headers=[
                (b"host", b"example.com"),
                (b"x-fides-source", b"privacy-center"),
            ],
        )

        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        # Mock send_analytics_event to capture the AnalyticsEvent
        async def capture_analytics_event(event):
            nonlocal captured_analytics_event
            captured_analytics_event = event

        # Collect tasks created by asyncio.create_task so we can await them
        created_tasks = []
        original_create_task = asyncio.create_task

        def track_create_task(coro, *args, **kwargs):
            task = original_create_task(coro, *args, **kwargs)
            created_tasks.append(task)
            return task

        with (
            patch("fides.api.asgi_middleware.CONFIG.user.analytics_opt_out", False),
            patch(
                "fides.api.asgi_middleware.send_analytics_event",
                side_effect=capture_analytics_event,
            ),
            patch(
                "fides.api.asgi_middleware.asyncio.create_task",
                side_effect=track_create_task,
            ),
        ):
            await middleware(scope, receive, noop_send)
            # Wait for all background tasks to complete
            if created_tasks:
                await asyncio.gather(*created_tasks, return_exceptions=True)

        # Verify the analytics event was captured and contains the fides_source
        assert captured_analytics_event is not None
        assert captured_analytics_event.extra_data is not None
        assert (
            captured_analytics_event.extra_data.get("fides_source") == "privacy-center"
        )
        assert (
            captured_analytics_event.endpoint
            == "POST: https://example.com/api/v1/privacy-request"
        )
        assert captured_analytics_event.status_code == 200

    async def test_builds_full_url_for_endpoint(self, mock_asgi_app):
        """Test that the middleware builds the full URL including scheme, host, path, and query string."""
        captured_endpoint = None

        app, _ = mock_asgi_app()
        middleware = AnalyticsLoggingMiddleware(app)

        scope = create_http_scope(
            method="GET",
            path="/api/v1/privacy-request",
            scheme="https",
            query_string=b"page=1&size=50",
            headers=[(b"host", b"api.example.com:8080")],
        )

        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        with patch.object(
            middleware, "_log_analytics", new_callable=AsyncMock
        ) as mock_log:
            await middleware(scope, receive, noop_send)
            await asyncio.sleep(0.01)

            mock_log.assert_called_once()
            captured_endpoint = mock_log.call_args[0][0]

        # Verify full URL is built correctly
        assert (
            captured_endpoint
            == "GET: https://api.example.com:8080/api/v1/privacy-request?page=1&size=50"
        )

    async def test_extracts_hostname_without_port(self, mock_asgi_app):
        """Test that the middleware extracts hostname without port for accessed_through_local_host check."""
        captured_hostname = None

        app, _ = mock_asgi_app()
        middleware = AnalyticsLoggingMiddleware(app)

        # Host header includes port, path that won't be skipped
        scope = create_http_scope(
            method="GET",
            path="/api/v1/privacy-request",
            headers=[(b"host", b"localhost:8080")],
        )

        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        with patch.object(
            middleware, "_log_analytics", new_callable=AsyncMock
        ) as mock_log:
            await middleware(scope, receive, noop_send)
            await asyncio.sleep(0.01)

            mock_log.assert_called_once()
            # hostname is the second argument
            captured_hostname = mock_log.call_args[0][1]

        # Verify hostname is extracted without port
        assert captured_hostname == "localhost"

    async def test_skips_non_api_endpoints(self, mock_asgi_app):
        """Test that the middleware skips non-API endpoints."""
        app, _ = mock_asgi_app()
        middleware = AnalyticsLoggingMiddleware(app)

        # Non-API path
        scope = create_http_scope(
            method="GET",
            path="/static/js/app.js",
            headers=[(b"host", b"example.com")],
        )

        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        with patch.object(
            middleware, "_log_analytics", new_callable=AsyncMock
        ) as mock_log:
            await middleware(scope, receive, noop_send)
            await asyncio.sleep(0.01)

            # Should not be called for non-API paths
            mock_log.assert_not_called()

    async def test_skips_health_endpoints(self, mock_asgi_app):
        """Test that the middleware skips health check endpoints."""
        app, _ = mock_asgi_app()
        middleware = AnalyticsLoggingMiddleware(app)

        scope = create_http_scope(
            method="GET",
            path="/api/v1/health",
            headers=[(b"host", b"example.com")],
        )

        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        with patch.object(
            middleware, "_log_analytics", new_callable=AsyncMock
        ) as mock_log:
            await middleware(scope, receive, noop_send)
            await asyncio.sleep(0.01)

            # Should not be called for health endpoints
            mock_log.assert_not_called()

    def test_x_fides_source_header_e2e(self, owner_auth_header, monkeypatch):
        """
        E2E test: Verify that the X-Fides-Source header (sent with standard HTTP
        capitalization) is correctly extracted by the middleware during a real request.

        This test verifies the full chain:
        1. Client sends 'X-Fides-Source'
        2. ASGI server (Starlette/TestClient) normalizes it to 'x-fides-source'
        3. AnalyticsLoggingMiddleware extracts it correctly
        4. The value is passed to the analytics event
        """
        # Enable analytics for this test
        monkeypatch.setattr(CONFIG.user, "analytics_opt_out", False)

        # Create a minimal lifespan for testing (just yields without startup tasks)
        @asynccontextmanager
        async def test_lifespan(app):
            yield

        # Create a fresh app with analytics middleware enabled
        test_app = create_fides_app(lifespan=test_lifespan)

        captured_fides_source = None

        # Capture the fides_source argument when _log_analytics is called
        async def capturing_log_analytics(
            self,
            endpoint,
            hostname,
            status_code,
            event_created_at,
            fides_source,
            error_class,
        ):
            nonlocal captured_fides_source
            captured_fides_source = fides_source
            # Don't actually send analytics
            return

        # Force asyncio.create_task to run coroutines synchronously
        # This is needed because TestClient doesn't run background tasks
        def run_immediately(coro, *args, **kwargs):
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context, schedule it
                return asyncio.ensure_future(coro)
            else:
                # Run synchronously
                loop.run_until_complete(coro)
                # Return a completed future
                future = loop.create_future()
                future.set_result(None)
                return future

        with (
            patch.object(
                AnalyticsLoggingMiddleware, "_log_analytics", capturing_log_analytics
            ),
            patch(
                "fides.api.asgi_middleware.asyncio.create_task",
                side_effect=run_immediately,
            ),
        ):
            with TestClient(test_app) as client:
                # Send request with X-Fides-Source header using standard HTTP capitalization
                response = client.get(
                    "/api/v1/config",
                    headers={
                        **owner_auth_header,
                        "X-Fides-Source": "privacy-center",
                    },
                )
                assert response.status_code == 200

        # Verify the header was correctly extracted
        assert captured_fides_source == "privacy-center", (
            f"Expected fides_source='privacy-center', got '{captured_fides_source}'. "
            "The X-Fides-Source header was not correctly extracted during the E2E request."
        )
