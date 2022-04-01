import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from fidesctl.core.config import APISettings, get_config


# Unit
@pytest.mark.unit
def test_get_config():
    """Test that the actual config matches what the function returns."""
    config = get_config("tests/test_config.toml")
    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert config.cli.server_url == "http://fidesctl:8080"


@pytest.mark.unit
def test_default_config():
    "Test building a config from default values."
    os.environ["FIDESCTL_CONFIG_PATH"] = ""
    os.chdir("/fides")
    config = get_config()
    os.chdir("/fides/fidesctl")

    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert config.cli.server_url == "http://localhost"


@patch.dict(
    os.environ,
    {
        "FIDESCTL_CONFIG_PATH": "",
        "FIDESCTL__USER__USER_ID": "2",
        "FIDESCTL__CLI__SERVER_HOST": "http://test",
        "FIDESCTL__CLI__SERVER_PORT": "8080",
    },
    clear=True,
)
@pytest.mark.unit
def test_config_from_env_vars():
    "Test building a config from env vars."
    config = get_config()
    os.chdir("/fides/fidesctl")

    assert config.user.user_id == "2"
    assert config.user.api_key == "test_api_key"
    assert config.cli.server_url == "http://test:8080"


@patch.dict(
    os.environ,
    {
        "FIDESCTL_CONFIG_PATH": "",
        "FIDESCTL__USER__USER_ID": "2",
        "FIDESCTL__CLI__SERVER_HOST": "test",
        "FIDESCTL__CLI__SERVER_PORT": "8080",
    },
    clear=True,
)
@pytest.mark.unit
def test_invalid_config_value_from_env_vars():
    "Test building a config from env vars."
    with pytest.raises(ValidationError):
        config = get_config()

    assert True


@pytest.mark.unit
def test_database_url_test_mode_disabled():
    os.environ["FIDESCTL_TEST_MODE"] = "False"
    api_settings = APISettings(
        test_database_name="test_database_url", database_name="database_url"
    )
    assert (
        api_settings.database_url == "postgres:fidesctl@fidesctl-db:5432/database_url"
    )


@pytest.mark.unit
def test_database_url_test_mode_enabled():
    os.environ["FIDESCTL_TEST_MODE"] = "True"
    api_settings = APISettings(
        test_database_name="test_database_url", database_name="database_url"
    )
    assert (
        api_settings.database_url
        == "postgres:fidesctl@fidesctl-db:5432/test_database_url"
    )
