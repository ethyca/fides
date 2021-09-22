import pytest

from fidesctl.core.config import get_config, FidesConfig


# Unit
@pytest.mark.unit
def test_get_config():
    """Test that the actual config matches what the function returns."""
    config = get_config("tests/test_config.toml")
    assert config.user.user_id == "1"
    assert config.user.api_key == "test_api_key"
    assert config.cli.server_url == "http://fidesctl:8080"
