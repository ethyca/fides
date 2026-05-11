"""Tests for engine creator factories and credential helpers."""

import ssl
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from fides.common.engine_creators import (
    _build_ssl_context,
    _convert_asyncpg_params,
    get_db_credentials,
    get_readonly_db_credentials,
    make_async_creator,
    make_sync_creator,
)
from fides.config import CONFIG
from fides.config.database_settings import DatabaseSettings


class TestGetDbCredentials:
    def test_returns_expected_fields(self) -> None:
        creds = get_db_credentials()
        assert set(creds.keys()) == {"host", "port", "user", "password", "dbname"}

    def test_port_is_int(self) -> None:
        creds = get_db_credentials()
        assert isinstance(creds["port"], int)

    def test_password_is_unescaped(self) -> None:
        """raw_password should reverse the quote_plus escaping."""
        creds = get_db_credentials()
        # The raw password should not contain URL-encoded characters
        # unless the original password literally contains them
        assert creds["password"] == CONFIG.database.raw_password

    def test_uses_test_db_in_test_mode(self) -> None:
        creds = get_db_credentials()
        if CONFIG.test_mode:
            assert creds["dbname"] == CONFIG.database.test_db
        else:
            assert creds["dbname"] == CONFIG.database.db


class TestGetReadonlyDbCredentials:
    def test_returns_none_when_not_configured(self) -> None:
        if not CONFIG.database.readonly_server:
            assert get_readonly_db_credentials() is None


class TestRawPassword:
    """Verify raw_password round-trips passwords with special characters."""

    @pytest.mark.parametrize(
        "password",
        [
            "simple",
            "p@ssw0rd",
            "pass#word",
            "pass%word",
            "pass/word",
            "p@ss#w%rd/123",
            "has spaces",
            "has+plus",
        ],
    )
    def test_raw_password_round_trip(self, password: str) -> None:
        """Constructing DatabaseSettings with special-char passwords
        should produce a raw_password that matches the original."""
        settings = DatabaseSettings(password=password)
        assert settings.raw_password == password

    @pytest.mark.parametrize("password", ["p@ssw0rd", "pass%word"])
    def test_raw_readonly_password_round_trip(self, password: str) -> None:
        """readonly_password should also round-trip through quote_plus."""
        settings = DatabaseSettings(
            readonly_server="replica", readonly_password=password
        )
        assert settings.raw_readonly_password == password

    def test_raw_readonly_password_none_when_not_set(self) -> None:
        settings = DatabaseSettings()
        assert settings.raw_readonly_password is None

    def test_pre_encoded_password_treated_as_literal(self) -> None:
        """Passwords are always treated as raw values, never as pre-encoded.

        If a user sets their password to "foo%40bar" (literally containing
        the characters %, 4, 0), raw_password returns "foo%40bar" — NOT
        "foo@bar". This matches the old URI-based path where escape_password
        would double-encode %40 to %2540 in the URI, and psycopg2 would
        decode it back to %40.
        """
        settings = DatabaseSettings(password="foo%40bar")
        assert settings.raw_password == "foo%40bar"


class TestConvertAsyncpgParams:
    def test_converts_sslmode_to_ssl(self) -> None:
        params = {"sslmode": "require", "other": "value"}
        result = _convert_asyncpg_params(params)
        assert "sslmode" not in result
        assert result["ssl"] == "require"
        assert result["other"] == "value"

    def test_drops_sslrootcert(self) -> None:
        params = {"sslrootcert": "/path/to/cert.pem", "other": "value"}
        result = _convert_asyncpg_params(params)
        assert "sslrootcert" not in result
        assert result["other"] == "value"

    def test_does_not_mutate_input(self) -> None:
        params = {"sslmode": "require", "sslrootcert": "/path"}
        _convert_asyncpg_params(params)
        assert "sslmode" in params
        assert "sslrootcert" in params

    def test_empty_params(self) -> None:
        assert _convert_asyncpg_params({}) == {}


class TestBuildSslContext:
    def test_returns_none_without_sslrootcert(self) -> None:
        assert _build_ssl_context({}) is None
        assert _build_ssl_context({"sslmode": "require"}) is None

    def test_returns_context_with_valid_sslrootcert(self, tmp_path) -> None:
        """Success path: a valid CA cert produces a usable SSLContext."""
        # Generate a self-signed cert for testing
        import datetime

        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "test-ca"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=1)
            )
            .sign(key, hashes.SHA256())
        )
        cert_file = tmp_path / "ca.pem"
        cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

        ctx = _build_ssl_context({"sslrootcert": str(cert_file)})
        assert isinstance(ctx, ssl.SSLContext)
        assert ctx.verify_mode == ssl.CERT_REQUIRED

    def test_returns_none_with_invalid_cert(self, tmp_path) -> None:
        cert_file = tmp_path / "bad.pem"
        cert_file.write_text("not a cert")
        with pytest.raises(ssl.SSLError):
            _build_ssl_context({"sslrootcert": str(cert_file)})


class TestMakeSyncCreator:
    def test_returns_callable(self) -> None:
        creator = make_sync_creator()
        assert callable(creator)

    def test_creator_opens_working_connection(self) -> None:
        """The sync creator should produce a real psycopg2 connection."""
        creator = make_sync_creator()
        conn = creator()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            assert cur.fetchone() == (1,)
        finally:
            conn.close()

    def test_creator_with_connect_args(self) -> None:
        """connect_args like keepalives should be forwarded."""
        creator = make_sync_creator(
            connect_args={"keepalives": 1, "keepalives_idle": 30}
        )
        conn = creator()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            assert cur.fetchone() == (1,)
        finally:
            conn.close()

    def test_engine_with_sync_creator(self) -> None:
        """A full engine using the sync creator can execute queries."""
        creator = make_sync_creator()
        engine = create_engine("postgresql+psycopg2://", creator=creator, pool_size=1)
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            engine.dispose()


class TestMakeAsyncCreator:
    def test_returns_callable(self) -> None:
        creator = make_async_creator()
        assert callable(creator)

    async def test_engine_with_async_creator(self) -> None:
        """A full async engine using the async creator can execute queries."""
        creator = make_async_creator()
        engine = create_async_engine(
            "postgresql+asyncpg://", creator=creator, pool_size=1
        )
        try:
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            await engine.dispose()

    @patch("fides.common.engine_creators.asyncpg")
    @patch("fides.common.engine_creators.AsyncAdapt_asyncpg_connection")
    def test_ssl_context_not_overwritten_by_async_params(
        self, mock_adapt_conn, mock_asyncpg
    ) -> None:
        """When both sslrootcert and sslmode are configured, the SSLContext
        must not be overwritten by the raw ssl string from async_params."""
        mock_ssl_context = MagicMock(spec=ssl.SSLContext)

        with (
            patch(
                "fides.common.engine_creators._build_ssl_context",
                return_value=mock_ssl_context,
            ),
            patch(
                "fides.common.engine_creators._convert_asyncpg_params",
                return_value={"ssl": "require", "other": "value"},
            ),
            patch(
                "fides.common.engine_creators.await_only",
                side_effect=lambda coro: coro,
            ),
        ):
            creator = make_async_creator()
            creator()

        # asyncpg.connect was called — check the ssl kwarg
        connect_kwargs = mock_asyncpg.connect.call_args[1]
        assert connect_kwargs["ssl"] is mock_ssl_context, (
            f"Expected SSLContext but got {connect_kwargs['ssl']!r} — "
            "async_params overwrote the ssl_context"
        )
        assert connect_kwargs["other"] == "value"
