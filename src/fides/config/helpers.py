"""This module contains logic related to loading/manipulation/writing the config."""

import os
from os import environ
from pathlib import Path
from re import compile as regex
from typing import Any, Dict, List, Union

from click import echo
from toml import dump, load

DEFAULT_CONFIG_PATH = ".fides/fides.toml"


def load_file(file_names: Union[List[Path], List[str]]) -> str:
    """
    Load a file from the first matching location.

    In order, will check:
    - A path set at ENV variable FIDES__CONFIG_PATH
    - The current directory
    - The parent directory
    - Two directories up for the current directory
    - The parent_directory/.fides
    - users home (~) directory
    raises FileNotFound if none is found
    """

    possible_directories = [
        os.getenv("FIDES__CONFIG_PATH"),
        os.curdir,
        os.pardir,
        os.path.abspath(os.path.join(os.curdir, "..", "..")),
        os.path.join(os.pardir, ".fides"),
        os.path.expanduser("~"),
    ]

    directories = [d for d in possible_directories if d]

    for dir_str in directories:
        for file_name in file_names:
            possible_location = os.path.join(dir_str, file_name)
            if possible_location and os.path.isfile(possible_location):
                return possible_location

    raise FileNotFoundError


def get_config_from_file(
    config_path_override: str,
    section: str,
    option: str,
) -> Union[str, bool, int, None]:
    """
    Return the value currently written to the config file for the
    specified `section.option`.
    """

    config_path = config_path_override or load_file(file_names=[DEFAULT_CONFIG_PATH])
    current_config = load(config_path)

    config_section = current_config.get(section)
    if config_section is not None:
        config_option = config_section.get(option)
        if config_option is not None:
            return config_option

    return None


def update_config_file(  # type: ignore
    updates: Dict[str, Dict[str, Any]],
    config_path_override: str,
) -> None:
    """
    Overwrite the existing config file with a new version that includes the desired `updates`.

    :param updates: A nested `dict`, where top-level keys correspond to configuration sections and top-level values contain `dict`s whose key/value pairs correspond to the desired option/value updates.
    :param config_path: The path to the current configuration file.
    """

    config_path = config_path_override or load_file(file_names=[DEFAULT_CONFIG_PATH])
    current_config = load(config_path)

    for key, value in updates.items():
        if key in current_config:
            current_config[key].update(value)
        else:
            current_config.update({key: value})

    with open(config_path, "w", encoding="utf-8") as config_file:
        dump(current_config, config_file)

    echo(f"Updated {config_path}:")

    for key, value in updates.items():
        for subkey, val in value.items():
            echo(f"\tSet {key}.{subkey} = {val}")


def handle_deprecated_fields(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Custom logic for handling deprecated values."""

    if settings.get("api") and not settings.get("database"):
        api_settings = settings.pop("api")
        database_settings = {}
        database_settings["user"] = api_settings.get("database_user")
        database_settings["password"] = api_settings.get("database_password")
        database_settings["server"] = api_settings.get("database_host")
        database_settings["port"] = api_settings.get("database_port")
        database_settings["db"] = api_settings.get("database_name")
        database_settings["test_db"] = api_settings.get("test_database_name")
        settings["database"] = database_settings

    return settings


def handle_deprecated_env_variables(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom logic for handling deprecated ENV variable configuration.
    """

    deprecated_env_vars = regex(r"FIDES__API__(\w+)")

    for key, val in environ.items():
        match = deprecated_env_vars.search(key)
        if match:
            setting = match.group(1).lower()
            setting = setting[setting.startswith("database_") and len("database_") :]
            if setting == "host":
                setting = "server"
            if setting == "name":
                setting = "db"
            if setting == "test_database_name":
                setting = "test_db"

            settings["database"][setting] = val

    return settings
