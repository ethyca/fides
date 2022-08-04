# pylint: disable=missing-docstring, redefined-outer-name
import os
from unittest.mock import patch

import pytest

from fidesctl.ctl.core.config import get_config
from fidesctl.ctl.core.config.database_settings import FidesctlDatabaseSettings


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
    assert config.cli.server_url == "http://fidesctl:8080"
    assert (
        config.credentials["postgres_1"]["connection_string"]
        == "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test"
    )


@patch.dict(
    os.environ,
    {},
    clear=True,
)
@pytest.mark.unit
def test_get_deprecated_api_config(test_deprecated_config_path: str) -> None:
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
    {"FIDESCTL_CONFIG_PATH": ""},
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
        "FIDES__CONFIG_PATH": "/fides/.fides/",
        "FIDESCTL__USER__USER_ID": "2",
        "FIDESCTL__CLI__SERVER_HOST": "test",
        "FIDESCTL__CLI__SERVER_PORT": "8080",
        "FIDESCTL__CREDENTIALS__POSTGRES_1__CONNECTION_STRING": "postgresql+psycopg2://fidesctl:env_variable.com:5439/fidesctl_test",
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
        == "postgresql+psycopg2://fidesctl:env_variable.com:5439/fidesctl_test"
    )


@pytest.mark.unit
def test_database_url_test_mode_disabled() -> None:
    os.environ["FIDESCTL_TEST_MODE"] = "False"
    database_settings = FidesctlDatabaseSettings(
        user="postgres",
        password="fidesctl",
        server="fidesctl-db",
        port="5432",
        db="database",
        test_db="test_database",
    )
    assert (
        database_settings.async_database_uri
        == "postgresql+asyncpg://postgres:fidesctl@fidesctl-db:5432/database"
    )
