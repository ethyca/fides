import os

import pytest

from fidesctl.core.config import get_config, FidesctlConfig


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

    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert config.cli.server_url == "http://localhost:8080"


@pytest.mark.unit
def test_config_from_env_vars():
    "Test building a config from env vars."
    os.environ["FIDESCTL_CONFIG_PATH"] = ""
    os.environ["FIDESCTL__USER__user_id"] = "2"
    os.environ["FIDESCTL__CLI__SERVER_URL"] = "test"
    os.chdir("/fides")
    config = get_config()

    assert config.user.user_id == "2"
    assert config.user.api_key == "test_api_key"
    assert config.cli.server_url == "test"
