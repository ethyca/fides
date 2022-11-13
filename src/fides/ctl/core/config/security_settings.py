"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from typing import Dict, List, Optional, Tuple, Union

import validators
from fideslib.core.config import FidesSettings
from fideslib.cryptography.cryptographic_util import generate_salt, hash_with_salt
from fideslib.exceptions import MissingConfig
from pydantic import root_validator, validator

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY

ENV_PREFIX = "FIDES__SECURITY__"


class SecuritySettings(FidesSettings):
    """Configuration settings for Security variables."""

    root_user_scopes: Optional[List[str]] = SCOPE_REGISTRY
    subject_request_download_link_ttl_seconds: int = 432000  # 5 days
    aes_encryption_key_length: int = 16
    aes_gcm_nonce_length: int = 12
    app_encryption_key: str
    drp_jwt_secret: Optional[str] = None
    root_username: Optional[str] = None
    root_password: Optional[str] = None
    identity_verification_attempt_limit: int = 3  # 3 attempts

    @validator("app_encryption_key")
    @classmethod
    def validate_encryption_key_length(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> Optional[str]:
        """Validate the encryption key is exactly 32 characters"""
        if v is None or len(v.encode(values.get("encoding", "UTF-8"))) != 32:
            raise ValueError(
                "APP_ENCRYPTION_KEY value must be exactly 32 characters long"
            )
        return v

    cors_origins: List[str] = []

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

    encoding: str = "UTF-8"

    oauth_root_client_id: str
    oauth_root_client_secret: str
    oauth_root_client_secret_hash: Optional[Tuple]
    oauth_access_token_expire_minutes: int = 60 * 24 * 8
    oauth_client_id_length_bytes = 16
    oauth_client_secret_length_bytes = 16

    @root_validator(pre=True)
    @classmethod
    def assemble_root_access_token(cls, values: Dict[str, str]) -> Dict[str, str]:
        """
        Sets a hashed value of the root access key.
        This is hashed as it is not wise to return a plaintext for of the
        root credential anywhere in the system.
        """
        value = values.get("oauth_root_client_secret")
        if not value:
            raise MissingConfig(
                "oauth_root_client_secret is required", SecuritySettings
            )

        encoding = values.get("encoding", "UTF-8")

        salt = generate_salt()
        hashed_client_id = hash_with_salt(value.encode(encoding), salt.encode(encoding))
        values["oauth_root_client_secret_hash"] = (hashed_client_id, salt.encode(encoding))  # type: ignore
        return values

    class Config:
        env_prefix = ENV_PREFIX
