"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from typing import Dict, List, Optional, Tuple, Union

import validators
from pydantic import validator
from slowapi.wrappers import parse_many  # type: ignore

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fides.lib.cryptography.cryptographic_util import generate_salt, hash_with_salt

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__SECURITY__"


class SecuritySettings(FidesSettings):
    """Configuration settings for Security variables."""

    root_user_scopes: Optional[List[str]] = SCOPE_REGISTRY
    subject_request_download_link_ttl_seconds: int = 432000  # 5 days
    request_rate_limit: str = "1000/minute"
    rate_limit_prefix: str = "fides-"
    aes_encryption_key_length: int = 16
    aes_gcm_nonce_length: int = 12
    app_encryption_key: str = ""
    drp_jwt_secret: Optional[str] = None
    root_username: Optional[str] = None
    root_password: Optional[str] = None
    parent_server_username: Optional[str] = None
    parent_server_password: Optional[str] = None
    identity_verification_attempt_limit: int = 3  # 3 attempts
    encoding: str = "UTF-8"

    cors_origins: List[str] = []
    oauth_root_client_id: str = ""
    oauth_root_client_secret: str = ""
    oauth_root_client_secret_hash: Optional[Tuple]
    oauth_access_token_expire_minutes: int = 60 * 24 * 8
    oauth_client_id_length_bytes = 16
    oauth_client_secret_length_bytes = 16

    @validator("app_encryption_key")
    @classmethod
    def validate_encryption_key_length(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> Optional[str]:
        """Validate the encryption key is exactly 32 characters"""

        # If the value is the default value, return immediately to prevent unwanted errors
        if v == "":
            return v

        if v is None or len(v.encode(values.get("encoding", "UTF-8"))) != 32:
            raise ValueError(
                "APP_ENCRYPTION_KEY value must be exactly 32 characters long"
            )
        return v

    @validator("cors_origins", pre=True)
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Return a list of valid origins for CORS requests"""

        def validate(values: List[str]) -> None:
            for value in values:
                if value != "*":
                    if not validators.url(value):
                        raise ValueError(f"{value} is not a valid url")

        if isinstance(v, str) and not v.startswith("["):
            values = [i.strip() for i in v.split(",")]
            validate(values)

            return values
        if isinstance(v, (list, str)):
            validate(v)  # type: ignore

            return v
        raise ValueError(v)

    @validator("oauth_root_client_secret_hash")
    @classmethod
    def assemble_root_access_token(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> Optional[Tuple]:
        """
        Sets a hashed value of the root access key.
        This is hashed as it is not wise to return a plaintext for of the
        root credential anywhere in the system.
        """
        value = values.get("oauth_root_client_secret", "")

        if not value:
            return None

        encoding = values.get("encoding", "UTF-8")

        salt = generate_salt()
        hashed_client_id = hash_with_salt(value.encode(encoding), salt.encode(encoding))
        oauth_root_client_secret_hash = (hashed_client_id, salt.encode(encoding))  # type: ignore
        return oauth_root_client_secret_hash

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
