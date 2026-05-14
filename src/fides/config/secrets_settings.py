"""Configuration settings for the secret provider subsystem."""

from typing import Literal, Optional

from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__SECRETS__"


class AWSSecretsManagerSettings(FidesSettings):
    """Configuration for the AWS Secrets Manager provider."""

    region: str = Field(
        description="AWS region for Secrets Manager.",
    )
    cache_ttl_seconds: float = Field(
        default=900.0,
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

    @model_validator(mode="before")
    @classmethod
    def _build_aws_settings_if_needed(cls, values: dict) -> dict:
        """Construct AWS settings from env vars when provider is aws but no config was provided."""
        if values.get("provider") == "aws_secrets_manager" and not values.get(
            "aws_secrets_manager"
        ):
            try:
                values["aws_secrets_manager"] = AWSSecretsManagerSettings()
            except Exception as exc:
                raise ValueError(
                    "secrets.provider is 'aws_secrets_manager' but "
                    "secrets.aws_secrets_manager is not configured. "
                    "Provide the configuration via TOML or environment variables "
                    "(e.g. FIDES__SECRETS__AWS_SECRETS_MANAGER__REGION)."
                ) from exc
        return values
