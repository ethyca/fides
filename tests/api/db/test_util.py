"""Tests for the db.util module."""

import pytest
from sqlalchemy import String, Text
from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType

from fides.api.db.util import optionally_encrypted_type


@pytest.mark.unit
class TestOptionallyEncryptedType:
    """Test suite for the optionally_encrypted_type factory function."""

    def test_returns_encrypted_type_when_enabled(self):
        """Test that StringEncryptedType is returned when encryption_enabled=True."""
        col_type = optionally_encrypted_type(type_in=Text(), encryption_enabled=True)
        assert isinstance(col_type, StringEncryptedType)

    def test_returns_plain_type_when_disabled(self):
        """Test that the plain type is returned when encryption_enabled=False."""
        col_type = optionally_encrypted_type(type_in=Text(), encryption_enabled=False)
        assert isinstance(col_type, Text)
        assert not isinstance(col_type, StringEncryptedType)

    def test_returns_encrypted_type_with_string_type(self):
        """Test that StringEncryptedType works with String() type."""
        col_type = optionally_encrypted_type(type_in=String(), encryption_enabled=True)
        assert isinstance(col_type, StringEncryptedType)

    def test_returns_plain_string_type_when_disabled(self):
        """Test that the plain String type is returned when encryption is disabled."""
        col_type = optionally_encrypted_type(type_in=String(), encryption_enabled=False)
        assert isinstance(col_type, String)
        assert not isinstance(col_type, StringEncryptedType)

    def test_defaults_to_text_type(self):
        """Test that Text() is used as default when no type_in is provided."""
        col_type = optionally_encrypted_type(encryption_enabled=False)
        assert isinstance(col_type, Text)

    def test_defaults_to_text_type_with_encryption(self):
        """Test that Text() is used as default with encryption when no type_in is provided."""
        col_type = optionally_encrypted_type(encryption_enabled=True)
        assert isinstance(col_type, StringEncryptedType)
