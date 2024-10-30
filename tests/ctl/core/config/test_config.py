# pylint: disable=missing-docstring, redefined-outer-name
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from fides.api.db.database import get_alembic_config
from fides.config import check_required_webserver_config_values, get_config
from fides.config.database_settings import DatabaseSettings
from fides.config.redis_settings import RedisSettings
from fides.config.security_settings import SecuritySettings

REQUIRED_ENV_VARS = {
    "FIDES__SECURITY__APP_ENCRYPTION_KEY": "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3",
    "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID": "fidesadmin",
    "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET": "fidesadminsecret",
    "FIDES__SECURITY__DRP_JWT_SECRET": "secret",
}


@pytest.mark.unit
def test_get_config_verbose() -> None:
    """Simple test to check the 'verbose' code path."""
    config = get_config(verbose=True, config_path_override="fakefiledoesntexist.toml")
    assert config


@pytest.mark.unit
class TestSecurityEnv:
    def test_security_invalid(self):
        """
        Test that an exception is raised when an invalid Enum value is used.
        """
        with pytest.raises(ValueError):
            SecuritySettings(env="invalid")


# Unit
@patch.dict(
    os.environ,
    REQUIRED_ENV_VARS,
    clear=True,
)
@pytest.mark.unit
def test_get_config(test_config_path: str) -> None:
    """Test that the actual config matches what the function returns."""
    config = get_config(test_config_path)
    assert config.database.user == "postgres"
    assert config.cli.server_url == "http://fides:8080"
    assert (
        config.credentials["postgres_1"]["connection_string"]
        == "postgresql+psycopg2://postgres:fides@fides-db:5432/fides_test"
    )


@patch.dict(
    os.environ,
    {
        "FIDES__CONFIG_PATH": "tests/ctl/test_default_config.toml",
    },
    clear=True,
)
@pytest.mark.unit
def test_get_config_default() -> None:
    """Check that get_config loads default values when given an empty TOML."""
    config = get_config()
    assert config.database.api_engine_pool_size == 50
    assert config.security.env == "prod"
    assert config.security.app_encryption_key == ""
    assert config.logging.level == "INFO"


@patch.dict(
    os.environ,
    REQUIRED_ENV_VARS,
    clear=True,
)
@pytest.mark.unit
def test_get_deprecated_api_config_from_file(test_deprecated_config_path: str) -> None:
    """
    Test that the deprecated API config values get written as database values.
    """
    config = get_config(test_deprecated_config_path)
    assert config.database.user == "postgres_deprecated"
    assert config.database.password == "fidesctl_deprecated"
    assert config.database.port == "5431"
    assert config.database.db == "fidesctl_deprecated"
    assert config.database.test_db == "fidesctl_test_deprecated"


@patch.dict(
    os.environ,
    {
        "FIDES__API__DATABASE_HOST": "test_host",
        "FIDES__API__DATABASE_NAME": "test_db_name",
        "FIDES__API__DATABASE_PASSWORD": "test_password",
        "FIDES__API__DATABASE_PORT": "1234",
        "FIDES__API__DATABASE_TEST_DATABASE_NAME": "test_test_db_name",
        "FIDES__API__DATABASE_USER": "phil_rules",
        **REQUIRED_ENV_VARS,
    },
    clear=True,
)
@pytest.mark.unit
def test_get_deprecated_api_config_from_env(test_config_path: str) -> None:
    """
    Test that the deprecated API config values get written as database values,
    when set via ENV variables.
    """

    config = get_config(test_config_path)
    assert config.database.db == "test_db_name"
    assert config.database.password == "test_password"
    assert config.database.port == "1234"
    assert config.database.server == "test_host"
    assert config.database.test_db == "test_test_db_name"
    assert config.database.user == "phil_rules"


@patch.dict(
    os.environ,
    {"FIDES__CONFIG_PATH": "", **REQUIRED_ENV_VARS},
    clear=True,
)
@pytest.mark.unit
def test_get_config_cache() -> None:
    "Test lru cache hits."

    config = get_config()
    cache_info = get_config.cache_info()
    assert config.user.encryption_key == "test_encryption_key"
    assert cache_info.hits == 0
    assert cache_info.misses == 1

    config = get_config()
    cache_info = get_config.cache_info()
    assert config.user.encryption_key == "test_encryption_key"
    assert cache_info.hits == 1
    assert cache_info.misses == 1

    config = get_config("tests/ctl/test_config.toml")
    cache_info = get_config.cache_info()
    assert config.user.encryption_key == "test_encryption_key"
    assert cache_info.hits == 1
    assert cache_info.misses == 2


@patch.dict(
    os.environ,
    {
        "FIDES__USER__ENCRYPTION_KEY": "test_key_one",
        "FIDES__CLI__SERVER_HOST": "test",
        "FIDES__CLI__SERVER_PORT": "8080",
        "FIDES__ADMIN_UI__URL": "http://localhost:3000/",
        "FIDES__CREDENTIALS__POSTGRES_1__CONNECTION_STRING": "postgresql+psycopg2://fides:env_variable.com:5439/fidesctl_test",
        **REQUIRED_ENV_VARS,
    },
    clear=True,
)
@pytest.mark.unit
def test_config_from_env_vars() -> None:
    """Test building a config from env vars."""
    config = get_config()

    assert config.user.encryption_key == "test_key_one"
    assert (
        config.cli.server_url == "http://test:8080"
    )  # No trailing slash because this is constructed from components
    assert config.admin_ui.url == "http://localhost:3000"  # Trailing slash is removed
    assert (
        config.credentials["postgres_1"]["connection_string"]
        == "postgresql+psycopg2://fides:env_variable.com:5439/fidesctl_test"
    )


@patch.dict(
    os.environ,
    {},
    clear=True,
)
@pytest.mark.unit
def test_database_url_test_mode_disabled() -> None:
    os.environ["FIDES__TEST_MODE"] = "False"
    database_settings = DatabaseSettings(
        user="postgres",
        password="fides",
        server="fides-db",
        port="5432",
        db="database",
        test_db="test_database",
    )
    assert (
        database_settings.async_database_uri
        == "postgresql+asyncpg://postgres:fides@fides-db:5432/database"
    )


@pytest.mark.unit
def test_password_escaped_by_database_settings_validation() -> None:
    database_settings = DatabaseSettings(
        user="postgres",
        password="fidesp@ssword",
        server="fides-db",
        port="5432",
        db="database",
        test_db="test_database",
    )
    assert (
        database_settings.async_database_uri
        == "postgresql+asyncpg://postgres:fidesp%40ssword@fides-db:5432/test_database"
    )

    assert (
        database_settings.sync_database_uri
        == "postgresql+psycopg2://postgres:fidesp%40ssword@fides-db:5432/test_database"
    )

    assert (
        database_settings.sqlalchemy_database_uri
        == "postgresql://postgres:fidesp%40ssword@fides-db:5432/database"
    )

    assert (
        database_settings.sqlalchemy_test_database_uri
        == "postgresql://postgres:fidesp%40ssword@fides-db:5432/test_database"
    )


def test_get_alembic_config_with_special_char_in_database_url():
    database_url = (
        "postgresql+psycopg2://postgres:fidesp%40ssword@fides-db:5432/test_database"
    )
    # this would fail with - ValueError: invalid interpolation syntax
    # if not handled
    get_alembic_config(database_url)


@patch.dict(
    os.environ,
    {
        "FIDES__CONFIG_PATH": "src/fides/data/sample_project/fides.toml",
    },
    clear=True,
)
def test_config_from_path() -> None:
    """Test reading config using the FIDES__CONFIG_PATH option."""
    config = get_config()
    print(os.environ)
    assert config.admin_ui.enabled is True
    assert config.execution.require_manual_request_approval is True


@patch.dict(
    os.environ,
    {
        "FIDES__DATABASE__SERVER": "envserver",
        "FIDES__DATABASE__PARAMS": '{"sslmode": "verify-full", "sslrootcert": "/etc/ssl/private/myca.crt"}',
        "FIDES__REDIS__HOST": "envhost",
        **REQUIRED_ENV_VARS,
    },
    clear=True,
)
def test_overriding_config_from_env_vars() -> None:
    """Test overriding config using ENV vars."""
    config = get_config()
    assert config.database.server == "envserver"
    assert config.redis.host == "envhost"
    assert config.security.app_encryption_key == "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"
    assert config.database.params == {
        "sslmode": "verify-full",
        "sslrootcert": "/etc/ssl/private/myca.crt",
    }


def test_config_app_encryption_key_validation() -> None:
    """Test APP_ENCRYPTION_KEY is validated to be exactly 32 characters."""
    app_encryption_key = "atestencryptionkeythatisvalidlen"

    with patch.dict(
        os.environ,
        {
            **REQUIRED_ENV_VARS,
            "FIDES__SECURITY__APP_ENCRYPTION_KEY": app_encryption_key,
        },
        clear=True,
    ):
        config = get_config()
        assert config.security.app_encryption_key == app_encryption_key


@pytest.mark.parametrize(
    "app_encryption_key",
    ["tooshortkey", "muchmuchmuchmuchmuchmuchmuchmuchtoolongkey"],
)
def test_config_app_encryption_key_validation_length_error(app_encryption_key) -> None:
    """Test APP_ENCRYPTION_KEY is validated to be exactly 32 characters."""
    with patch.dict(
        os.environ,
        {
            **REQUIRED_ENV_VARS,
            "FIDES__SECURITY__APP_ENCRYPTION_KEY": app_encryption_key,
        },
        clear=True,
    ):
        with pytest.raises(ValidationError) as err:
            get_config()
        assert "must be exactly 32 characters" in str(err.value)


@pytest.mark.parametrize(
    "log_level,expected_log_level",
    [
        ("DEBUG", "DEBUG"),
        ("debug", "DEBUG"),
        ("INFO", "INFO"),
        ("WARNING", "WARNING"),
        ("ERROR", "ERROR"),
        ("CRITICAL", "CRITICAL"),
    ],
)
def test_config_log_level(log_level, expected_log_level):
    """Test overriding the log level using ENV vars."""
    with patch.dict(
        os.environ,
        {
            "FIDES__LOGGING__LEVEL": log_level,
            **REQUIRED_ENV_VARS,
        },
        clear=True,
    ):
        config = get_config()
        assert config.logging.level == expected_log_level


def test_config_log_level_invalid():
    with patch.dict(
        os.environ,
        {
            "FIDES__LOGGING__LEVEL": "INVALID",
            **REQUIRED_ENV_VARS,
        },
        clear=True,
    ):
        with pytest.raises(ValidationError) as err:
            get_config()
        assert "Invalid LOG_LEVEL" in str(err.value)


class TestBuildingDatabaseValues:
    def test_validating_included_sqlalchemy_database_uri(self) -> None:
        """
        Test that injecting a pre-configured database uri is
        correctly used as opposed to building a new one.
        """
        incorrect_value = "incorrecthost"
        correct_value = "correcthosthost"
        database_settings = DatabaseSettings(
            server=incorrect_value,
            sqlalchemy_database_uri=f"postgresql://postgres:fides@{correct_value}:5432/fides",
        )
        assert incorrect_value not in database_settings.sqlalchemy_database_uri
        assert correct_value in database_settings.sqlalchemy_database_uri

    def test_validating_included_sqlalchemy_test_database_uri(self) -> None:
        """
        Test that injecting a pre-configured test database uri is
        correctly used as opposed to building a new one.
        """
        incorrect_value = "incorrecthost"
        correct_value = "correcthosthost"
        database_settings = DatabaseSettings(
            server=incorrect_value,
            sqlalchemy_test_database_uri=f"postgresql://postgres:fides@{correct_value}:5432/fides",
        )
        assert incorrect_value not in database_settings.sqlalchemy_test_database_uri
        assert correct_value in database_settings.sqlalchemy_test_database_uri

    def test_validating_included_sync_database_uri(self) -> None:
        """
        Test that injecting a pre-configured database uri is
        correctly used as opposed to building a new one.
        """
        incorrect_value = "incorrecthost"
        correct_value = "correcthosthost"
        database_settings = DatabaseSettings(
            server=incorrect_value,
            sync_database_uri=f"postgresql://postgres:fides@{correct_value}:5432/fides",
        )
        assert incorrect_value not in database_settings.sync_database_uri
        assert correct_value in database_settings.sync_database_uri

    def test_validating_included_async_database_uri(self) -> None:
        """
        Test that injecting a pre-configured database uri is
        correctly used as opposed to building a new one.
        """
        incorrect_value = "incorrecthost"
        correct_value = "correcthosthost"
        database_settings = DatabaseSettings(
            server=incorrect_value,
            async_database_uri=f"postgresql://postgres:fides@{correct_value}:5432/fides",
        )
        assert incorrect_value not in database_settings.async_database_uri
        assert correct_value in database_settings.async_database_uri

    def test_builds_with_params(self) -> None:
        """
        Test that when params are passed, they are correctly
        encoded as query parameters on the resulting database uris
        """
        os.environ["FIDES__TEST_MODE"] = "False"
        database_settings = DatabaseSettings(
            user="postgres",
            password="fides",
            server="fides-db",
            port="5432",
            db="database",
            params={
                "sslmode": "verify-full",
                "sslrootcert": "/etc/ssl/private/myca.crt",
            },
        )
        assert (
            database_settings.async_database_uri
            == "postgresql+asyncpg://postgres:fides@fides-db:5432/database?ssl=verify-full"
            # Q: But why! Where did the sslrootcert parameter go?
            # A: asyncpg cannot accept it, and an ssl context must be
            #    passed to the create_async_engine function.
            # Q: But wait! `ssl` is a different name than what we
            #    passed in the parameters!
            # A: That was more of a statement, but Jeopardy rules
            #    aside, asyncpg has a different set of names
            #    for these extremely standardized parameter names...
        )
        assert (
            database_settings.sync_database_uri
            == "postgresql+psycopg2://postgres:fides@fides-db:5432/database?sslmode=verify-full&sslrootcert=/etc/ssl/private/myca.crt"
        )


@pytest.mark.unit
def test_check_required_webserver_config_values_success(test_config_path: str) -> None:
    config = get_config(test_config_path)
    assert check_required_webserver_config_values(config=config) is None


@patch.dict(
    os.environ,
    {
        "FIDES__CONFIG_PATH": "tests/ctl/test_default_config.toml",
    },
    clear=True,
)
@pytest.mark.unit
def test_check_required_webserver_config_values_error(capfd) -> None:
    config = get_config()
    assert config.security.app_encryption_key is ""

    with pytest.raises(SystemExit):
        check_required_webserver_config_values(config=config)

    out, _ = capfd.readouterr()
    assert "app_encryption_key" in out
    assert "oauth_root_client_id" in out
    assert "oauth_root_client_secret" in out


@patch.dict(
    os.environ,
    {
        "FIDES__CONFIG_PATH": "src/fides/data/sample_project/fides.toml",
    },
    clear=True,
)
def test_check_required_webserver_config_values_success_from_path() -> None:
    config = get_config()
    assert check_required_webserver_config_values(config=config) is None


class TestBuildingRedisURLs:
    def test_generic(self) -> None:
        redis_settings = RedisSettings()
        assert redis_settings.connection_url == "redis://:testpassword@redis:6379/"

    def test_configured(self) -> None:
        redis_settings = RedisSettings(
            db_index=1, host="myredis", port="6380", password="supersecret"
        )
        assert redis_settings.connection_url == "redis://:supersecret@myredis:6380/1"

    def test_tls(self) -> None:
        redis_settings = RedisSettings(ssl=True, ssl_cert_reqs="none")
        assert (
            redis_settings.connection_url
            == "rediss://:testpassword@redis:6379/?ssl_cert_reqs=none"
        )

    def test_tls_custom_ca(self) -> None:
        redis_settings = RedisSettings(ssl=True, ssl_ca_certs="/path/to/my/cert.crt")
        assert (
            redis_settings.connection_url
            == "rediss://:testpassword@redis:6379/?ssl_cert_reqs=required&ssl_ca_certs=/path/to/my/cert.crt"
        )


@patch.dict(
    os.environ,
    {
        "FIDES__CONSENT__TCF_ENABLED": "true",
        "FIDES__CONSENT__AC_ENABLED": "true",
    },
    clear=True,
)
@pytest.mark.unit
def test_tcf_and_ac_mode() -> None:
    """Test that AC mode cannot be true without TCF mode on"""
    config = get_config()
    assert config.consent.tcf_enabled
    assert config.consent.ac_enabled


@patch.dict(
    os.environ,
    {
        "FIDES__CONSENT__TCF_ENABLED": "false",
        "FIDES__CONSENT__AC_ENABLED": "true",
    },
    clear=True,
)
@pytest.mark.unit
def test_get_config_ac_mode_without_tc_mode() -> None:
    """Test that AC mode cannot be true without TCF mode on"""
    with pytest.raises(ValidationError) as exc:
        get_config()

    assert (
        exc.value.errors()[0]["msg"]
        == "Value error, AC cannot be enabled unless TCF mode is also enabled."
    )
