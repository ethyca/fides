# pylint: disable=missing-docstring, redefined-outer-name
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from fides.config import get_config
from fides.config.privacy_center_settings import PrivacyCenterSettings

REQUIRED_ENV_VARS = {
    "FIDES__SECURITY__APP_ENCRYPTION_KEY": "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3",
    "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID": "fidesadmin",
    "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET": "fidesadminsecret",
    "FIDES__SECURITY__DRP_JWT_SECRET": "secret",
}


@pytest.mark.unit
class TestPrivacyCenterSettings:
    """Test class for PrivacyCenterSettings configuration."""

    def test_privacy_center_settings_defaults(self):
        """Test that PrivacyCenterSettings has correct default values."""
        settings = PrivacyCenterSettings()
        assert settings.url is None

    @patch.dict(
        os.environ,
        {
            "FIDES__PRIVACY_CENTER__URL": "https://privacy.example.com/",
        },
        clear=True,
    )
    def test_privacy_center_settings_from_env(self):
        """Test PrivacyCenterSettings configuration from environment variables."""
        settings = PrivacyCenterSettings()
        assert (
            str(settings.url) == "https://privacy.example.com"
        )  # Trailing slash removed

    @patch.dict(
        os.environ,
        {
            "FIDES__PRIVACY_CENTER__URL": "https://privacy.example.com",
        },
        clear=True,
    )
    def test_privacy_center_settings_url_without_trailing_slash(self):
        """Test that URL without trailing slash is preserved."""
        settings = PrivacyCenterSettings()
        assert str(settings.url) == "https://privacy.example.com"

    def test_privacy_center_settings_invalid_url(self):
        """Test that invalid URL raises validation error."""
        with pytest.raises(ValidationError):
            PrivacyCenterSettings(url="not-a-valid-url")

    @patch.dict(
        os.environ,
        {
            "FIDES__PRIVACY_CENTER__URL": "invalid-url",
        },
        clear=True,
    )
    def test_privacy_center_settings_invalid_url_from_env(self):
        """Test that invalid URL from environment raises validation error."""
        with pytest.raises(ValidationError):
            PrivacyCenterSettings()


@patch.dict(
    os.environ,
    {
        "FIDES__PRIVACY_CENTER__URL": "https://privacy.example.com/",
        **REQUIRED_ENV_VARS,
    },
    clear=True,
)
@pytest.mark.unit
def test_privacy_center_config_integration():
    """Test that PrivacyCenterSettings integrates correctly with main config system."""
    config = get_config()
    assert str(config.privacy_center.url) == "https://privacy.example.com"


@patch.dict(
    os.environ,
    {
        **REQUIRED_ENV_VARS,
    },
    clear=True,
)
@pytest.mark.unit
def test_privacy_center_config_defaults_in_main_config():
    """Test that privacy center defaults are correctly set in main config."""
    config = get_config()
    assert config.privacy_center.url is None
