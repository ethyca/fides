import sys
from os import getenv
from typing import Any, Dict, Union

from click import echo
from fideslib.core.config import load_file
from toml import dump, load

DEFAULT_CONFIG_PATH = ".fides/fides.toml"


def get_test_mode() -> bool:
    test_mode = getenv("FIDES__TEST_MODE", "").lower() == "true"
    return test_mode


def get_config_from_file(
    config_path_override: str,
    section: str,
    option: str,
) -> Union[str, bool, int, None]:
    """
    Return the value currently written to the config file for the specified `section.option`.
    """

    try:
        config_path = config_path_override or load_file(
            file_names=[DEFAULT_CONFIG_PATH]
        )
    except FileNotFoundError as error:
        raise error

    current_config = load(config_path)

    config_section = current_config.get(section)
    if config_section is not None:
        config_option = config_section.get(option)
        if config_option is not None:
            return config_option

    return None


def check_if_required_config_vars_are_configured() -> None:
    app_encryption_key: Union[str, int, None] = getenv(
        "FIDES__SECURITY__APP_ENCRYPTION_KEY"
    )
    oauth_root_client_id: Union[str, int, None] = getenv(
        "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID"
    )
    oauth_root_client_secret: Union[str, int, None] = getenv(
        "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET"
    )
    try:
        if not app_encryption_key:
            app_encryption_key = get_config_from_file(
                "", "security", "app_encryption_key"
            )
        if not oauth_root_client_id:
            oauth_root_client_id = get_config_from_file(
                "", "security", "oauth_root_client_id"
            )
        if not oauth_root_client_secret:
            oauth_root_client_secret = get_config_from_file(
                "", "security", "oauth_root_client_secret"
            )
    except FileNotFoundError:
        pass

    missing_required_config_vars = []
    if app_encryption_key is None:
        missing_required_config_vars.append(
            ("security.app_encryption_key", "FIDES__SECURITY__APP_ENCRYPTION_KEY")
        )
    if oauth_root_client_id is None:
        missing_required_config_vars.append(
            ("security.oauth_root_client_id", "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID")
        )
    if oauth_root_client_secret is None:
        missing_required_config_vars.append(
            (
                "security.oauth_root_client_secret",
                "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET",
            )
        )

    if len(missing_required_config_vars) > 0:
        print(
            "There are missing required config variables. Please add the following config variables to either the `fides.toml` file or your environment variable to start Fides: "
        )
        for missing_var in missing_required_config_vars:
            print(f"fides.toml: {missing_var[0]} or ENV VAR: {missing_var[1]}")
        sys.exit(1)


def update_config_file(  # type: ignore
    updates: Dict[str, Dict[str, Any]],
    config_path_override: str,
) -> None:
    """
    Overwrite the existing config file with a new version that includes the desired `updates`.

    :param updates: A nested `dict`, where top-level keys correspond to configuration sections and top-level values contain `dict`s whose key/value pairs correspond to the desired option/value updates.
    :param config_path: The path to the current configuration file.
    """

    try:
        config_path = config_path_override or load_file(
            file_names=[DEFAULT_CONFIG_PATH]
        )
    except FileNotFoundError as error:
        raise error

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
