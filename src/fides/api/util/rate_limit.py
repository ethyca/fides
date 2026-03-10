from __future__ import annotations

import json
from ipaddress import ip_address
from typing import Optional

from fastapi import Request
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address  # type: ignore

from fides.api.asgi_middleware import BaseASGIMiddleware, Receive, Scope, Send
from fides.config import CONFIG


class InvalidClientIPError(Exception):
    def __init__(self, detail: str, header_value: str, header_name: str):
        self.detail = detail
        self.header_value = header_value
        self.header_name = header_name
        super().__init__(detail)


def validate_client_ip(ip: Optional[str]) -> bool:
    """
    Returns true if the provided ip is valid and not from a reserved range.
    Returns false otherwise.
    """
    if not ip:
        return False
    try:
        ip_obj = ip_address(ip)
        if (
            ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_multicast
            or ip_obj.is_private
        ):
            return False
        return True
    except ValueError:
        return False


def _extract_hostname_from_ip(ip: str) -> Optional[str]:
    """
    Extract hostname/IP address from header value, stripping port if present.

    Simple string-based approach following the reference implementation pattern.
    Does not validate whether the result is a valid IP address.

    Examples:
        # IPv4 cases
        _extract_hostname_from_ip("192.168.1.1") -> "192.168.1.1"
        _extract_hostname_from_ip("192.168.1.1:8080") -> "192.168.1.1"

        # IPv6 cases
        _extract_hostname_from_ip("2001:db8::1") -> "2001:db8::1"
        _extract_hostname_from_ip("[2001:db8::1]:8080") -> "2001:db8::1"

        # Edge cases (alidation will later reject)
        _extract_hostname_from_ip("192.168.1.1, 192.168.1.2") -> "192.168.1.1, 192.168.1.2"
        _extract_hostname_from_ip("not-an-ip:8080") -> "not-an-ip"

        # Error
        _extract_hostname_from_ip("") -> raises ValueError

    Raises:
        ValueError: If no hostname can be extracted from the input
    """

    clean_ip = ip.strip()

    if not clean_ip:
        raise ValueError("Could not parse IP from header value")

    # Handle IPv6 with port: [IPv6]:port
    if "]:" in clean_ip:
        return clean_ip.split("]:")[0].replace("[", "").strip()

    # Handle IPv4 with port: IPv4:port
    if ":" in clean_ip and "::" not in clean_ip:
        return clean_ip.split(":")[0].strip()

    # Return as-is (IPv6 without port, IPv4 without port, or other values)
    return clean_ip


def extract_and_validate_ip(ip_value: str) -> tuple[bool, Optional[str]]:
    """
    Extract and validate an IP from a header value.

    Returns (is_valid, extracted_ip). If invalid, extracted_ip is None.
    This is shared logic used by both the ASGI middleware and SlowAPI key function.
    """
    try:
        extracted_ip = _extract_hostname_from_ip(ip_value)
        if extracted_ip and validate_client_ip(extracted_ip):
            return True, extracted_ip
        return False, None
    except ValueError:
        return False, None


def _resolve_client_ip_from_header(request: Request, strict: bool) -> str:
    """Shared resolver for client IP from the configured header.

    - When strict=True: raise InvalidClientIPError on invalid/malformed header values.
    - When strict=False: never raise; fall back to the connection source IP.
    """
    header_name = CONFIG.security.rate_limit_client_ip_header
    if not header_name:
        # This line should never be reached when rate limiting is enabled
        logger.warning(
            "Rate limit client IP header not configured. Falling back to source IP.",
            header_name,
        )
        return get_remote_address(request)

    ip_address_from_header = request.headers.get(header_name)
    if not ip_address_from_header:
        logger.debug(
            "Rate limit header '{}' not found. Falling back to source IP.",
            header_name,
        )
        return get_remote_address(request)

    # Extract and validate IP using shared helper
    is_valid, extracted_ip = extract_and_validate_ip(ip_address_from_header)
    if is_valid and extracted_ip:
        return extracted_ip

    if strict:
        logger.error(
            "Invalid IP '{}' in header '{}'. Rejecting request.",
            ip_address_from_header,
            header_name,
        )
        raise InvalidClientIPError(
            detail="Invalid IP address format",
            header_value=ip_address_from_header,
            header_name=header_name,
        )
    # Non-strict path: fall back silently to source IP
    return get_remote_address(request)


def safe_rate_limit_key(request: Request) -> str:
    """
    Safe key function for SlowAPI limiter.

    Must never raise. If the configured header is missing or malformed,
    fall back to the connection source IP for rate limiting purposes.
    """
    return _resolve_client_ip_from_header(request, strict=False)


class RateLimitIPValidationMiddleware(BaseASGIMiddleware):
    """
    Pure ASGI middleware to pre-validate the configured client IP header when rate limiting is enabled.

    If the header is present but invalid, short-circuit the request with 422.
    This keeps SlowAPI's middleware path free of exceptions from the key function.

    This is a high-performance replacement for the BaseHTTPMiddleware-based version.
    """

    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not is_rate_limit_enabled:
            await self.app(scope, receive, send)
            return

        # Check if the IP header is present and valid
        header_name = CONFIG.security.rate_limit_client_ip_header
        if header_name:
            header_name_bytes = header_name.lower().encode("latin-1")
            ip_address_str = self.get_header(scope, header_name_bytes)

            if ip_address_str:
                is_valid, _ = extract_and_validate_ip(ip_address_str)
                if not is_valid:
                    logger.error(
                        "Invalid IP '{}' in header '{}'. Rejecting request.",
                        ip_address_str,
                        header_name,
                    )
                    body = json.dumps({"detail": "Invalid client IP header"}).encode(
                        "utf-8"
                    )
                    await self.send_response(send, 422, body, b"application/json")
                    return

        await self.app(scope, receive, send)


# Used for rate limiting with Slow API
# Decorate individual routes to deviate from the default rate limits
is_rate_limit_enabled = (
    CONFIG.security.rate_limit_client_ip_header is not None
    and CONFIG.security.rate_limit_client_ip_header != ""
)

disabled_limiter = Limiter(
    default_limits=[CONFIG.security.request_rate_limit],
    headers_enabled=True,
    key_prefix=CONFIG.security.rate_limit_prefix,
    key_func=safe_rate_limit_key,
    retry_after="http-date",
    enabled=False,
)

try:
    if is_rate_limit_enabled:
        fides_limiter = Limiter(
            storage_uri=CONFIG.redis.connection_url_unencoded,
            application_limits=[
                CONFIG.security.request_rate_limit
            ],  # Creates ONE shared bucket for all endpoints
            headers_enabled=True,
            key_prefix=CONFIG.security.rate_limit_prefix,
            key_func=safe_rate_limit_key,
            retry_after="http-date",
            in_memory_fallback_enabled=False,  # Fall back to no rate limiting if Redis unavailable
            enabled=is_rate_limit_enabled,
        )
    else:
        fides_limiter = disabled_limiter
except Exception as e:
    logger.exception("Error instantiating rate limiter: {}", e)
    if is_rate_limit_enabled:
        raise e
