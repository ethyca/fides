import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, List, MutableMapping, Set, Tuple

from fides.config import CONFIG

apply_recommended_headers = CONFIG.security.headers_mode == "recommended"


def is_exact_match(matcher: re.Pattern[str], path_name: str) -> bool:
    matched_content = re.fullmatch(matcher, path_name)
    return matched_content is not None


HeaderDefinition = tuple[str, str]


@dataclass
class HeaderRule:
    matcher: re.Pattern[str]
    headers: list[HeaderDefinition]


recommended_csp_header_value = re.sub(
    r"\s{2,}",
    " ",
    """
        default-src 'self';
        script-src 'self' 'unsafe-inline';
        style-src 'self' 'unsafe-inline';
        connect-src 'self';
        img-src 'self' blob: data:;
        font-src 'self';
        object-src 'none';
        base-uri 'self';
        form-action 'self';
        frame-ancestors 'self';
        upgrade-insecure-requests;
    """,
).strip()

recommended_headers: list[HeaderRule] = [
    HeaderRule(
        matcher=re.compile(r"/.*"),
        headers=[
            ("X-Content-Type-Options", "nosniff"),
            ("Strict-Transport-Security", "max-age=31536000"),
        ],
    ),
    HeaderRule(
        matcher=re.compile(r"^/((?!api|health).*)"),
        headers=[
            (
                "Content-Security-Policy",
                recommended_csp_header_value,
            ),
            ("X-Frame-Options", "SAMEORIGIN"),
        ],
    ),
]


def get_applicable_header_rules(
    path: str, header_rules: list[HeaderRule]
) -> list[HeaderDefinition]:
    header_names: set[str] = set()
    header_definitions: list[HeaderDefinition] = []

    for rule in header_rules:
        if is_exact_match(rule.matcher, path):
            for header in rule.headers:
                [header_name, _] = header
                if header_name not in header_names:
                    header_names.add(header_name)
                    header_definitions.append(header)

    return header_definitions


# Type aliases for ASGI
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class SecurityHeadersMiddleware:
    """
    Pure ASGI middleware that controls what security headers are included in Fides API responses.

    This is a high-performance replacement for the BaseHTTPMiddleware-based version.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not apply_recommended_headers:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")
        applicable_headers = get_applicable_header_rules(path, recommended_headers)

        # If no headers to add, just pass through
        if not applicable_headers:
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Get existing headers
                headers: List[Tuple[bytes, bytes]] = list(message.get("headers", []))

                # Track existing header names (lowercase for case-insensitive comparison)
                existing_names: Set[bytes] = {h[0].lower() for h in headers}

                # Add our security headers if not already present
                for header_name, header_value in applicable_headers:
                    header_name_bytes = header_name.lower().encode("latin-1")
                    if header_name_bytes not in existing_names:
                        headers.append(
                            (
                                header_name.encode("latin-1"),
                                header_value.encode("latin-1"),
                            )
                        )

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_wrapper)
