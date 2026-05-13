"""Configuration settings for the secret provider subsystem."""

from typing import Literal, Optional

from pydantic import Field, model_validator
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

    provider: Literal["static", "aws_secrets_manager"] = Field(
        default="static",
        description="Which secret provider to use: 'static' or 'aws_secrets_manager'.",
    )
    aws_secrets_manager: Optional[AWSSecretsManagerSettings] = Field(
        default=None,
        description="AWS Secrets Manager configuration. Required when provider is 'aws_secrets_manager'.",
    )

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)

    @model_validator(mode="after")
    def _validate_aws_config(self) -> "SecretsSettings":
        """Require aws_secrets_manager settings when provider is 'aws_secrets_manager'."""
        if self.provider == "aws_secrets_manager" and not self.aws_secrets_manager:
            raise ValueError(
                "secrets.provider is 'aws_secrets_manager' but "
                "secrets.aws_secrets_manager is not configured."
            )
        return self
