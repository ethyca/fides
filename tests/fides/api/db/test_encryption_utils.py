"""Tests for the db.encryption_utils module."""

import pytest
from sqlalchemy import String, Text
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.encryption_utils import (
    _reset_encryption_key_cache,
    encrypted_type,
    get_encryption_key,
)
from fides.config import CONFIG


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the cached DEK before and after each test."""
    _reset_encryption_key_cache()
    yield
    _reset_encryption_key_cache()


@pytest.mark.unit
class TestGetEncryptionKey:
    """Test suite for the get_encryption_key function."""

    def test_returns_app_encryption_key(self):
        """get_encryption_key() should return CONFIG.security.app_encryption_key in legacy mode."""
        result = get_encryption_key()
        assert result == CONFIG.security.app_encryption_key

    def test_returns_string(self):
        """get_encryption_key() must return a string."""
        assert isinstance(get_encryption_key(), str)

    def test_caches_result(self):
        """get_encryption_key() should return the same cached value on repeated calls."""
        first = get_encryption_key()
        second = get_encryption_key()
        assert first is second


@pytest.mark.unit
class TestEncryptedType:
    """Test suite for the encrypted_type factory function."""

    def test_returns_string_encrypted_type(self):
        """encrypted_type() should return a StringEncryptedType."""
        col_type = encrypted_type()
        assert isinstance(col_type, StringEncryptedType)

    def test_default_type_in_is_text(self):
        """Default underlying type should be Text."""
        col_type = encrypted_type()
        assert isinstance(col_type.underlying_type, Text)

    def test_custom_type_in(self):
        """Specifying type_in should use that type."""
        col_type = encrypted_type(type_in=String())
        assert isinstance(col_type.underlying_type, String)

    def test_key_is_callable(self):
        """The key should be a callable (get_encryption_key), not a string."""
        col_type = encrypted_type()
        assert callable(col_type.key)
        assert col_type.key is get_encryption_key

    def test_uses_aesgcm_engine(self):
        """Engine should be AesGcmEngine."""
        col_type = encrypted_type()
        assert isinstance(col_type.engine, AesGcmEngine)
