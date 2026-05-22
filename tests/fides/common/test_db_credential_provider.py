"""Tests for DBCredentialProvider.

Covers:
- Auth error detection (_is_auth_error / _extract_sqlstate)
- Exception sanitization (credential leakage prevention)
- Credential resolution (static, readonly, dynamic)
- Connection retry on auth failure (dynamic only)
"""

from unittest.mock import MagicMock, patch

import asyncpg
import psycopg2
import pytest
from sqlalchemy.dialects.postgresql.asyncpg import (
    AsyncAdapt_asyncpg_connection,
    AsyncAdapt_asyncpg_dbapi,
)
from sqlalchemy.util.concurrency import await_only

from fides.common.db_credential_provider import (
    _AUTH_RETRY_DELAY,
    DBCredentialProvider,
    SanitizedConnectionError,
)
from fides.config import CONFIG
from fides.config.database_settings import DatabaseSettings
from fides.config.secrets.base import SecretValue
from fides.config.secrets.static_provider import StaticSecretProvider

# --- Helpers ---


def _make_auth_error(pgcode=None, sqlstate=None):
    """Create a mock exception with pgcode/sqlstate attributes."""
    exc = Exception("connection failed")
    if pgcode is not None:
        exc.pgcode = pgcode
    if sqlstate is not None:
        exc.sqlstate = sqlstate
    return exc


def _make_password_leaking_error(password):
    """Create an exception whose message contains the password."""
    exc = Exception(
        f'FATAL: password authentication failed for user "myuser" '
        f"(password={password}, host=db.example.com)"
    )
    exc.pgcode = "28P01"
    return exc


# --- Fixtures ---


@pytest.fixture()
def static_provider():
    """DBCredentialProvider using the real CONFIG with a static provider."""
    yield DBCredentialProvider()


@pytest.fixture()
def dynamic_provider():
    """DBCredentialProvider backed by a mock SecretProvider."""
    with (
        patch("fides.common.db_credential_provider.get_secret_provider") as mock_get,
        patch("fides.common.db_credential_provider.CONFIG") as mock_config,
        patch("fides.common.db_credential_provider.time") as mock_time,
    ):
        mock_secret_provider = MagicMock()
        mock_secret_provider.get_secret.return_value = SecretValue(
            {"username": "secret_user", "password": "secret_pass"}
        )
        mock_get.return_value = mock_secret_provider
        mock_config.database = CONFIG.database
        mock_config.database.credential_secret_name = "db-creds"
        mock_config.database.readonly_credential_secret_name = None
        mock_config.test_mode = CONFIG.test_mode
        yield DBCredentialProvider(), mock_config, mock_secret_provider, mock_time


# --- Auth error detection ---


class TestIsAuthError:
    @pytest.mark.parametrize(
        "exc",
        [
            _make_auth_error(pgcode="28P01"),
            _make_auth_error(pgcode="28000"),
            _make_auth_error(sqlstate="28P01"),
            _make_auth_error(sqlstate="28000"),
        ],
        ids=["pgcode-28P01", "pgcode-28000", "sqlstate-28P01", "sqlstate-28000"],
    )
    def test_detects_auth_sqlstates(self, exc):
        assert DBCredentialProvider._is_auth_error(exc)

    @pytest.mark.parametrize(
        "message",
        [
            'FATAL:  password authentication failed for user "postgres"',
            'connection to server failed: FATAL:  Password authentication failed for user "app"',
        ],
        ids=["standard-pg", "mixed-case"],
    )
    def test_string_fallback_detects_auth_message(self, message):
        """psycopg2 doesn't set pgcode on connection-time errors,
        so _is_auth_error falls back to message matching."""
        exc = Exception(message)
        assert DBCredentialProvider._is_auth_error(exc)

    @pytest.mark.parametrize(
        "message",
        [
            "connection refused",
            "could not connect to server: Connection timed out",
            'FATAL:  database "nope" does not exist',
        ],
        ids=["refused", "timeout", "db-not-found"],
    )
    def test_string_fallback_rejects_non_auth_messages(self, message):
        exc = Exception(message)
        assert not DBCredentialProvider._is_auth_error(exc)

    def test_detects_psycopg2_operational_error(self):
        """OperationalError from RDS Proxy may not have a standard auth message."""
        exc = psycopg2.OperationalError("proxy connection error")
        assert DBCredentialProvider._is_auth_error(exc)

    @pytest.mark.parametrize(
        "exc",
        [
            _make_auth_error(pgcode="42P01"),
            Exception("generic error"),
        ],
        ids=["non-auth-pgcode", "no-code-attributes"],
    )
    def test_rejects_non_auth_errors(self, exc):
        assert not DBCredentialProvider._is_auth_error(exc)


# --- Exception sanitization ---


class TestSanitizeException:
    def test_includes_exception_type_and_sqlstate(self):
        exc = _make_auth_error(pgcode="28P01")
        sanitized = DBCredentialProvider._sanitize_exception(exc)
        assert isinstance(sanitized, SanitizedConnectionError)
        assert "Exception" in str(sanitized)
        assert "28P01" in str(sanitized)
        assert sanitized.sqlstate == "28P01"

    def test_without_sqlstate(self):
        sanitized = DBCredentialProvider._sanitize_exception(RuntimeError("boom"))
        assert "RuntimeError" in str(sanitized)
        assert sanitized.sqlstate is None

    def test_password_not_in_sanitized_message(self):
        password = "s3cret!p@ss"
        exc = _make_password_leaking_error(password)
        sanitized = DBCredentialProvider._sanitize_exception(exc)
        assert password not in str(sanitized)
        assert password not in repr(sanitized)

    def test_exception_chain_broken_with_from_none(self):
        exc = _make_auth_error(pgcode="28P01")
        sanitized = DBCredentialProvider._sanitize_exception(exc)
        try:
            raise sanitized from None
        except SanitizedConnectionError as caught:
            assert caught.__cause__ is None
            assert caught.__context__ is None


# --- Credential resolution ---


class TestGetCredentials:
    def test_static_returns_config_credentials(self, static_provider):
        creds = static_provider.get_credentials()
        assert set(creds.keys()) == {"host", "port", "user", "password", "dbname"}
        assert creds["host"] == CONFIG.database.server
        assert creds["port"] == int(CONFIG.database.port)
        assert creds["user"] == CONFIG.database.user
        assert isinstance(creds["port"], int)

    def test_static_is_not_dynamic(self, static_provider):
        assert not static_provider.is_dynamic

    def test_readonly_falls_back_to_primary_when_no_readonly_server(
        self, static_provider
    ):
        creds = static_provider.get_credentials(readonly=True)
        assert creds["host"] == CONFIG.database.server
        assert creds["user"] == CONFIG.database.user

    def test_readonly_uses_readonly_fields(self):
        readonly_settings = DatabaseSettings(
            readonly_server="replica",
            readonly_port="5433",
            readonly_user="ro_user",
            readonly_password="ro_pass",
            readonly_db="ro_db",
        )
        with (
            patch("fides.config.secrets.static_provider.CONFIG") as mock_sp_config,
            patch("fides.common.db_credential_provider.CONFIG") as mock_dcp_config,
            patch(
                "fides.common.db_credential_provider.get_secret_provider"
            ) as mock_get,
        ):
            mock_sp_config.database = readonly_settings
            mock_dcp_config.database = readonly_settings
            mock_dcp_config.test_mode = False
            mock_get.return_value = StaticSecretProvider()

            provider = DBCredentialProvider()
            creds = provider.get_credentials(readonly=True)
            assert creds == {
                "host": "replica",
                "port": 5433,
                "user": "ro_user",
                "password": "ro_pass",
                "dbname": "ro_db",
            }

    def test_dynamic_fetches_user_password_from_secret(self, dynamic_provider):
        provider, _, mock_secret_provider, _ = dynamic_provider
        assert provider.is_dynamic
        creds = provider.get_credentials()
        assert creds["user"] == "secret_user"
        assert creds["password"] == "secret_pass"
        assert creds["host"] == CONFIG.database.server
        mock_secret_provider.get_secret.assert_called_once_with("db-creds")

    def test_dynamic_without_credential_secret_name_raises(self, dynamic_provider):
        provider, mock_config, _, _ = dynamic_provider
        mock_config.database.credential_secret_name = None
        with pytest.raises(ValueError, match="credential_secret_name is not set"):
            provider.get_credentials()

    def test_dynamic_readonly_falls_back_to_primary_secret_id(self, dynamic_provider):
        provider, _, mock_secret_provider, _ = dynamic_provider
        provider.get_credentials(readonly=True)
        mock_secret_provider.get_secret.assert_called_once_with("db-creds")


# --- Database URL construction ---


class TestGetDatabaseUrl:
    def test_returns_valid_url(self, static_provider):
        url = static_provider.get_database_url()
        assert url.startswith("postgresql+psycopg2://")
        assert CONFIG.database.server in url

    def test_includes_connection_params(self):
        """SSL and other params from CONFIG.database.params are appended as query params."""
        with (
            patch("fides.config.secrets.static_provider.CONFIG") as mock_sp_config,
            patch("fides.common.db_credential_provider.CONFIG") as mock_dcp_config,
            patch(
                "fides.common.db_credential_provider.get_secret_provider"
            ) as mock_get,
        ):
            mock_sp_config.database = DatabaseSettings(
                params={"sslmode": "require", "sslrootcert": "/path/to/cert"},
            )
            mock_dcp_config.database = mock_sp_config.database
            mock_dcp_config.test_mode = False
            mock_get.return_value = StaticSecretProvider()

            provider = DBCredentialProvider()
            url = provider.get_database_url()
            assert "sslmode=require" in url
            assert "sslrootcert=/path/to/cert" in url

    @pytest.mark.parametrize(
        "user,password",
        [
            ("user@domain", "p@ss"),
            ("user", "pass%word"),
            ("user", "pass/word"),
            ("user", "pass#word"),
            ("user", "p@ss#w%rd/123"),
        ],
        ids=["at-sign", "percent", "slash", "hash", "mixed-special"],
    )
    def test_special_characters_are_url_encoded(self, user, password):
        """Credentials with special characters must be URL-encoded so the
        resulting URL is parseable by SQLAlchemy / libpq."""
        with (
            patch("fides.config.secrets.static_provider.CONFIG") as mock_sp_config,
            patch("fides.common.db_credential_provider.CONFIG") as mock_dcp_config,
            patch(
                "fides.common.db_credential_provider.get_secret_provider"
            ) as mock_get,
        ):
            mock_sp_config.database = DatabaseSettings(user=user, password=password)
            mock_dcp_config.database = mock_sp_config.database
            mock_dcp_config.test_mode = False
            mock_get.return_value = StaticSecretProvider()

            provider = DBCredentialProvider()
            url = provider.get_database_url()

            # Raw special chars should not appear unescaped in the URL
            # (the user:password section is between :// and @)
            user_pass_section = url.split("://")[1].split("@")[0]
            assert (
                "@" not in user_pass_section.split(":")[0] or "%40" in user_pass_section
            )
            assert "#" not in user_pass_section
            assert "/" not in user_pass_section


# --- Connection retry ---


class TestConnectWithRetry:
    def test_happy_path_merges_connect_kwargs_and_credentials(self, static_provider):
        connect_fn = MagicMock(return_value="connection")
        result = static_provider.connect_with_retry(connect_fn, {"keepalives": 1})
        assert result == "connection"
        call_kwargs = connect_fn.call_args[1]
        assert call_kwargs["host"] == CONFIG.database.server
        assert call_kwargs["keepalives"] == 1

    def test_non_auth_error_raises_sanitized(self, static_provider):
        connect_fn = MagicMock(side_effect=RuntimeError("connection refused"))
        with pytest.raises(SanitizedConnectionError) as exc_info:
            static_provider.connect_with_retry(connect_fn, {})
        assert CONFIG.database.raw_password not in str(exc_info.value)
        assert exc_info.value.__cause__ is None

    def test_static_does_not_retry_auth_error(self, static_provider):
        connect_fn = MagicMock(side_effect=_make_auth_error(pgcode="28P01"))
        with pytest.raises(SanitizedConnectionError):
            static_provider.connect_with_retry(connect_fn, {})
        connect_fn.assert_called_once()

    @pytest.mark.parametrize(
        "exc",
        [
            _make_auth_error(pgcode="28P01"),
            _make_auth_error(pgcode="28000"),
            _make_auth_error(sqlstate="28P01"),
            _make_auth_error(sqlstate="28000"),
        ],
        ids=["pgcode-28P01", "pgcode-28000", "sqlstate-28P01", "sqlstate-28000"],
    )
    def test_dynamic_retries_on_auth_error_and_succeeds(self, dynamic_provider, exc):
        provider, _, mock_secret_provider, mock_time = dynamic_provider
        connect_fn = MagicMock(side_effect=[exc, "connection"])
        result = provider.connect_with_retry(connect_fn, {})

        assert result == "connection"
        assert connect_fn.call_count == 2
        mock_secret_provider.invalidate.assert_called_once_with("db-creds")
        mock_time.sleep.assert_called_once_with(_AUTH_RETRY_DELAY)

    def test_dynamic_retry_fails_raises_sanitized(self, dynamic_provider):
        provider, _, _, _ = dynamic_provider
        connect_fn = MagicMock(
            side_effect=[
                _make_auth_error(pgcode="28P01"),
                _make_auth_error(pgcode="28P01"),
            ]
        )
        with pytest.raises(SanitizedConnectionError) as exc_info:
            provider.connect_with_retry(connect_fn, {})
        assert exc_info.value.__cause__ is None
        assert connect_fn.call_count == 2

    def test_psycopg2_wrong_password_against_real_db(self):
        """
        End-to-end: attempts to connect to the test database and
        checks the real psycopg2 auth failure is caught and sanitized.
        """
        wrong_password = "definitely-wrong-password-xyz"
        db = CONFIG.database
        wrong_db = DatabaseSettings(
            server=db.server,
            port=db.port,
            user=db.user,
            password=wrong_password,
            db=db.db,
            test_db=db.test_db,
        )
        with (
            patch("fides.config.secrets.static_provider.CONFIG") as mock_sp_config,
            patch("fides.common.db_credential_provider.CONFIG") as mock_dcp_config,
            patch(
                "fides.common.db_credential_provider.get_secret_provider"
            ) as mock_get,
        ):
            mock_sp_config.database = wrong_db
            mock_dcp_config.database = wrong_db
            mock_dcp_config.test_mode = CONFIG.test_mode
            mock_get.return_value = StaticSecretProvider()

            provider = DBCredentialProvider()
            with pytest.raises(SanitizedConnectionError) as exc_info:
                provider.connect_with_retry(psycopg2.connect, {})
            assert wrong_password not in str(exc_info.value)
            assert exc_info.value.__cause__ is None

    async def test_asyncpg_wrong_password_against_real_db(self):
        """
        End-to-end: attempts to connect to the test database and
        checks the real asyncpg auth failure is caught and sanitized.
        """
        _dbapi = AsyncAdapt_asyncpg_dbapi(asyncpg)
        wrong_password = "definitely-wrong-password-xyz"
        db = CONFIG.database
        wrong_db = DatabaseSettings(
            server=db.server,
            port=db.port,
            user=db.user,
            password=wrong_password,
            db=db.db,
            test_db=db.test_db,
        )

        def _connect_asyncpg(**kwargs):
            kw = {
                "host": kwargs.pop("host"),
                "port": kwargs.pop("port"),
                "user": kwargs.pop("user"),
                "password": kwargs.pop("password"),
                "database": kwargs.pop("dbname"),
            }
            kw.update(kwargs)
            raw_conn = await_only(asyncpg.connect(**kw))
            return AsyncAdapt_asyncpg_connection(_dbapi, raw_conn)

        with (
            patch("fides.config.secrets.static_provider.CONFIG") as mock_sp_config,
            patch("fides.common.db_credential_provider.CONFIG") as mock_dcp_config,
            patch(
                "fides.common.db_credential_provider.get_secret_provider"
            ) as mock_get,
        ):
            mock_sp_config.database = wrong_db
            mock_dcp_config.database = wrong_db
            mock_dcp_config.test_mode = CONFIG.test_mode
            mock_get.return_value = StaticSecretProvider()

            provider = DBCredentialProvider()
            with pytest.raises(SanitizedConnectionError) as exc_info:
                provider.connect_with_retry(_connect_asyncpg, {})
            assert wrong_password not in str(exc_info.value)
            assert exc_info.value.__cause__ is None


# --- Credential leakage ---


class TestCredentialLeakage:
    def test_password_not_in_sanitized_exception(self, static_provider):
        password = "v3ry-s3cret-p@ssw0rd!"
        connect_fn = MagicMock(side_effect=_make_password_leaking_error(password))
        with pytest.raises(SanitizedConnectionError) as exc_info:
            static_provider.connect_with_retry(connect_fn, {})
        assert password not in str(exc_info.value)
        assert password not in repr(exc_info.value)

    def test_password_not_in_log_output_during_retry(self, dynamic_provider, caplog):
        provider, _, mock_secret_provider, _ = dynamic_provider
        password = "super-secret-123"
        mock_secret_provider.get_secret.return_value = SecretValue(
            {"username": "u", "password": password}
        )
        connect_fn = MagicMock(
            side_effect=[
                _make_auth_error(pgcode="28P01"),
                _make_auth_error(pgcode="28P01"),
            ]
        )
        with pytest.raises(SanitizedConnectionError):
            provider.connect_with_retry(connect_fn, {})
        assert password not in caplog.text
