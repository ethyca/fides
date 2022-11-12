"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from typing import List, Optional

from fideslib.core.config import SecuritySettings as FideslibSecuritySettings
from pydantic import validator
from slowapi.wrappers import parse_many  # type: ignore

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY

ENV_PREFIX = "FIDES__SECURITY__"


class SecuritySettings(FideslibSecuritySettings):
    """Configuration settings for Security variables."""

    root_user_scopes: Optional[List[str]] = SCOPE_REGISTRY
    subject_request_download_link_ttl_seconds: int = 432000  # 5 days
    request_rate_limit: str = "1000/minute"
    rate_limit_prefix: str = "fides-"
    identity_verification_attempt_limit: int = 3  # 3 attempts

    @validator("request_rate_limit")
    @classmethod
    def validate_request_rate_limit(
        cls,
        v: str,
    ) -> str:
        """Validate the formatting of `request_rate_limit`"""
        try:
            # Defer to `limits.parse_many` https://limits.readthedocs.io/en/stable/api.html#limits.parse_many
            parse_many(v)
        except ValueError:
            message = """
            Ratelimits must be specified in the format: [count] [per|/] [n (optional)] [second|minute|hour|day|month|year]
            e.g. 10 per hour
            e.g. 10/hour
            e.g. 10/hour;100/day;2000 per year
            e.g. 100/day, 500/7days
            """
            raise ValueError(message)
        return v

    class Config:
        env_prefix = ENV_PREFIX
