from __future__ import annotations

from datetime import datetime

from jose import jwe


def extract_payload(jwe_string: str, encryption_key: str) -> str:
    """Given a jwe, extracts the payload and returns it in string form."""
    return jwe.decrypt(jwe_string, encryption_key)


def is_token_expired(issued_at: datetime | None, token_duration_min: int) -> bool:
    """Returns True if the datetime is earlier than token_duration_min ago."""
    if not issued_at:
        return True

    return (datetime.now() - issued_at).total_seconds() / 60.0 > token_duration_min
