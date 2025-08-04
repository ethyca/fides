from __future__ import annotations

from ipaddress import ip_address

from fastapi import Request
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address  # type: ignore

from fides.config import CONFIG


def validate_client_ip(ip: str) -> bool:
    """Ensure IP is valid and not from a reserved range."""
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


def get_client_ip_from_header(request: Request) -> str:
    """
    Extracts the client IP from the configured CDN header.

    If the header is not configured or is missing, it falls back to the
    source IP on the request. The source IP is the client IP determined
    by Uvicorn for the TCP connection terminated on the Fides Webserver
    container.
    """
    header_name = CONFIG.security.rate_limit_client_ip_header
    if not header_name:
        # This line should never be reached as we prevent our rate-limiting middleware
        # from running if the header is not configured
        return get_remote_address(request)

    header_value = request.headers.get(header_name)
    if not header_value:
        logger.warning(
            "Rate limit header '{}' not found. Falling back to source IP.",
            header_name,
        )
        return get_remote_address(request)

    # We find the leftmost IP and strip the port if one is present e.g. 198.51.100.10:46532 will be treated as if the client IP is 198.51.100.10
    if ":" in header_value:
        ip = header_value.split(":")[0]
    else:
        ip = header_value

    if not validate_client_ip(ip):
        logger.warning(
            "Invalid IP '{}' in header '{}'. Falling back to source IP.",
            ip,
            header_name,
        )
        return get_remote_address(request)

    return ip


# Used for rate limiting with Slow API
# Decorate individual routes to deviate from the default rate limits
fides_limiter = Limiter(
    storage_uri=CONFIG.redis.connection_url,
    default_limits=[CONFIG.security.request_rate_limit],
    headers_enabled=True,
    key_prefix=CONFIG.security.rate_limit_prefix,
    key_func=get_client_ip_from_header,
    retry_after="http-date",
    in_memory_fallback_enabled=False,  # Fall back to no rate limiting if Redis unavailable
)
