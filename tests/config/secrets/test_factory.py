import pytest
from moto import mock_aws

from fides.config.secrets.aws_secrets_manager_provider import (
    AWSSecretsManagerProvider,
)
from fides.config.secrets.base import SecretProviderError
from fides.config.secrets.factory import create_secret_provider
from fides.config.secrets.static_provider import StaticSecretProvider
from fides.config.secrets_settings import SecretsSettings


class TestCreateSecretProvider:
    def test_static_provider(self):
        settings = SecretsSettings(provider="static")
        provider = create_secret_provider(
            settings, static_secrets={"db": {"user": "admin"}}
        )
        assert isinstance(provider, StaticSecretProvider)
        assert provider.get_secret("db")["user"] == "admin"

    def test_static_provider_default_empty_secrets(self):
        settings = SecretsSettings(provider="static")
        provider = create_secret_provider(settings)
        assert isinstance(provider, StaticSecretProvider)
        with pytest.raises(SecretProviderError):
            provider.get_secret("anything")

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
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SecretsSettings(provider="vault")

    def test_default_provider_is_static(self):
        settings = SecretsSettings()
        assert settings.provider == "static"
        provider = create_secret_provider(settings)
        assert isinstance(provider, StaticSecretProvider)
