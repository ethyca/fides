# pylint: disable=missing-function-docstring, redefined-outer-name

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fideslib.core.config import (
    DatabaseSettings,
    SecuritySettings,
    get_config,
    load_toml,
)
from fideslib.exceptions import MissingConfig
from pydantic import ValidationError

ROOT_PATH = Path().absolute()


def test_config_app_encryption_key_validation() -> None:
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
def test_config_app_encryption_key_validation_error(app_encryption_key) -> None:
    with patch.dict(
        os.environ,
        {
            "FIDES__SECURITY__APP_ENCRYPTION_KEY": app_encryption_key,
        },
        clear=True,
    ):
        with pytest.raises(ValidationError) as exc:
            get_config()

        assert "must be exactly 32 characters" in str(exc.value)


@pytest.fixture
def config_dict(fides_toml_path):
    yield load_toml([fides_toml_path])


@patch.dict(
    os.environ,
    {
        "FIDES__CONFIG_PATH": str(ROOT_PATH / "tests" / "assets"),
    },
    clear=True,
)
def test_config_from_path() -> None:
    """Test reading config using the FIDESOPS__CONFIG_PATH option."""
    config = get_config()
    assert config.database.server == "testserver"
    assert config.security.app_encryption_key == "atestencryptionkeythatisvalidlen"


def test_database_settings_sqlalchemy_database_uri_str(config_dict):
    expected = "postgresql://someuri:216f4b49bea5da4f84f05288258471852c3e325cd336821097e1e65ff92b528a@db:5432/test"
    config_dict["database"]["sqlalchemy_database_uri"] = expected
    settings = DatabaseSettings.parse_obj(config_dict["database"])

    assert settings.sqlalchemy_database_uri == expected


def test_database_settings_sqlalchemy_test_database_uri_str(config_dict):
    expected = "postgresql://someuri:216f4b49bea5da4f84f05288258471852c3e325cd336821097e1e65ff92b528a@db:5432/test"
    config_dict["database"]["sqlalchemy_test_database_uri"] = expected
    settings = DatabaseSettings.parse_obj(config_dict["database"])

    assert settings.sqlalchemy_test_database_uri == expected


@pytest.mark.parametrize(
    "file_names", ["bad.toml", ["bad.toml"], ["bad.toml", "file.toml"]]
)
def test_get_config_bad_files(file_names, caplog):
    with pytest.raises(MissingConfig):
        get_config(file_names=file_names)

    assert "could not be loaded" in caplog.text


def test_missing_config_file():
    with pytest.raises(MissingConfig):
        get_config(file_names=["bad.toml"])


def test_security_cors_str(config_dict):
    expected = "http://localhost.com"
    config_dict["security"]["cors_origins"] = expected
    settings = SecuritySettings.parse_obj(config_dict["security"])

    assert settings.cors_origins[0] == expected


def test_security_invalid_cors(config_dict):
    config_dict["security"]["cors_origins"] = 1

    with pytest.raises(ValueError):
        SecuritySettings.parse_obj(config_dict["security"])


def test_security_invalid_app_encryption_key(config_dict):
    config_dict["security"]["app_encryption_key"] = "a"

    with pytest.raises(ValueError):
        SecuritySettings.parse_obj(config_dict["security"])


def test_security_missing_oauth_root_client_secret(config_dict):
    del config_dict["security"]["oauth_root_client_secret"]

    with pytest.raises(MissingConfig):
        SecuritySettings.parse_obj(config_dict["security"])


@pytest.mark.parametrize(
    "cors_origins, expected",
    [
        ("*", ["*"]),
        ("http://localhost", ["http://localhost"]),
        (["*"], ["*"]),
        (
            [
                "https://localhost",
                "http://localhost:8080",
                "http://localhost:3000",
                "http://localhost:3001",
            ],
            [
                "https://localhost",
                "http://localhost:8080",
                "http://localhost:3000",
                "http://localhost:3001",
            ],
        ),
    ],
)
def tests_cors_origins(cors_origins, expected, config_dict):
    config_dict["security"]["cors_origins"] = cors_origins
    settings = SecuritySettings.parse_obj(config_dict["security"])

    assert settings.cors_origins == expected


@pytest.mark.parametrize(
    "url",
    [
        "im_bad",
        "localhost.com",
        "http://local host.com",
        "no://localhost.com",
    ],
)
def test_cors_origins_invalid(url, config_dict):
    config_dict["security"]["cors_origins"] = url
    with pytest.raises(ValueError):
        SecuritySettings.parse_obj(config_dict["security"])
