# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Generator

import pytest
from py._path.local import LocalPath
from toml import dump, load

from fidesctl.core.config import FidesctlConfig
from fidesctl.core.config.utils import update_config_file


@pytest.fixture
def test_change_config() -> Generator:
    """Create a dictionary to be used as an example config file"""

    yield {"cli": {"analytics_id": "initial_id"}}


@pytest.mark.unit
def test_update_config_file_new_value(
    test_change_config: FidesctlConfig, tmpdir: LocalPath
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
