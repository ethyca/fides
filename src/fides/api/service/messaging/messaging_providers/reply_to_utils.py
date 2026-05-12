"""Reply-to address utilities for correspondence threading.

Generates unique reply-to addresses for outbound correspondence emails
and stores the token for inbound reply matching.
"""

import re
import secrets

# Prevent email header injection — tokens must be hex-only, domains must be
# alphanumeric with dots/hyphens. Rejects newlines, spaces, and @ characters
# that could alter the address structure.
_SAFE_TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
_SAFE_DOMAIN_RE = re.compile(r"^(?!.*\.\.)[a-zA-Z0-9]([a-zA-Z0-9.\-]*[a-zA-Z0-9])$")


def generate_reply_to_token() -> str:
    """Generate a cryptographically random 32-hex-char token (128 bits)."""
    return secrets.token_hex(16)


def format_reply_to_address(
    token: str,
    domain: str,
    use_plus_addressing: bool = True,
) -> str:
    """Format a reply-to address using plus addressing or dedicated subdomain."""
    if not token or not _SAFE_TOKEN_RE.fullmatch(token):
        raise ValueError(f"Invalid reply-to token: {token!r}")
    if not domain or not _SAFE_DOMAIN_RE.fullmatch(domain):
        raise ValueError(f"Invalid reply-to domain: {domain!r}")
    if use_plus_addressing:
        return f"reply+{token}@replies.{domain}"
    return f"{token}@replies.{domain}"
