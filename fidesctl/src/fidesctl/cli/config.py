import os
import configparser
from typing import Optional, Dict

from fidesctl.core.utils import echo_red, jwt_encode


class FidesConfig:
    def __init__(self, id: int, api_key: str):
        self.id = id
        self.api_key = api_key

    def __repr__(self):
        return f"{self.id} -- {self.api_key}"

    def generate_request_headers(self) -> Dict[str, str]:
        """
        Generate the headers for a request.
        """
        return {
            "Content-Type": "application/json",
            "user-id": str(self.id),
            "Authorization": "Bearer {}".format(jwt_encode(1, self.api_key)),
        }


def read_conf(configuration: Optional[str] = None) -> Optional[FidesConfig]:
    """Attempt to read config file from
    a) passed in configuration, if it exists
    b) local directory
    c) home directory

    This will fail on the first encountered bad conf file.
    """

    def read_config_file(f: str) -> FidesConfig:
        parser = configparser.ConfigParser()
        parser.read_file(open(f))
        id = int(parser["User"]["id"])
        api_key = parser["User"]["api-key"]
        return FidesConfig(id, api_key)

    for loc in [
        configuration,
        os.path.join(os.curdir, ".fides.conf"),
        os.path.join(os.path.expanduser("~"), ".fides.conf"),
    ]:
        if loc is not None and os.path.isfile(loc):
            try:
                return read_config_file(loc)
            except:
                echo_red(f"error reading config file from {loc}")
