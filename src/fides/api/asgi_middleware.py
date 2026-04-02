"""
Pure ASGI middleware implementations for high-performance request processing.

These replace the BaseHTTPMiddleware-based implementations which have significant
performance overhead (see https://github.com/fastapi/fastapi/discussions/6985).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, Awaitable, Callable, MutableMapping, Optional, Set
from uuid import uuid4

from loguru import logger
from pyinstrument import Profiler
from starlette.requests import Request

from fides.api.middleware import handle_audit_log_resource
from fides.api.request_context import set_request_id
from fides.api.util.endpoint_utils import API_PREFIX
from fides.config import CONFIG

# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

# Alphanumeric, hyphens, underscores, dots, max 128 chars.
_REQUEST_ID_RE = re.compile(r"^[\w\-.]{1,128}$")


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
    def header_injecting_send(send: Send, extra_headers: dict[bytes, bytes]) -> Send:
        """Wrap ``send`` to append headers to the response.

        The headers are added when the ``http.response.start`` message passes
        through.  Body messages are forwarded unchanged.
        """

        async def wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(extra_headers.items())
                message["headers"] = headers
            await send(message)

        return wrapper

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

        # Read or generate a request ID for log correlation.
        # Validate the client-supplied value to prevent log injection.
        request_id_header = self.get_header(scope, b"x-request-id")
        request_id = (
            request_id_header
            if request_id_header and _REQUEST_ID_RE.match(request_id_header)
            else str(uuid4())
        )
        set_request_id(request_id)

        # Inject response headers, then wrap with status capture
        send_with_headers = self.header_injecting_send(
            send, {b"x-request-id": request_id.encode("latin-1")}
        )
        get_status, wrapped_send = self.status_capturing_send(send_with_headers)

        status_code = 500

        try:
            await self.app(scope, receive, wrapped_send)
            status_code = get_status()
        except Exception as e:
            logger.exception(f"Unhandled exception processing request: '{e}'")
            await self.send_response(send_with_headers, 500, b"Internal Server Error")
            status_code = 500

        handler_time = round((perf_counter() - start_time) * 1000, 3)

        logger.bind(
            method=method,
            status_code=status_code,
            handler_time=f"{handler_time}ms",
            path=path,
            fides_client=fides_client,
        ).info("Request received")


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
