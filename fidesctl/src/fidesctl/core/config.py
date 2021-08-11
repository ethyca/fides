"""This module handles finding and parsing fides configuration files."""

## Add this as a pydantic model

import os
import configparser
from typing import Dict

from fidesctl.core.utils import echo_red, jwt_encode


def generate_request_headers(user_id: str, api_key: str) -> Dict[str, str]:
    """
    Generate the headers for a request.
    """
    return {
        "Content-Type": "application/json",
        "user-id": str(user_id),
        "Authorization": "Bearer {}".format(jwt_encode(1, api_key)),
    }


def read_config(config_path: str = "") -> Dict[str, str]:
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
        os.path.join(os.curdir, ".fides.conf"),
        os.path.join(os.path.expanduser("~"), ".fides.conf"),
    ]

    for file_location in possible_config_locations:
        if file_location != "" and os.path.isfile(file_location):
            try:
                parser = configparser.ConfigParser()
                parser.read(file_location)
                user_id = parser["User"]["id"]
                api_key = parser["User"]["api-key"]
                user_dict = {"user_id": user_id, "api_key": api_key}
                return user_dict
            except IOError:
                echo_red(f"Error reading config file from {file_location}")
            break
    return {"user_id": "1", "api_key": "test_api_key"}
