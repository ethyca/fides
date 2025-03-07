"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from typing import List, Optional, Pattern, Tuple, Union

import validators
from pydantic import Field, SerializeAsAny, ValidationInfo, field_validator
from pydantic_settings import SettingsConfigDict
from slowapi.wrappers import parse_many  # type: ignore

from fides.api.cryptography.cryptographic_util import (
    generate_salt,
    hash_credential_with_salt,
)
from fides.api.custom_types import URLOriginString
from fides.api.oauth.roles import OWNER
from fides.common.api.scope_registry import SCOPE_REGISTRY

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__SECURITY__"


class SecuritySettings(FidesSettings):
    """Configuration settings for application security."""

    aes_encryption_key_length: int = Field(
        default=16,
        description="Length of desired encryption key when using Fides to generate a random secure string used for AES encryption.",
    )
    aes_gcm_nonce_length: int = Field(
        default=12,
        description="Length of desired random byte str for the AES GCM encryption used throughout Fides.",
    )
    app_encryption_key: str = Field(
        default="", description="The key used to sign Fides API access tokens."
    )
    cors_origins: SerializeAsAny[List[URLOriginString]] = Field(
        default_factory=list,
        description="A list of client addresses allowed to communicate with the Fides webserver.",
    )
    cors_origin_regex: Optional[Pattern] = Field(
        default=None,
        description="A regex pattern used to set the CORS origin allowlist.",
    )
    drp_jwt_secret: Optional[str] = Field(
        default=None,
        description="JWT secret by which passed-in identity is decrypted according to the HS256 algorithm.",
    )
    encoding: str = Field(
        default="UTF-8", description="Text encoding to use for the application."
    )
    env: str = Field(
        default="prod",
        description="The default, `dev`, does not apply authentication to endpoints typically used by the CLI. The other option, `prod`, requires authentication for _all_ endpoints that may contain sensitive information.",
    )
    identity_verification_attempt_limit: int = Field(
        default=3,
        description="The number of times identity verification will be attempted before raising an error.",
    )
    oauth_root_client_id: str = Field(
        default="",
        description="The value used to identify the Fides application root API client.",
    )
    oauth_root_client_secret: str = Field(
        default="",
        description="The secret value used to authenticate the Fides application root API client.",
    )
    oauth_root_client_secret_hash: Optional[Tuple] = Field(
        default=None,
        description="Automatically generated by Fides, and represents a hashed value of the oauth_root_client_secret.",
    )
    oauth_access_token_expire_minutes: int = Field(
        default=11520,
        description="The time in minutes for which Fides API tokens will be valid. Default value is equal to 8 days.",
    )
    oauth_client_id_length_bytes: int = Field(
        default=16,
        description="Sets desired length in bytes of generated client id used for oauth.",
    )
    oauth_client_secret_length_bytes: int = Field(
        default=16,
        description="Sets desired length in bytes of generated client secret used for oauth.",
    )
    parent_server_password: Optional[str] = Field(
        default=None,
        description="When using a parent/child Fides deployment, this password will be used by the child server to access the parent server.",
    )
    parent_server_username: Optional[str] = Field(
        default=None,
        description="When using a parent/child Fides deployment, this username will be used by the child server to access the parent server.",
    )
    public_request_rate_limit: str = Field(
        default="2000/minute",
        description="The number of requests from a single IP address allowed to hit a public endpoint within the specified time period",
    )
    rate_limit_prefix: str = Field(
        default="fides-",
        description="The prefix given to keys in the Redis cache used by the rate limiter.",
    )
    request_rate_limit: str = Field(
        default="1000/minute",
        description="The number of requests from a single IP address allowed to hit an endpoint within a rolling 60 second period.",
    )
    root_user_scopes: List[str] = Field(
        default=SCOPE_REGISTRY,
        description="The list of scopes that are given to the root user.",
    )
    root_user_roles: List[str] = Field(
        default=[OWNER],
        description="The list of roles that are given to the root user.",
    )
    root_password: Optional[str] = Field(
        default=None,
        description="If set, this can be used in conjunction with root_username to log in without first creating a user in the database.",
    )

    root_username: Optional[str] = Field(
        default=None,
        description="If set, this can be used in conjunction with root_password to log in without first creating a user in the database.",
    )
    subject_request_download_ui_enabled: bool = Field(
        default=False,
        description="If set to True, the user interface will display a download button for subject requests.",
    )
    dsr_testing_tools_enabled: bool = Field(
        default=False,
        description="If set to True, contributor and owner roles will be able to run test privacy requests.",
    )
    subject_request_download_link_ttl_seconds: int = Field(
        default=432000,
        description="The number of seconds that a pre-signed download URL when using S3 storage will be valid. The default is equal to 5 days.",
    )
    enable_audit_log_resource_middleware: Optional[bool] = Field(
        default=False,
        description="Either enables the collection of audit log resource data or bypasses the middleware",
    )

    bastion_server_host: Optional[str] = Field(
        default=None, description="An optional field to store the bastion server host"
    )
    bastion_server_ssh_username: Optional[str] = Field(
        default=None,
        description="An optional field to store the username used to access the bastion server",
    )
    bastion_server_ssh_private_key: Optional[str] = Field(
        default=None,
        description="An optional field to store the key used to SSH into the bastion server.",
    )
    bastion_server_ssh_timeout: float = Field(
        default=0.1,
        description="The timeout in seconds for the transport socket (``socket.settimeout``)",
    )
    bastion_server_ssh_tunnel_timeout: float = Field(
        default=10,
        description="The timeout in seconds for tunnel connection (open_channel timeout)",
    )

    @field_validator("app_encryption_key", mode="before")
    @classmethod
    def validate_encryption_key_length(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Validate the encryption key is exactly 32 characters"""

        # If the value is the default value, return immediately to prevent unwanted errors
        if v == "":
            return v

        if v is None or len(v.encode(info.data.get("encoding", "UTF-8"))) != 32:
            raise ValueError(
                "APP_ENCRYPTION_KEY value must be exactly 32 characters long"
            )
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Return a list of valid origins for CORS requests"""
        if isinstance(v, str) and not v.startswith("["):
            values = [i.strip() for i in v.split(",")]
            return values
        if isinstance(v, list):
            return v
        raise ValueError(v)

    @field_validator("oauth_root_client_secret_hash", mode="before")
    @classmethod
    def assemble_root_access_token(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[Tuple]:
        """
        Sets a hashed value of the root access key.
        This is hashed as it is not wise to return a plaintext for of the
        root credential anywhere in the system.
        """
        value = info.data.get("oauth_root_client_secret", "")

        if not value:
            return None

        encoding = info.data.get("encoding", "UTF-8")

        salt = generate_salt()
        hashed_client_id = hash_credential_with_salt(
            value.encode(encoding), salt.encode(encoding)
        )
        oauth_root_client_secret_hash = (hashed_client_id, salt.encode(encoding))  # type: ignore
        return oauth_root_client_secret_hash

    @field_validator("request_rate_limit")
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

    @field_validator("env")
    @classmethod
    def validate_env(
        cls,
        v: str,
    ) -> str:
        """Validate the formatting of `request_rate_limit`"""
        if v not in ["dev", "prod"]:
            message = "Security environment must be either 'dev' or 'prod'."
            raise ValueError(message)
        return v

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
