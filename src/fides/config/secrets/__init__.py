"""Secret provider abstraction for dynamically-resolved credentials."""

from fides.config.secrets.aws_secrets_manager_provider import (
    AWSSecretsManagerProvider,
)
from fides.config.secrets.base import SecretProvider, SecretProviderError, SecretValue
from fides.config.secrets.factory import create_secret_provider
from fides.config.secrets.static_provider import StaticSecretProvider

__all__ = [
    "AWSSecretsManagerProvider",
    "SecretProvider",
    "SecretProviderError",
    "SecretValue",
    "StaticSecretProvider",
    "create_secret_provider",
]
