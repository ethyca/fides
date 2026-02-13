"""
Pure ASGI middleware implementations for high-performance request processing.

These replace the BaseHTTPMiddleware-based implementations which have significant
performance overhead (see https://github.com/fastapi/fastapi/discussions/6985).
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
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
from fides.api.middleware import handle_audit_log_resource
from fides.api.schemas.analytics import Event, ExtraData
from fides.api.util.endpoint_utils import API_PREFIX
from fides.api.util.logger import _log_exception
from fides.config import CONFIG

# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class BaseASGIMiddleware(ABC):
    """
    Lightweight base class for pure ASGI HTTP middleware.

    Subclasses implement `handle_http()` instead of `__call__()` to avoid
    boilerplate. Only HTTP requests reach `handle_http()`; other scope types
    pass through automatically.

    Provides helper methods for common operations like header extraction,
    status code capture, and response sending.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        await self.handle_http(scope, receive, send)

    @abstractmethod
    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Override this to implement HTTP middleware logic."""

    # --- Helper Methods ---

    @staticmethod
    def get_headers(scope: Scope) -> dict[bytes, bytes]:
        """Return headers as a dict for easy lookup."""
        return dict(scope.get("headers", []))

    @staticmethod
    def get_header(scope: Scope, name: bytes, default: str = "") -> str:
        """Get a single header value, decoded as latin-1."""
        headers = dict(scope.get("headers", []))
        return headers.get(name, b"").decode("latin-1") or default

    @staticmethod
    def get_method(scope: Scope) -> str:
        """Get the HTTP method from scope."""
        return scope.get("method", "UNKNOWN")

    @staticmethod
    def get_path(scope: Scope) -> str:
        """Get the request path from scope."""
        return scope.get("path", "/")

    @staticmethod
    def get_host(scope: Scope) -> Optional[str]:
        """Get hostname without port from the Host header."""
        headers = dict(scope.get("headers", []))
        host = headers.get(b"host", b"").decode("latin-1")
        return host.split(":")[0] if host else None

    @staticmethod
    def get_host_with_port(scope: Scope) -> str:
        """Get full host header value including port."""
        headers = dict(scope.get("headers", []))
        return headers.get(b"host", b"").decode("latin-1")

    @staticmethod
    def build_url(scope: Scope) -> str:
        """Build the full request URL from scope."""
        scheme = scope.get("scheme", "http")
        headers = dict(scope.get("headers", []))
        host = headers.get(b"host", b"").decode("latin-1")
        path = scope.get("path", "/")
        query = scope.get("query_string", b"").decode("latin-1")
        url = f"{scheme}://{host}{path}"
        return f"{url}?{query}" if query else url

    @staticmethod
    def status_capturing_send(send: Send) -> tuple[Callable[[], int], Send]:
        """
        Return a (get_status, wrapped_send) tuple.

        Call get_status() after the request completes to retrieve the captured
        status code. Defaults to 500 if no response was sent.
        """
        captured = {"status": 500}

        async def wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                captured["status"] = message.get("status", 500)
            await send(message)

        return lambda: captured["status"], wrapper

    @staticmethod
    async def send_response(
        send: Send,
        status: int,
        body: bytes,
        content_type: bytes = b"text/plain",
    ) -> None:
        """Send a complete HTTP response."""
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", content_type),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    @staticmethod
    async def send_html(send: Send, status: int, html: str) -> None:
        """Send an HTML response."""
        body = html.encode("utf-8")
        await BaseASGIMiddleware.send_response(
            send, status, body, b"text/html; charset=utf-8"
        )


class LogRequestMiddleware(BaseASGIMiddleware):
    """
    Pure ASGI middleware that logs basic information about every request.

    Logs: method, status_code, handler_time, path, fides_client header
    """

    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        start_time = perf_counter()
        method = self.get_method(scope)
        path = self.get_path(scope)
        fides_client = self.get_header(scope, b"fides-client", "unknown")

        get_status, wrapped_send = self.status_capturing_send(send)
        status_code = 500

        try:
            await self.app(scope, receive, wrapped_send)
            status_code = get_status()
        except Exception as e:
            logger.exception(f"Unhandled exception processing request: '{e}'")
            await self.send_response(send, 500, b"Internal Server Error")
            status_code = 500

        handler_time = round((perf_counter() - start_time) * 1000, 3)

        logger.bind(
            method=method,
            status_code=status_code,
            handler_time=f"{handler_time}ms",
            path=path,
            fides_client=fides_client,
        ).info("Request received")


class AnalyticsLoggingMiddleware(BaseASGIMiddleware):
    """
    Pure ASGI middleware that logs analytics events for each call to Fides endpoints.

    Only logs for API endpoints (paths starting with API_PREFIX) and skips /health endpoints.
    """

    # Class-level set to hold references to pending tasks, preventing garbage collection
    # before completion. Tasks remove themselves from this set when done.
    _pending_tasks: set[asyncio.Task] = set()

    def __init__(self, app: ASGIApp, api_prefix: str = API_PREFIX) -> None:
        super().__init__(app)
        self.api_prefix = api_prefix

    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = self.get_path(scope)

        # Skip non-API endpoints and health endpoints
        if not path.startswith(self.api_prefix) or path.endswith("/health"):
            await self.app(scope, receive, send)
            return

        method = self.get_method(scope)
        fides_source: Optional[str] = self.get_header(scope, b"x-fides-source") or None
        hostname = self.get_host(scope)
        full_url = self.build_url(scope)

        now = datetime.now(tz=timezone.utc)
        endpoint = f"{method}: {full_url}"

        # Capture status and detect HTTP errors
        captured: dict[str, Any] = {"status": 500, "error_class": None}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_code: int = message.get("status", 500)
                captured["status"] = status_code
                if status_code >= 400:
                    captured["error_class"] = "HTTPException"
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            captured["status"] = 500
            captured["error_class"] = e.__class__.__name__
            _log_exception(e, CONFIG.dev_mode)
            raise
        finally:
            # Schedule analytics logging as a background task.
            # Store task reference to prevent garbage collection before completion.
            task = asyncio.create_task(
                self._log_analytics(
                    endpoint,
                    hostname,
                    captured["status"],
                    now,
                    fides_source,
                    captured["error_class"],
                )
            )
            self._pending_tasks.add(task)
            # Task will be passed as argument to discard when it completes
            task.add_done_callback(self._pending_tasks.discard)

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


class AuditLogMiddleware(BaseASGIMiddleware):
    """
    Pure ASGI middleware that logs audit information for non-GET requests.

    This middleware buffers the request body to allow audit logging while
    still making the body available to downstream handlers.
    """

    def __init__(self, app: ASGIApp, ignored_paths: Optional[Set[str]] = None) -> None:
        super().__init__(app)
        self.ignored_paths = ignored_paths or {f"{API_PREFIX}/login"}

    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        method = self.get_method(scope)
        path = self.get_path(scope)

        # Only audit non-GET requests that aren't in the ignored list
        should_audit = (
            method != "GET"
            and path not in self.ignored_paths
            and CONFIG.security.enable_audit_log_resource_middleware
        )

        if not should_audit:
            await self.app(scope, receive, send)
            return

        # Buffer the request body as it's consumed by the downstream app
        body_parts: list[bytes] = []

        async def receiving_wrapper() -> Message:
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    body_parts.append(body)
            return message

        # Let the downstream app process the request
        await self.app(scope, receiving_wrapper, send)

        # After the request is complete, do audit logging with the buffered body
        full_body = b"".join(body_parts)
        try:

            async def body_receive() -> Message:
                return {
                    "type": "http.request",
                    "body": full_body,
                    "more_body": False,
                }

            request = Request(scope, body_receive, send)
            await handle_audit_log_resource(request)
        except Exception as exc:
            logger.debug(exc)


class ProfileRequestMiddleware(BaseASGIMiddleware):
    """
    Pure ASGI middleware for profiling requests using pyinstrument.

    Only active when the 'profile-request' header is present.
    Should only be used in dev mode.

    When profiling is active, the original response is replaced with an HTML
    page showing the profiling results.
    """

    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        profiling = self.get_header(scope, b"profile-request")

        if not profiling:
            await self.app(scope, receive, send)
            return

        # Profile the request
        profiler = Profiler(interval=0.001, async_mode="enabled")
        profiler.start()

        # Intercept send to discard the original response
        async def discard_send(message: Message) -> None:
            pass

        try:
            await self.app(scope, receive, discard_send)
        finally:
            profiler.stop()
            logger.debug("Request Profiled!")

        # Send the profiling HTML as the response
        await self.send_html(send, 200, profiler.output_html())
