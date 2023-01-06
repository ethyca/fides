"""Module for interaction with User endpoints/commands."""
from pathlib import Path
from typing import Dict

import requests
import toml

from fides.core.utils import echo_red

OAUTH_TOKEN_URL = "http://localhost:8080/api/v1/oauth/token"
CREDENTIALS_PATH = f"{str(Path.home())}/.fides_credentials"


def get_access_token(username: str, password: str) -> str:
    """
    Get a user access token from the webserver.
    """
    payload = {
        "client_id": username,
        "client_secret": password,
        "grant_type": "client_credentials",
    }

    response = requests.post(OAUTH_TOKEN_URL, data=payload)
    if response.status_code != 200:
        echo_red(
            "Authentication failed! Please check your username/password and try again."
        )
        raise SystemExit(1)
    access_token = response.json()["access_token"]
    return access_token


def write_credentials_file(username: str, access_token: str) -> str:
    """
    Write the user credentials file.
    """
    credentials_data = {"username": username, "access_token": access_token}
    with open(CREDENTIALS_PATH, "w", encoding="utf-8") as credentials_file:
        credentials_file.write(toml.dumps(credentials_data))
    return CREDENTIALS_PATH


def read_credentials_file() -> Dict[str, str]:
    """Read and return the credentials file."""
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as credentials_file:
        credentials_data = toml.load(credentials_file)
    return credentials_data


def create_auth_header(access_token: str) -> str:
    """Given an access token, create an auth header."""
    auth_header = f"Authorization: Bearer {access_token}"
    return auth_header


def get_user_scopes(username: str, auth_header: str) -> str:
    """
    Get a user access token from the webserver.
    """
    response = requests.post(
        f"http://localhost:8080/api/v1/oauth/{username}/scope", headers=auth_header
    )
    if response.status_code != 200:
        echo_red(
            "Authentication failed! Please check your username/password and try again."
        )
        raise SystemExit(1)
    print(response.json())
