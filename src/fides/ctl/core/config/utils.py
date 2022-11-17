from os import getenv
from typing import Any, Dict, Union

from click import echo
from fideslib.core.config import load_file
from toml import dump, load

from fides.ctl.core.utils import echo_red

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


def check_required_webserver_config_values() -> None:
    """Check for required env vars and print a user-friendly error message."""
    required_config_dict = {
        "app_encryption_key": {
            "env_var": "FIDES__SECURITY__APP_ENCRYPTION_KEY",
            "config_subsection": "security",
        },
        "oauth_root_client_id": {
            "env_var": "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID",
            "config_subsection": "security",
        },
        "oauth_root_client_secret": {
            "env_var": "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET",
            "config_subsection": "security",
        },
    }

    missing_required_config_vars = []
    for key, value in required_config_dict.items():
        try:
            config_value = getenv(value["env_var"]) or get_config_from_file(
                "",
                value["config_subsection"],
                key,
            )
        except FileNotFoundError:
            config_value = None

        if not config_value:
            missing_required_config_vars.append(key)

    if missing_required_config_vars:
        echo_red(
            "\nThere are missing required configuration variables. Please add the following config variables to either the "
            "`fides.toml` file or your environment variables to start Fides: \n"
        )
        for missing_value in missing_required_config_vars:
            print(f"- {missing_value}")
        print(
            "\nVisit the Fides deployment documentation for more information: "
            "https://ethyca.github.io/fides/deployment/"
        )

        raise SystemExit(1)


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
