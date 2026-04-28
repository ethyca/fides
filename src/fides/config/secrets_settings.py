"""Configuration settings for the secret provider subsystem."""

from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__SECRETS__"


class AWSSecretsManagerSettings(FidesSettings):
    """Configuration for the AWS Secrets Manager provider."""

    region: str = Field(
        default="us-east-1",
        description="AWS region for Secrets Manager.",
    )
    cache_ttl_seconds: float = Field(
        default=300.0,
        description="TTL for cached secret values.",
    )
    cache_stale_ttl_seconds: float = Field(
        default=1800.0,
        description="Grace period for serving last-known-good credentials when Secrets Manager is unreachable.",
    )
    circuit_breaker_cooldown_seconds: float = Field(
        default=30.0,
        description="Cooldown window after a failed fetch before allowing another retry.",
    )
    endpoint_url: Optional[str] = Field(
        default=None,
        description="Optional custom endpoint URL (e.g. LocalStack for local dev/CI).",
    )

    model_config = SettingsConfigDict(
        env_prefix=f"{ENV_PREFIX}AWS_SECRETS_MANAGER__",
    )


class SecretsSettings(FidesSettings):
    """Top-level configuration for the secrets provider."""

    provider: str = Field(
        default="static",
        description="Which secret provider to use: 'static' or 'aws_secrets_manager'.",
    )
    aws_secrets_manager: AWSSecretsManagerSettings = Field(
        default_factory=AWSSecretsManagerSettings,
    )

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
