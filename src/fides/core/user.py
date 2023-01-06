"""Module for interaction with User endpoints/commands."""
from pathlib import Path
from typing import Dict, List

import requests
import toml

from fides.core.utils import echo_red

OAUTH_TOKEN_URL = "http://localhost:8080/api/v1/oauth/token"
CLIENT_SCOPES_URL = "http://localhost:8080/api/v1/oauth/client/{}/scope"
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
    if response.status_code == 401:
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


def create_auth_header(access_token: str) -> Dict[str, str]:
    """Given an access token, create an auth header."""
    auth_header = {"Authorization": f"Bearer {access_token}"}
    return auth_header


def get_user_scopes(username: str, auth_header: Dict[str, str]) -> List[str]:
    """
    Get a user access token from the webserver.
    """
    scopes_url = CLIENT_SCOPES_URL.format(username)
    response = requests.get(
        scopes_url,
        headers=auth_header,
    )

    if response.status_code != 200:
        echo_red("Request failed! Please check your username/password and try again.")
        raise SystemExit(1)

    return response.json()


def create_user(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    auth_header: Dict[str, str],
) -> None:
    """Create a user."""
    user_data = {
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
    }
    print(user_data)
    response = requests.post(
        "http://localhost:8080/api/v1/user", headers=auth_header, data=user_data
    )
    print(response.text)
