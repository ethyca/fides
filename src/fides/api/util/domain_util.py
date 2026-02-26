"""Shared helpers for domain-validation logic."""

import re
from typing import List


def wildcard_to_regex(pattern: str) -> str:
    """
    Convert a wildcard pattern (using ``*``) into a regex string.

    The conversion escapes every regex-special character first, then
    replaces the escaped ``\\*`` tokens with ``.+`` so that each ``*``
    in the original pattern matches one or more characters (including
    dots).  This prevents ``*.example.com`` from matching the bare
    ``.example.com`` (leading dot, no subdomain).
    """
    escaped = re.escape(pattern)
    return escaped.replace(r"\*", ".+")


def validate_value_against_allowed_list(
    value: str, allowed_values: List[str], param_name: str
) -> None:
    """
    Validate that a value matches at least one of the allowed patterns.

    Each entry in allowed_values is a wildcard pattern that is matched
    case-insensitively against the full value string.  The only special
    character is ``*`` which matches any sequence of characters (including
    dots).  Everything else is treated as a literal.

    An empty ``allowed_values`` list means the param is self-hosted and any
    value is permitted.

    Examples:
      - Exact: "api.stripe.com"
      - Subdomain wildcard: "*.salesforce.com"
      - Any position: "api.*.stripe.com"

    Raises ValueError if the value does not match any allowed pattern.
    """
    if not allowed_values:
        return

    value_stripped = value.strip()
    for pattern in allowed_values:
        pattern_stripped = pattern.strip()
        regex = wildcard_to_regex(pattern_stripped)
        if re.fullmatch(regex, value_stripped, re.IGNORECASE):
            return
    raise ValueError(
        f"The value '{value}' for '{param_name}' is not in the list of "
        f"allowed values: [{', '.join(allowed_values)}]"
    )
