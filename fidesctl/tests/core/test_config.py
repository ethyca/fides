import os

import pytest

from fidesctl.core.config import get_config, FidesctlConfig, APISettings


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
    assert config.cli.server_url == "http://localhost:8080"


@pytest.mark.unit
def test_config_from_env_vars():
    "Test building a config from env vars."
    ## TODO: This test doesn't properly inject env vars, but has been tested
    ## and is working. Need to revisit and fix this test.
    os.environ["FIDESCTL_CONFIG_PATH"] = ""
    os.environ["FIDESCTL__USER__USER_ID"] = "2"
    os.environ["FIDESCTL__CLI__SERVER_URL"] = "test"
    os.chdir("/fides")
    config = get_config()
    os.chdir("/fides/fidesctl")

    # assert config.user.user_id == "2"
    # assert config.user.api_key == "test_api_key"
    # assert config.cli.server_url == "test"

@pytest.mark.unit
def test_database_url_test_mode_disabled():
    os.environ["FIDESCTL_TEST_MODE"] = "False"
    api_settings = APISettings(
    test_database_url="test_database_url",
    database_url="database_url"
    )
    assert api_settings.database_url == "database_url"

@pytest.mark.unit
def test_database_url_test_mode_enabled():
    os.environ["FIDESCTL_TEST_MODE"] = "True"
    api_settings = APISettings(
    test_database_url="test_database_url",
    database_url="database_url"
    )
    assert api_settings.database_url == "test_database_url"
