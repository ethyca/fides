# pylint: disable=missing-docstring, redefined-outer-name
import os
from types import SimpleNamespace
from typing import Generator

import pytest
from py._path.local import LocalPath
from toml import dump, load

from fides.config import FidesConfig
from fides.config.cli_settings import CLISettings
from fides.config.helpers import update_config_file
from fides.config.utils import replace_config_value


@pytest.fixture
def test_change_config() -> Generator:
    """Create a dictionary to be used as an example config file"""

    yield {"cli": {"analytics_id": "initial_id"}}


@pytest.mark.unit
def test_replace_config_value(tmpdir: LocalPath) -> None:
    config_dir = tmpdir / ".fides"
    os.mkdir(config_dir)
    config_path = config_dir / "fides.toml"

    expected_result = "# test_value = true"
    test_file = "# test_value = false"

    with open(config_path, "w") as config_file:
        config_file.write(test_file)

    replace_config_value(str(tmpdir), "test_value", "false", "true")

    with open(config_path, "r") as config_file:
        actual_result = config_file.read()

    print(actual_result)
    assert actual_result == expected_result


@pytest.mark.unit
def test_update_config_file_new_value(
    test_change_config: FidesConfig, tmpdir: LocalPath
) -> None:
    """
    Create an example config.toml and validate both updating an
    existing config setting and adding a new section and setting.
    """

    config_path = os.path.join(tmpdir, "test_writing_config.toml")

    with open(config_path, "w") as config_file:
        dump(test_change_config, config_file)

    config_updates = {
        "cli": {"analytics_id": "updated_id"},
        "user": {"analytics_opt_out": True},
    }

    update_config_file(config_updates, config_path)

    updated_config = load(config_path)

    assert updated_config["cli"] is not None, "updated_config.cli should exist"
    assert (
        updated_config["cli"]["analytics_id"] == "updated_id"
    ), "updated_config.cli.analytics_id should be 'updated_id'"
    assert updated_config["user"] is not None, "updated_config.user should exist"
    assert updated_config["user"][
        "analytics_opt_out"
    ], "updated_config.user.analytics_opt_out should be True"


@pytest.mark.unit
def test_cli_settings_get_server_url() -> None:
    """Test the get_server_url method of CLISettings"""

    # no path
    validation_info = SimpleNamespace(
        data={
            "server_host": "test_host",
            "server_protocol": "http",
            "server_port": "8080",
        }
    )
    server_url = CLISettings.get_server_url(info=validation_info, value="")
    assert server_url == "http://test_host:8080"

    # specifying a path
    validation_info.data["server_host"] = "test_host/api/v1"
    server_url = CLISettings.get_server_url(info=validation_info, value="")
    assert server_url == "http://test_host:8080"
