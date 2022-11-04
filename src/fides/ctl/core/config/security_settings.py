"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from typing import List, Optional

from fideslib.core.config import SecuritySettings as FideslibSecuritySettings

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY

ENV_PREFIX = "FIDES__SECURITY__"


class SecuritySettings(FideslibSecuritySettings):
    """Configuration settings for Security variables."""

    root_user_scopes: Optional[List[str]] = SCOPE_REGISTRY
    subject_request_download_link_ttl_seconds: int = 432000  # 5 days

    class Config:
        env_prefix = ENV_PREFIX
