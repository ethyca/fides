import os
from errno import ENOENT
from typing import Any, Dict

from click import echo
from toml import dump, load


def get_config_path(config_path: str) -> str:
    """
    Attempt to read config file from:
    a) passed in configuration, if it exists
    b) env var FIDESCTL_CONFIG_PATH
    b) local directory
    c) home directory

    Returns the path of the first configuration file found.
    """

    default_file_name = ".fides/fidesctl.toml"

    possible_config_locations = [
        config_path,
        os.getenv("FIDESCTL_CONFIG_PATH", ""),
        os.path.join(os.curdir, default_file_name),
        os.path.join(os.path.expanduser("~"), default_file_name),
    ]

    for file_location in possible_config_locations:
        if file_location != "" and os.path.isfile(file_location):
            return file_location

    raise FileNotFoundError(ENOENT, os.strerror(ENOENT), config_path)


def update_config_file(  # type: ignore
    updates: Dict[str, Dict[str, Any]],
    config_path: str,
) -> None:
    """
    Overwrite the existing config file with a new version that includes the desired `updates`.

    :param updates: A nested `dict`, where top-level keys correspond to configuration sections and top-level values contain `dict`s whose key/value pairs correspond to the desired option/value updates.
    :param config_path: The path to the current configuration file.
    """

    try:
        config_path = get_config_path(config_path)
    except FileNotFoundError as error:
        raise error

    current_config = load(config_path)

    for key, value in updates.items():
        if key in current_config:
            current_config[key].update(value)
        else:
            current_config.update({key: value})

    with open(config_path, "w") as config_file:
        dump(current_config, config_file)

    echo(f"Updated {config_file}:")

    for key, value in updates.items():
        for subkey, val in value.items():
            echo(f"\tSet {key}.{subkey} = {val}")
