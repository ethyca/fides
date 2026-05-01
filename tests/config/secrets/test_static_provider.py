import pytest

from fides.config.secrets.base import SecretProviderError, SecretValue
from fides.config.secrets.static_provider import StaticSecretProvider


class TestStaticSecretProvider:
    def test_get_secret_returns_correct_value(self):
        provider = StaticSecretProvider(
            secrets={"db": {"username": "app", "password": "s3cret"}}
        )
        secret = provider.get_secret("db")
        assert secret["username"] == "app"
        assert secret["password"] == "s3cret"

    def test_get_secret_returns_secret_value_type(self):
        provider = StaticSecretProvider(secrets={"db": {"username": "app"}})
        assert isinstance(provider.get_secret("db"), SecretValue)

    def test_get_secret_unknown_id_raises(self):
        provider = StaticSecretProvider(secrets={"db": {"username": "app"}})
        with pytest.raises(SecretProviderError, match="Unknown secret_id"):
            provider.get_secret("nonexistent")

    def test_invalidate_is_noop(self):
        provider = StaticSecretProvider(
            secrets={"db": {"username": "app", "password": "s3cret"}}
        )
        provider.invalidate("db")
        # Still works after invalidation
        assert provider.get_secret("db")["username"] == "app"

    def test_invalidate_unknown_id_does_not_raise(self):
        provider = StaticSecretProvider(secrets={})
        provider.invalidate("nonexistent")  # should not raise

    def test_multiple_secrets(self):
        provider = StaticSecretProvider(
            secrets={
                "db": {"username": "dbuser", "password": "dbpass"},
                "redis": {"password": "redispass"},
            }
        )
        assert provider.get_secret("db")["username"] == "dbuser"
        assert provider.get_secret("redis")["password"] == "redispass"
