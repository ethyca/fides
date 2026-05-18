import pytest

from fides.config import CONFIG
from fides.config.secrets.base import SecretProviderError, SecretValue
from fides.config.secrets.static_provider import (
    DATABASE_CREDENTIALS_KEY,
    DATABASE_READONLY_CREDENTIALS_KEY,
    StaticSecretProvider,
)


class TestStaticSecretProvider:
    def test_caches_db_credentials_from_config(self):
        provider = StaticSecretProvider()
        secret = provider.get_secret(DATABASE_CREDENTIALS_KEY)
        assert isinstance(secret, SecretValue)
        assert secret["username"] == CONFIG.database.user
        assert secret["password"] == CONFIG.database.raw_password

    def test_unknown_id_raises(self):
        provider = StaticSecretProvider()
        with pytest.raises(SecretProviderError, match="Unknown secret_id"):
            provider.get_secret("nonexistent")

    def test_invalidate_is_noop(self):
        provider = StaticSecretProvider()
        provider.invalidate(DATABASE_CREDENTIALS_KEY)
        assert (
            provider.get_secret(DATABASE_CREDENTIALS_KEY)["username"]
            == CONFIG.database.user
        )

    def test_invalidate_unknown_id_does_not_raise(self):
        provider = StaticSecretProvider()
        provider.invalidate("nonexistent")

    def test_readonly_credentials_absent_when_no_readonly_server(self):
        if CONFIG.database.readonly_server:
            pytest.skip("readonly_server is configured in this environment")
        provider = StaticSecretProvider()
        with pytest.raises(SecretProviderError, match="Unknown secret_id"):
            provider.get_secret(DATABASE_READONLY_CREDENTIALS_KEY)
