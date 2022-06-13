import logging
import os
from unittest.mock import patch

import pytest
from fideslib.core.config import get_config
from pydantic import ValidationError

from fidesops.core.config import FidesopsConfig


def test_config_from_default() -> None:
    "Test building a config from default local TOML"
    config = get_config(FidesopsConfig)

    assert config.database.SERVER == "db"
    assert config.redis.HOST == "redis"
    assert config.security.APP_ENCRYPTION_KEY == "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"


@patch.dict(
    os.environ,
    {
        "FIDES__CONFIG_PATH": "data/config/",
    },
    clear=True,
)
def test_config_from_path() -> None:
    """Test reading config using the FIDESOPS__CONFIG_PATH option."""
    config = get_config(FidesopsConfig)
    assert config.database.SERVER == "testserver"
    assert config.redis.HOST == "testredis"
    assert config.security.APP_ENCRYPTION_KEY == "atestencryptionkeythatisvalidlen"


@patch.dict(
    os.environ,
    {
        "FIDESOPS__DATABASE__SERVER": "envserver",
        "FIDESOPS__REDIS__HOST": "envhost",
    },
    clear=True,
)
def test_config_from_env_vars() -> None:
    """Test overriding config using ENV vars."""
    config = get_config(FidesopsConfig)
    assert config.database.SERVER == "envserver"
    assert config.redis.HOST == "envhost"
    assert config.security.APP_ENCRYPTION_KEY == "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"


def test_config_app_encryption_key_validation() -> None:
    """Test APP_ENCRYPTION_KEY is validated to be exactly 32 characters."""
    app_encryption_key = "atestencryptionkeythatisvalidlen"

    with patch.dict(
        os.environ,
        {
            "FIDESOPS__SECURITY__APP_ENCRYPTION_KEY": app_encryption_key,
        },
        clear=True,
    ):
        config = get_config(FidesopsConfig)
        assert config.security.APP_ENCRYPTION_KEY == app_encryption_key


@pytest.mark.parametrize(
    "app_encryption_key",
    ["tooshortkey", "muchmuchmuchmuchmuchmuchmuchmuchtoolongkey"],
)
def test_config_app_encryption_key_validation_length_error(app_encryption_key) -> None:
    """Test APP_ENCRYPTION_KEY is validated to be exactly 32 characters."""
    with patch.dict(
        os.environ,
        {
            "FIDESOPS__SECURITY__APP_ENCRYPTION_KEY": app_encryption_key,
        },
        clear=True,
    ):
        with pytest.raises(ValidationError) as err:
            get_config(FidesopsConfig)
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
            "FIDESOPS__SECURITY__LOG_LEVEL": log_level,
        },
        clear=True,
    ):
        config = get_config(FidesopsConfig)
        assert config.security.LOG_LEVEL == expected_log_level


def test_config_log_level_invalid():
    with patch.dict(
        os.environ,
        {
            "FIDESOPS__SECURITY__LOG_LEVEL": "INVALID",
        },
        clear=True,
    ):
        with pytest.raises(ValidationError) as err:
            get_config(FidesopsConfig)
        assert "Invalid LOG_LEVEL" in str(err.value)
