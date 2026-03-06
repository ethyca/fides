"""
CLI helpers for initializing the fides config directory and file.
"""

import os
from typing import Tuple

from click import echo

from fides.cli.utils import request_analytics_consent
from fides.config import FidesConfig
from fides.config.utils import generate_config_docs, replace_config_value


def create_config_file(config: FidesConfig, fides_directory_location: str = ".") -> str:
    """
    Initializes the .fides/fides.toml file if it doesn't exist.

    Returns the config_path if successful.
    """
    fides_dir_name = ".fides"
    fides_dir_path = f"{fides_directory_location}/{fides_dir_name}"
    config_file_name = "fides.toml"
    config_path = f"{fides_dir_path}/{config_file_name}"

    # create the .fides dir if it doesn't exist
    if not os.path.exists(fides_dir_path):
        os.mkdir(fides_dir_path)
        echo(f"Created a '{fides_dir_path}' directory.")
    else:
        echo(f"Directory '{fides_dir_path}' already exists.")

    # create a fides.toml config file if it doesn't exist
    if not os.path.isfile(config_path):
        generate_config_docs(config, config_path)
    else:
        echo(f"Configuration file already exists: {config_path}")

    echo("To learn more about configuring fides, see:")
    echo("\thttps://ethyca.github.io/fides/config/")

    return config_path


def create_and_update_config_file(
    config: FidesConfig,
    fides_directory_location: str = ".",
    opt_in: bool = False,
) -> Tuple[FidesConfig, str]:
    config = request_analytics_consent(config=config, opt_in=opt_in)

    config_path = create_config_file(
        config=config, fides_directory_location=fides_directory_location
    )

    if not config.user.analytics_opt_out:
        replace_config_value(
            fides_directory_location=fides_directory_location,
            key="analytics_opt_out",
            old_value="true",
            new_value="false",
        )
    return (config, config_path)
