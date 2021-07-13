"""This module handles finding and parsing fides configuration files."""

import os
import configparser
from typing import Optional, Dict

from fidesctl.core.utils import echo_red, jwt_encode


class FidesConfig:
    """A parsed configuration. This configuration expects a file of the form:
    [User]
    id = 1
    api-key = test_api_key
    """

    def __init__(self, user_id: int, api_key: str):
        self.user_id = user_id
        self.api_key = api_key

    def __repr__(self):
        return f"{self.user_id} -- {self.api_key}"

    def generate_request_headers(self) -> Dict[str, str]:
        """
        Generate the headers for a request.
        """
        return {
            "Content-Type": "application/json",
            "user-id": str(self.user_id),
            "Authorization": "Bearer {}".format(jwt_encode(1, self.api_key)),
        }


def read_conf(configuration: Optional[str] = None) -> Optional[FidesConfig]:
    """Attempt to read config file from
    a) passed in configuration, if it exists
    b) local directory
    c) home directory

    This will fail on the first encountered bad conf file.
    """

    def read_config_file(file_name: str) -> FidesConfig:
        parser = configparser.ConfigParser()
        parser.read_file(open(file_name))
        user_id = int(parser["User"]["id"])
        api_key = parser["User"]["api-key"]
        return FidesConfig(user_id, api_key)

    for file_location in [
        configuration,
        os.path.join(os.curdir, ".fides.conf"),
        os.path.join(os.path.expanduser("~"), ".fides.conf"),
    ]:
        if file_location is not None and os.path.isfile(file_location):
            try:
                return read_config_file(file_location)
            except IOError:
                echo_red(f"error reading config file from {file_location}")
