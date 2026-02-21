"""Shared helpers for domain-validation logic.

This module exists to avoid circular imports between saas_config.py
(which defines ConnectorParam / SaaSConfig) and saas_util.py (which
imports SaaSConfig).  Both modules can safely import from here.
"""

import re


def wildcard_to_regex(pattern: str) -> str:
    """
    Convert a wildcard pattern (using ``*``) into a regex string.

    The conversion escapes every regex-special character first, then
    replaces the escaped ``\\*`` tokens with ``.*`` so that each ``*``
    in the original pattern matches any sequence of characters
    (including dots and empty strings).
    """
    escaped = re.escape(pattern)
    return escaped.replace(r"\*", ".*")
