"""Secret provider abstraction for dynamically-resolved credentials."""

from typing import Optional

from fides.config import CONFIG
from fides.config.secrets.aws_secrets_manager_provider import (
    AWSSecretsManagerProvider,
)
from fides.config.secrets.base import SecretProvider, SecretProviderError, SecretValue
from fides.config.secrets.factory import create_secret_provider
from fides.config.secrets.static_provider import StaticSecretProvider

_provider: Optional[SecretProvider] = None


def get_secret_provider() -> SecretProvider:
    """Return the application-wide SecretProvider singleton.

    Created lazily on first access from ``CONFIG.secrets``.  All consumers
    share one instance so the credential cache is coherent.
    """
    global _provider
    if _provider is None:
        _provider = create_secret_provider(CONFIG.secrets)
    return _provider


def reset_secret_provider() -> None:
    """Reset the singleton to ``None``, forcing re-creation on next access.

    Intended for testing only.
    """
    global _provider
    _provider = None


__all__ = [
    "AWSSecretsManagerProvider",
    "SecretProvider",
    "SecretProviderError",
    "SecretValue",
    "StaticSecretProvider",
    "create_secret_provider",
    "get_secret_provider",
    "reset_secret_provider",
]
