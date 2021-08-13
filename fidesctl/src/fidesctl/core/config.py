"""This module handles finding and parsing fides configuration files."""

import os
import configparser
from typing import Dict

from pydantic import BaseModel

from fidesctl.core.utils import echo_red, generate_request_headers


class MissingConfig(Exception):
    """Custom exception for when no valid configuration file is provided."""

    def __init__(self) -> None:
        message: str = "No configuration file provided!"
        super().__init__(message)


class UserConfig(BaseModel):
    """Class used to store values from the 'user' section of the config."""

    user_id: int
    api_key: str
    request_headers: Dict[str, str] = dict()


class CLIConfig(BaseModel):
    """Class used to store values from the 'cli' section of the config."""

    server_url: str


class Config(BaseModel):
    """Umbrella class that encapsulates all of the config subsections."""

    user: UserConfig
    cli: CLIConfig


def get_config(config_path: str = "") -> Config:
    """
    Attempt to read config file from:
    a) passed in configuration, if it exists
    b) env var FIDES_CONFIG_PATH
    b) local directory
    c) home directory

    This will fail on the first encountered bad conf file.
    """

    possible_config_locations = [
        config_path,
        os.getenv("FIDES_CONFIG_PATH", ""),
        os.path.join(os.curdir, "fides.ini"),
        os.path.join(os.path.expanduser("~"), "fides.ini"),
    ]

    for file_location in possible_config_locations:
        if file_location != "" and os.path.isfile(file_location):
            try:
                parser = configparser.ConfigParser()
                parser.read(file_location)
                user_config = UserConfig.parse_obj(parser["user"])
                cli_config = CLIConfig.parse_obj(parser["cli"])
                config = Config(
                    user=user_config,
                    cli=cli_config,
                )
                config.user.request_headers = generate_request_headers(
                    config.user.user_id, config.user.api_key
                )
            except IOError:
                echo_red(f"Error reading config file from {file_location}")
            break
    else:
        raise MissingConfig
    return config
