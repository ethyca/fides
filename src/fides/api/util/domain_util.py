"""Shared helpers for domain-validation logic."""

import os
import re
from typing import List

from loguru import logger

from fides.api.common_exceptions import DomainValidationError
from fides.config import CONFIG
from fides.config.security_settings import DomainValidationMode

_DOMAIN_MODE_ENV_VAR = "FIDES__SECURITY__DOMAIN_VALIDATION_MODE"


def get_domain_validation_mode() -> DomainValidationMode:
    """Return the effective domain validation mode, accounting for dev_mode.

    In dev mode, defaults to ``enabled`` so that integration developers catch
    domain-validation errors early — unless the env var is explicitly set, in
    which case the explicit value is respected.
    """
    if CONFIG.dev_mode and _DOMAIN_MODE_ENV_VAR not in os.environ:
        return DomainValidationMode.enabled
    return CONFIG.security.domain_validation_mode


def wildcard_to_regex(pattern: str) -> str:
    """
    Convert a wildcard pattern (using ``*``) into a regex string.

    The conversion escapes every regex-special character first, then
    replaces the escaped ``\\*`` tokens with ``[a-zA-Z0-9._-]+`` so that
    each ``*`` in the original pattern matches one or more valid hostname
    characters only.  This prevents ``*.example.com`` from matching the
    bare ``.example.com`` (leading dot, no subdomain) and also prevents
    path-injection attacks like ``badactor.com/fake.example.com``.
    """
    escaped = re.escape(pattern)
    return escaped.replace(r"\*", "[a-zA-Z0-9._-]+")


def validate_value_against_allowed_list(
    value: str,
    allowed_values: List[str],
    param_name: str,
    mode: DomainValidationMode = DomainValidationMode.monitor,
) -> None:
    """
    Validate that a value matches at least one of the allowed patterns.

    Each entry in allowed_values is a wildcard pattern that is matched
    case-insensitively against the full value string.  The only special
    character is ``*`` which matches one or more valid hostname characters
    (letters, digits, hyphens, dots, underscores).  Everything else is treated as a
    literal.

    An empty ``allowed_values`` list means the param is self-hosted and any
    value is permitted.

    Examples:
      - Exact: "api.stripe.com"
      - Subdomain wildcard: "*.salesforce.com"
      - Any position: "api.*.stripe.com"

    When ``mode`` is ``monitor``, logs a warning instead of raising.
    Raises ValueError if the value does not match any allowed pattern
    and ``mode`` is ``enabled``.
    """
    if not allowed_values:
        return

    value_stripped = value.strip()
    for pattern in allowed_values:
        pattern_stripped = pattern.strip()
        regex = wildcard_to_regex(pattern_stripped)
        if re.fullmatch(regex, value_stripped, re.IGNORECASE):
            return

    violation_msg = (
        f"The value '{value}' for '{param_name}' is not in the list of "
        f"allowed values: [{', '.join(allowed_values)}]."
    )

    if mode == DomainValidationMode.monitor:
        logger.warning(
            f"Domain validation violation (enforcement mode - monitor): {violation_msg}"
        )
        return

    logger.error(
        f"Domain validation violation (enforcement mode - enabled): {violation_msg}"
    )
    logger.info(
        "You may change the domain validation behavior by setting the environment variable "
        f"{_DOMAIN_MODE_ENV_VAR} to 'monitor' (log warnings only) or 'disabled' (skip validation)."
    )
    raise DomainValidationError(violation_msg)
