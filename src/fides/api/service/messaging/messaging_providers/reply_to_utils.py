"""Reply-to address utilities for correspondence threading.

Consumed by CorrespondenceService (ENG-3299) to generate unique reply-to
addresses for outbound correspondence emails and store the token for
inbound reply matching.
"""

import secrets


def generate_reply_to_token() -> str:
    """Generate a cryptographically random 32-hex-char token (128 bits)."""
    return secrets.token_hex(16)


def format_reply_to_address(
    token: str,
    domain: str,
    use_plus_addressing: bool = True,
) -> str:
    """Format a reply-to address using plus addressing or dedicated subdomain."""
    if use_plus_addressing:
        return f"reply+{token}@replies.{domain}"
    return f"{token}@replies.{domain}"
