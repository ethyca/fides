"""Factory for creating a SecretProvider from config settings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from loguru import logger as log

from fides.config.secrets.aws_secrets_manager_provider import (
    AWSSecretsManagerProvider,
)
from fides.config.secrets.base import SecretProvider, SecretProviderError
from fides.config.secrets.static_provider import StaticSecretProvider

if TYPE_CHECKING:
    from fides.config.secrets_settings import SecretsSettings


def create_secret_provider(
    secrets_settings: SecretsSettings,
    static_secrets: Dict[str, Dict[str, Any]] | None = None,
) -> SecretProvider:
    """Instantiate the configured secret provider.

    Args:
        secrets_settings: The ``[secrets]`` config section.
        static_secrets: Secret ID → key/value mapping for the static provider.
            Ignored when the provider is not ``"static"``.
    """
    provider_type = secrets_settings.provider

    if provider_type == "static":
        log.info("Using static secret provider")
        return StaticSecretProvider(secrets=static_secrets or {})

    if provider_type == "aws_secrets_manager":
        aws = secrets_settings.aws_secrets_manager
        log.info(
            "Using AWS Secrets Manager provider (region={})",
            aws.region,
        )
        return AWSSecretsManagerProvider(
            region_name=aws.region,
            cache_ttl_seconds=aws.cache_ttl_seconds,
            cache_stale_ttl_seconds=aws.cache_stale_ttl_seconds,
            circuit_breaker_cooldown_seconds=aws.circuit_breaker_cooldown_seconds,
            endpoint_url=aws.endpoint_url,
        )

    raise SecretProviderError(
        f"Unknown secrets provider: {provider_type!r}. "
        f"Must be 'static' or 'aws_secrets_manager'."
    )
