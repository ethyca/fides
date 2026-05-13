import os
from unittest.mock import patch

import pytest
from moto import mock_aws
from pydantic import ValidationError

import fides.config.secrets as secrets_module
from fides.config.secrets import get_secret_provider
from fides.config.secrets.aws_secrets_manager_provider import (
    AWSSecretsManagerProvider,
)
from fides.config.secrets.base import SecretProviderError
from fides.config.secrets.factory import create_secret_provider
from fides.config.secrets.static_provider import StaticSecretProvider
from fides.config.secrets_settings import SecretsSettings


class TestSecretsSettings:
    def test_aws_provider_without_aws_config_raises(self):
        with pytest.raises(
            ValidationError, match="aws_secrets_manager is not configured"
        ):
            SecretsSettings(provider="aws_secrets_manager")

    def test_aws_provider_with_aws_config_passes(self):
        settings = SecretsSettings(
            provider="aws_secrets_manager",
            aws_secrets_manager={"region": "us-east-1"},
        )
        assert settings.aws_secrets_manager is not None
        assert settings.aws_secrets_manager.region == "us-east-1"

    def test_aws_provider_from_env_vars(self):
        with patch.dict(
            os.environ,
            {
                "FIDES__SECRETS__AWS_SECRETS_MANAGER__REGION": "eu-west-1",
            },
        ):
            settings = SecretsSettings(provider="aws_secrets_manager")
            assert settings.aws_secrets_manager.region == "eu-west-1"

    def test_aws_config_requires_region(self):
        with pytest.raises(ValidationError, match="region"):
            SecretsSettings(
                provider="aws_secrets_manager",
                aws_secrets_manager={},
            )

    def test_static_provider_without_aws_config_passes(self):
        settings = SecretsSettings(provider="static")
        assert settings.aws_secrets_manager is None


class TestCreateSecretProvider:
    def test_static_provider(self):
        settings = SecretsSettings(provider="static")
        provider = create_secret_provider(settings)
        assert isinstance(provider, StaticSecretProvider)

    @mock_aws
    def test_aws_secrets_manager_provider(self):
        settings = SecretsSettings(
            provider="aws_secrets_manager",
            aws_secrets_manager={
                "region": "us-east-1",
                "cache_ttl_seconds": 120.0,
            },
        )
        provider = create_secret_provider(settings)
        assert isinstance(provider, AWSSecretsManagerProvider)
        assert provider._cache_ttl == 120.0

    def test_unknown_provider_raises_at_validation(self):
        with pytest.raises(ValidationError, match="literal_error"):
            SecretsSettings(provider="vault")

    def test_unknown_provider_raises_in_factory(self):
        """Bypass Pydantic validation to test the factory's own guard."""
        settings = SecretsSettings()
        settings.provider = "unknown"  # type: ignore[assignment]
        with pytest.raises(SecretProviderError, match="Unknown secrets provider"):
            create_secret_provider(settings)

    def test_default_provider_is_static(self):
        settings = SecretsSettings()
        assert settings.provider == "static"
        provider = create_secret_provider(settings)
        assert isinstance(provider, StaticSecretProvider)


class TestGetSecretProvider:
    def test_returns_provider(self):
        """Reset the singleton, then verify it creates and returns a provider."""
        original = secrets_module._provider
        try:
            secrets_module._provider = None
            provider = get_secret_provider()
            assert isinstance(provider, StaticSecretProvider)
        finally:
            secrets_module._provider = original

    def test_returns_same_instance(self):
        """Singleton: second call returns the same object."""
        original = secrets_module._provider
        try:
            secrets_module._provider = None
            first = get_secret_provider()
            second = get_secret_provider()
            assert first is second
        finally:
            secrets_module._provider = original
