"""
Pure ASGI middleware implementations for high-performance request processing.

These replace the BaseHTTPMiddleware-based implementations which have significant
performance overhead (see https://github.com/fastapi/fastapi/discussions/6985).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Awaitable, Callable, MutableMapping, Optional, Set

from fideslog.sdk.python.event import AnalyticsEvent
from loguru import logger
from pyinstrument import Profiler
from starlette.requests import Request

from fides.api.analytics import (
    accessed_through_local_host,
    in_docker_container,
    send_analytics_event,
)
from fides.api.middleware import handle_audit_log_resource, set_body
from fides.api.schemas.analytics import Event, ExtraData
from fides.api.util.logger import _log_exception
from fides.config import CONFIG

# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class LogRequestMiddleware:
    """
    Pure ASGI middleware that logs basic information about every request handled by the server.

    Logs: method, status_code, handler_time, path, fides_client header
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = perf_counter()
        status_code = 500  # Default in case of exception

        # Extract request info from scope
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        # Get Fides-Client header
        headers = dict(scope.get("headers", []))
        fides_client = headers.get(b"fides-client", b"unknown").decode("latin-1")

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.exception(f"Unhandled exception processing request: '{e}'")
            # Send a 500 response
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"text/plain")],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"Internal Server Error",
                }
            )
            status_code = 500

        # Calculate handler time in milliseconds
        handler_time = round((perf_counter() - start_time) * 1000, 3)

        logger.bind(
            method=method,
            status_code=status_code,
            handler_time=f"{handler_time}ms",
            path=path,
            fides_client=fides_client,
        ).info("Request received")


class AnalyticsLoggingMiddleware:
    """
    Pure ASGI middleware that logs analytics events for each call to Fides endpoints.

    Only logs for API endpoints (paths starting with /api/v1) and skips /health endpoints.
    """

    def __init__(self, app: ASGIApp, api_prefix: str = "/api/v1") -> None:
        self.app = app
        self.api_prefix = api_prefix

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")

        # Skip non-API endpoints and health endpoints
        if not path.startswith(self.api_prefix) or path.endswith("/health"):
            await self.app(scope, receive, send)
            return

        # Extract request info
        method = scope.get("method", "UNKNOWN")
        headers = dict(scope.get("headers", []))
        fides_source: Optional[str] = (
            headers.get(b"x-fides-source", b"").decode("latin-1") or None
        )

        # Get hostname from Host header, stripping port if present
        # Original used request.url.hostname which is just the domain (no port)
        host_header = headers.get(b"host", b"").decode("latin-1")
        hostname = host_header.split(":")[0] if host_header else None

        # Build full URL for endpoint to match original behavior
        # Original: f"{request.method}: {request.url}"
        scheme = scope.get("scheme", "http")
        query_string = scope.get("query_string", b"").decode("latin-1")
        full_url = f"{scheme}://{host_header}{path}"
        if query_string:
            full_url = f"{full_url}?{query_string}"

        now = datetime.now(tz=timezone.utc)
        endpoint = f"{method}: {full_url}"

        status_code = 500  # Default
        error_class: Optional[str] = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, error_class
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                if status_code >= 400:
                    error_class = "HTTPException"
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            status_code = 500
            error_class = e.__class__.__name__
            # Log exception
            _log_exception(e, CONFIG.dev_mode)
            raise
        finally:
            # Schedule analytics logging as a background task
            asyncio.create_task(
                self._log_analytics(
                    endpoint, hostname, status_code, now, fides_source, error_class
                )
            )

    async def _log_analytics(
        self,
        endpoint: str,
        hostname: Optional[str],
        status_code: int,
        event_created_at: datetime,
        fides_source: Optional[str],
        error_class: Optional[str],
    ) -> None:
        """Log analytics event if not opted out."""
        if CONFIG.user.analytics_opt_out:
            return

        try:
            await send_analytics_event(
                AnalyticsEvent(
                    docker=in_docker_container(),
                    event=Event.endpoint_call.value,
                    event_created_at=event_created_at,
                    local_host=accessed_through_local_host(hostname),
                    endpoint=endpoint,
                    status_code=status_code,
                    error=error_class or None,
                    extra_data=(
                        {ExtraData.fides_source.value: fides_source}
                        if fides_source
                        else None
                    ),
                )
            )
        except Exception:
            # Analytics should never break the request
            pass


class AuditLogMiddleware:
    """
    Pure ASGI middleware that logs audit information for non-GET requests.

    This middleware buffers the request body to allow audit logging while
    still making the body available to downstream handlers.
    """

    def __init__(self, app: ASGIApp, ignored_paths: Optional[Set[str]] = None) -> None:
        self.app = app
        self.ignored_paths = ignored_paths or {"/api/v1/login"}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "/")

        # Only audit non-GET requests that aren't in the ignored list
        should_audit = (
            method != "GET"
            and path not in self.ignored_paths
            and CONFIG.security.enable_audit_log_resource_middleware
        )

        if should_audit:
            # Buffer the request body as it's consumed by the downstream app
            body_parts = []
            body_complete = False

            async def receiving_wrapper() -> Message:
                nonlocal body_complete
                message = await receive()

                if message["type"] == "http.request":
                    body = message.get("body", b"")
                    if body:
                        body_parts.append(body)

                    # Check if body is complete
                    if not message.get("more_body", False):
                        body_complete = True
                        # Trigger audit logging now that we have the full body
                        full_body = b"".join(body_parts)
                        try:
                            # Create a Request object for the audit handler
                            request = Request(scope, receive, send)
                            # Pre-set the body so handle_audit_log_resource doesn't consume it
                            await set_body(request, full_body)

                            await handle_audit_log_resource(request)
                        except Exception as exc:
                            logger.debug(exc)

                return message

            await self.app(scope, receiving_wrapper, send)
        else:
            await self.app(scope, receive, send)


class ProfileRequestMiddleware:
    """
    Pure ASGI middleware for profiling requests using pyinstrument.

    Only active when the 'profile-request' header is present.
    Should only be used in dev mode.

    When profiling is active, the original response is replaced with an HTML
    page showing the profiling results.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check for profile-request header
        headers = dict(scope.get("headers", []))
        profiling = headers.get(b"profile-request", b"").decode("latin-1")

        if not profiling:
            await self.app(scope, receive, send)
            return

        # Profile the request
        profiler = Profiler(interval=0.001, async_mode="enabled")
        profiler.start()

        # Intercept send to discard the original response
        async def send_wrapper(message: Message) -> None:
            # Discard the original response - we'll send profiling HTML instead
            pass

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            profiler.stop()
            logger.debug("Request Profiled!")

        # Send the profiling HTML as the response
        profile_html = profiler.output_html()

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/html; charset=utf-8"),
                    (b"content-length", str(len(profile_html)).encode("latin-1")),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": profile_html.encode("utf-8"),
            }
        )
