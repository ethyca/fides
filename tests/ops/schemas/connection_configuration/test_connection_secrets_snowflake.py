"""Unit tests for Snowflake connection secrets schema and private key handling."""

import base64

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from fides.api.schemas.connection_configuration.connection_secrets_snowflake import (
    SnowflakeSchema,
    normalize_private_key,
    format_private_key,
)


def _make_base64_der_key() -> str:
    """Produce a base64-encoded DER private key string (what Snowflake expects as str)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return base64.b64encode(der).decode("ascii")


def _make_pem_key() -> str:
    """Produce a PEM-format private key string."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")


class TestNormalizePrivateKey:
    """Tests for normalize_private_key (base64 DER vs PEM)."""

    def test_base64_der_passthrough(self):
        """Base64 DER string is stripped of whitespace and returned as-is."""
        key = _make_base64_der_key()
        assert normalize_private_key(key) == key

    def test_base64_der_strips_whitespace(self):
        """Base64 DER with newlines/spaces is normalized to a single line."""
        key = _make_base64_der_key()
        # Simulate copy-paste with line breaks
        wrapped = key[:64] + "\n" + key[64:128] + " \n " + key[128:]
        result = normalize_private_key(wrapped)
        assert result == key
        assert "\n" not in result
        assert " " not in result

    def test_pem_normalized(self):
        """PEM key is normalized via format_private_key (spaces in body -> newlines)."""
        pem = _make_pem_key()
        result = normalize_private_key(pem)
        assert "-----BEGIN" in result
        assert "-----END" in result

    def test_pem_with_spaces_in_body(self):
        """PEM with spaces in the key body gets spaces replaced by newlines."""
        pem = _make_pem_key()
        # Replace newlines in the body with spaces (broken PEM)
        lines = pem.split("\n")
        # lines[0]=BEGIN, lines[1:-2]=body, lines[-1]=END
        body = "".join(lines[1:-2]).replace("\n", " ")
        broken = f"{lines[0]}\n{body}\n{lines[-1]}"
        result = normalize_private_key(broken)
        assert "-----BEGIN" in result
        assert "-----END" in result


class TestSnowflakeSchemaPrivateKey:
    """Tests for SnowflakeSchema with private_key (base64 DER and PEM)."""

    def test_schema_accepts_base64_der_private_key(self):
        """Schema accepts a base64-encoded DER private key (no PEM headers)."""
        key = _make_base64_der_key()
        schema = SnowflakeSchema(
            account_identifier="test_account",
            user_login_name="test_user",
            private_key=key,
            warehouse_name="test_wh",
        )
        assert schema.private_key == key

    def test_schema_accepts_pem_private_key(self):
        """Schema accepts PEM-format private key."""
        pem = _make_pem_key()
        schema = SnowflakeSchema(
            account_identifier="test_account",
            user_login_name="test_user",
            private_key=pem,
            warehouse_name="test_wh",
        )
        assert schema.private_key is not None
        assert "-----BEGIN" in schema.private_key

    def test_schema_rejects_both_password_and_private_key(self):
        """Schema rejects providing both password and private_key."""
        key = _make_base64_der_key()
        with pytest.raises(
            ValueError, match="Cannot provide both password and private key"
        ):
            SnowflakeSchema(
                account_identifier="test_account",
                user_login_name="test_user",
                password="secret",
                private_key=key,
                warehouse_name="test_wh",
            )

    def test_schema_requires_password_or_private_key(self):
        """Schema requires either password or private_key."""
        with pytest.raises(
            ValueError, match="Must provide either a password or a private key"
        ):
            SnowflakeSchema(
                account_identifier="test_account",
                user_login_name="test_user",
                warehouse_name="test_wh",
            )


class TestFormatPrivateKey:
    """Tests for format_private_key (PEM-only helper)."""

    def test_format_private_key_requires_pem_structure(self):
        """format_private_key expects PEM with ----- delimiters; base64 DER has none."""
        key = _make_base64_der_key()
        with pytest.raises(IndexError):
            format_private_key(key)
