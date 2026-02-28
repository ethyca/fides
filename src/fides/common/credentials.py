"""Credential management utilities shared between CLI and config."""

from os import getenv
from os.path import isfile
from pathlib import Path
from typing import Dict

import toml
from pydantic import BaseModel

from fides.common.utils import echo_red


class Credentials(BaseModel):
    """
    User credentials for the CLI.
    """

    username: str
    user_id: str
    access_token: str


def write_credentials_file(credentials: Credentials, credentials_path: str) -> str:
    """Write the user credentials file."""
    with open(credentials_path, "w", encoding="utf-8") as credentials_file:
        credentials_file.write(toml.dumps(credentials.model_dump(mode="json")))
    return credentials_path


def get_credentials_path() -> str:
    """
    Returns the default credentials path or the path set as an environment variable.
    """
    default_credentials_file_path = f"{str(Path.home())}/.fides_credentials"
    credentials_path = getenv("FIDES_CREDENTIALS_PATH", default_credentials_file_path)
    return credentials_path


def read_credentials_file(
    credentials_path: str,
) -> Credentials:
    """Read and return the credentials file."""
    if not isfile(credentials_path):
        raise FileNotFoundError
    with open(credentials_path, "r", encoding="utf-8") as credentials_file:
        credentials = Credentials.model_validate(toml.load(credentials_file))
    return credentials


def create_auth_header(access_token: str) -> Dict[str, str]:
    """Given an access token, create an auth header."""
    auth_header = {
        "Authorization": f"Bearer {access_token}",
    }
    return auth_header


def get_auth_header(verbose: bool = True) -> Dict[str, str]:
    """
    Executes all of the logic required to form a valid auth header.
    """
    credentials_path = get_credentials_path()
    try:
        credentials = read_credentials_file(credentials_path=credentials_path)
    except FileNotFoundError:
        if verbose:
            echo_red("No credentials file found.")
        raise SystemExit(1)

    access_token = credentials.access_token
    auth_header = create_auth_header(access_token)
    return auth_header
