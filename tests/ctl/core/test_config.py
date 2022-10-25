# pylint: disable=missing-docstring, redefined-outer-name
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from fides.ctl.core.config import get_config
from fides.ctl.core.config.database_settings import DatabaseSettings


# Unit
@patch.dict(
    os.environ,
    {},
    clear=True,
)
@pytest.mark.unit
def test_get_config(test_config_path: str) -> None:
    """Test that the actual config matches what the function returns."""
    config = get_config(test_config_path)
    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert config.database.user == "postgres"
    assert config.cli.server_url == "http://fides:8080"
    assert (
        config.credentials["postgres_1"]["connection_string"]
        == "postgresql+psycopg2://postgres:fides@fides-db:5432/fides_test"
    )


@patch.dict(
    os.environ,
    {},
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
    {"FIDES__CONFIG_PATH": ""},
    clear=True,
)
@pytest.mark.unit
def test_get_config_cache() -> None:
    "Test lru cache hits."
    config = get_config()
    cache_info = get_config.cache_info()
    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert cache_info.hits == 0
    assert cache_info.misses == 1

    config = get_config()
    cache_info = get_config.cache_info()
    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert cache_info.hits == 1
    assert cache_info.misses == 1

    config = get_config("tests/test_config.toml")
    cache_info = get_config.cache_info()
    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert cache_info.hits == 1
    assert cache_info.misses == 2


@pytest.mark.unit
def test_default_config() -> None:
    "Test building a config from default values."
    os.environ["FIDES__CONFIG_PATH"] = ""
    config = get_config()
    os.chdir("/fides")

    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"


@patch.dict(
    os.environ,
    {
        "FIDES__USER__USER_ID": "2",
        "FIDES__CLI__SERVER_HOST": "test",
        "FIDES__CLI__SERVER_PORT": "8080",
        "FIDES__CREDENTIALS__POSTGRES_1__CONNECTION_STRING": "postgresql+psycopg2://fides:env_variable.com:5439/fidesctl_test",
    },
    clear=True,
)
@pytest.mark.unit
def test_config_from_env_vars() -> None:
    "Test building a config from env vars."
    config = get_config()

    assert config.user.user_id == "2"
    assert config.user.api_key == "test_api_key"
    assert config.cli.server_url == "http://test:8080"
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


@patch.dict(
    os.environ,
    {},
    clear=True,
)
def test_config_from_default() -> None:
    """Test building a config from the local project TOML."""
    config = get_config()

    assert config.database.server == "fides-db"
    assert config.redis.host == "redis"
    assert config.security.app_encryption_key == "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"


@patch.dict(
    os.environ,
    {
        "FIDES__CONFIG_PATH": "data/config/fides.test_env.toml",
    },
    clear=True,
)
def test_config_from_path() -> None:
    """Test reading config using the FIDES__CONFIG_PATH option."""
    config = get_config()
    print(os.environ)
    assert config.security.app_encryption_key == "atestencryptionkeythatisvalidlen"
    assert config.admin_ui.enabled == True
    assert config.execution.require_manual_request_approval == True


@patch.dict(
    os.environ,
    {
        "FIDES__DATABASE__SERVER": "envserver",
        "FIDES__REDIS__HOST": "envhost",
    },
    clear=True,
)
def test_overriding_config_from_env_vars() -> None:
    """Test overriding config using ENV vars."""
    config = get_config()
    assert config.database.server == "envserver"
    assert config.redis.host == "envhost"
    assert config.security.app_encryption_key == "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"


def test_config_app_encryption_key_validation() -> None:
    """Test APP_ENCRYPTION_KEY is validated to be exactly 32 characters."""
    app_encryption_key = "atestencryptionkeythatisvalidlen"

    with patch.dict(
        os.environ,
        {
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
        },
        clear=True,
    ):
        with pytest.raises(ValidationError) as err:
            get_config()
        assert "Invalid LOG_LEVEL" in str(err.value)
