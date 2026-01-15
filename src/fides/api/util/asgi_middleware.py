"""
Pure ASGI middleware implementations for high-performance request processing.

These replace the BaseHTTPMiddleware-based implementations which have significant
performance overhead due to reading the entire request body into memory.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Awaitable, Callable, MutableMapping, Optional, Set

from loguru import logger

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

        # Get host from headers
        host = headers.get(b"host", b"").decode("latin-1")

        now = datetime.now(tz=timezone.utc)
        endpoint = f"{method}: {path}"

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
            raise
        finally:
            # Schedule analytics logging as a background task
            asyncio.create_task(
                self._log_analytics(
                    endpoint, host, status_code, now, fides_source, error_class
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
        # Avoid circular imports
        from fideslog.sdk.python.event import AnalyticsEvent

        from fides.api.analytics import (
            accessed_through_local_host,
            in_docker_container,
            send_analytics_event,
        )
        from fides.api.schemas.analytics import Event, ExtraData

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
            try:
                # We need to create a Request object for the audit handler
                # This is a lightweight operation compared to BaseHTTPMiddleware
                from starlette.requests import Request

                request = Request(scope, receive, send)
                from fides.api.middleware import handle_audit_log_resource

                await handle_audit_log_resource(request)
            except Exception as exc:
                logger.debug(exc)

        await self.app(scope, receive, send)


class ProfileRequestMiddleware:
    """
    Pure ASGI middleware for profiling requests using pyinstrument.

    Only active when the 'profile-request' header is present.
    Should only be used in dev mode.
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
        from pyinstrument import Profiler

        profiler = Profiler(interval=0.001, async_mode="enabled")
        profiler.start()

        try:
            await self.app(scope, receive, send)
        finally:
            profiler.stop()
            logger.debug("Request Profiled!")

        # Note: In the original implementation, this returned an HTMLResponse with the profile.
        # With pure ASGI, we've already started sending the response, so we just log it.
        # If you need the profile output, consider logging it or writing to a file.
