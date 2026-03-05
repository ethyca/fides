"""Shared fixtures for middleware tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, MutableMapping, Optional, Tuple

import pytest

# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


@dataclass
class MockAppResult:
    """Tracks what happened during mock app execution."""

    called: bool = False
    response_sent: bool = False
    received_body: bytes = b""
    scope: Optional[Scope] = None
    headers_sent: List[Tuple[bytes, bytes]] = field(default_factory=list)


def create_mock_asgi_app(
    status: int = 200,
    body: bytes = b"{}",
    headers: Optional[List[Tuple[bytes, bytes]]] = None,
    delay: float = 0,
    exception: Optional[Exception] = None,
    capture_body: bool = False,
) -> Tuple[ASGIApp, MockAppResult]:
    """
    Factory for creating mock ASGI apps for middleware testing.

    Args:
        status: HTTP status code to return
        body: Response body
        headers: Response headers (defaults to JSON content-type)
        delay: Artificial delay in seconds before responding
        exception: Exception to raise instead of responding
        capture_body: Whether to read and capture the request body

    Returns:
        Tuple of (mock_app, result) where result tracks execution
    """
    if headers is None:
        headers = [(b"content-type", b"application/json")]

    result = MockAppResult()

    async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
        result.called = True
        result.scope = scope

        # Capture request body if requested
        if capture_body:
            body_parts = []
            while True:
                message = await receive()
                chunk = message.get("body", b"")
                if chunk:
                    body_parts.append(chunk)
                if not message.get("more_body", False):
                    break
            result.received_body = b"".join(body_parts)

        # Artificial delay
        if delay > 0:
            await asyncio.sleep(delay)

        # Raise exception if configured
        if exception:
            raise exception

        # Send response
        result.headers_sent = list(headers)
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )
        result.response_sent = True

    return mock_app, result


@pytest.fixture
def mock_asgi_app():
    """Fixture that returns the factory function for creating mock ASGI apps."""
    return create_mock_asgi_app


@pytest.fixture
def simple_200_app():
    """Returns a simple mock app that returns 200 OK."""
    return create_mock_asgi_app()


# Helper functions for creating common test components


def create_http_scope(
    method: str = "GET",
    path: str = "/test",
    headers: Optional[List[Tuple[bytes, bytes]]] = None,
    query_string: bytes = b"",
    scheme: str = "http",
) -> Scope:
    """Create a standard HTTP scope for testing."""
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers or [],
        "query_string": query_string,
        "scheme": scheme,
    }


def create_body_receive(body: bytes) -> Receive:
    """Create a receive callable that returns a single body chunk."""
    called = False

    async def receive() -> Message:
        nonlocal called
        if not called:
            called = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive


def create_chunked_receive(chunks: List[bytes]) -> Receive:
    """Create a receive callable that returns body in multiple chunks."""
    index = 0

    async def receive() -> Message:
        nonlocal index
        if index < len(chunks):
            chunk = chunks[index]
            index += 1
            more = index < len(chunks)
            return {"type": "http.request", "body": chunk, "more_body": more}
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive


async def noop_send(message: Message) -> None:
    """A no-op send callable for tests that don't need to inspect responses."""
    pass


class ResponseCapture:
    """Captures response messages sent through the send callable."""

    def __init__(self):
        self.messages: List[Message] = []
        self.status: Optional[int] = None
        self.headers: List[Tuple[bytes, bytes]] = []
        self.body_parts: List[bytes] = []

    async def __call__(self, message: Message) -> None:
        self.messages.append(message)
        if message["type"] == "http.response.start":
            self.status = message.get("status")
            self.headers = list(message.get("headers", []))
        elif message["type"] == "http.response.body":
            body = message.get("body", b"")
            if body:
                self.body_parts.append(body)

    @property
    def body(self) -> bytes:
        return b"".join(self.body_parts)


@pytest.fixture
def response_capture():
    """Fixture that returns a fresh ResponseCapture instance."""
    return ResponseCapture()
