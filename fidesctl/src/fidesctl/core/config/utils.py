from errno import ENOENT
from os import strerror
from os.path import exists
from typing import Any, Dict

from click import echo
from toml import dump, load


def update_config_file(  # type: ignore
    updates: Dict[str, Dict[str, Any]],
    config_path: str = ".fides/fidesctl.toml",
) -> None:
    """
    Overwrite the existing config file with a new version that includes the desired `updates`.

    :param updates: A nested `dict`, where top-level keys correspond to configuration sections and top-level values contain `dict`s whose key/value pairs correspond to the desired option/value updates.
    :param config_path: The path to the current configuration file.
    """

    if not exists(config_path):
        raise FileNotFoundError(ENOENT, strerror(ENOENT), config_path)

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
