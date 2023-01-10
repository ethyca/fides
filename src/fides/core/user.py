"""Module for interaction with User endpoints/commands."""
import json
from pathlib import Path
from typing import Dict, List, Tuple
from fides.lib.cryptography.cryptographic_util import str_to_b64_str

import requests
import toml
from pydantic import BaseModel

from fides.cli.utils import handle_cli_response

CREATE_USER_URL = "http://localhost:8080/api/v1/user"
LOGIN_URL = "http://localhost:8080/api/v1/login"
USER_PERMISSIONS_URL = "http://localhost:8080/api/v1/user/{}/permission"

CREDENTIALS_PATH = f"{str(Path.home())}/.fides_credentials"


class Credentials(BaseModel):
    """
    User credentials for the CLI.
    """

    username: str
    password: str
    user_id: str
    access_token: str


def get_access_token(username: str, password: str) -> Tuple[str, str]:
    """
    Get a user access token from the webserver.
    """
    payload = {
        "username": username,
        "password": str_to_b64_str(password),
    }

    response = requests.post(LOGIN_URL, json=payload)
    handle_cli_response(response, verbose=False)
    user_id: str = response.json()["user_data"]["id"]
    access_token: str = response.json()["token_data"]["access_token"]
    return (user_id, access_token)


def write_credentials_file(
    username: str, password: str, user_id: str, access_token: str
) -> str:
    """
    Write the user credentials file.
    """
    credentials = Credentials(
        username=username,
        password=password,
        user_id=user_id,
        access_token=access_token,
    )
    with open(CREDENTIALS_PATH, "w", encoding="utf-8") as credentials_file:
        credentials_file.write(toml.dumps(credentials.dict()))
    return CREDENTIALS_PATH


def read_credentials_file() -> Credentials:
    """Read and return the credentials file."""
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as credentials_file:
        credentials = Credentials.parse_obj(toml.load(credentials_file))
    return credentials


def create_auth_header(access_token: str) -> Dict[str, str]:
    """Given an access token, create an auth header."""
    auth_header = {
        "Authorization": f"Bearer {access_token}",
    }
    return auth_header


def create_user(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    auth_header: Dict[str, str],
) -> requests.Response:
    """Create a user."""
    request_data = {
        "username": username,
        "password": str_to_b64_str(password),
        "first_name": first_name,
        "last_name": last_name,
    }
    response = requests.post(
        CREATE_USER_URL,
        headers=auth_header,
        data=json.dumps(request_data),
    )
    handle_cli_response(response, verbose=False)
    return response


def get_user_permissions(user_id: str, auth_header: Dict[str, str]) -> List[str]:
    """
    List all of the user permissions for the provided user.
    """
    scopes_url = USER_PERMISSIONS_URL.format(user_id)
    response = requests.get(
        scopes_url,
        headers=auth_header,
    )

    handle_cli_response(response, verbose=False)
    return response.json()["scopes"]


def update_user_permissions(
    user_id: str, scopes: List[str], auth_header: Dict[str, str]
) -> requests.Response:
    """
    Update user permissions for a given user.
    """
    request_data = {"scopes": scopes, "id": user_id}
    response = requests.put(
        USER_PERMISSIONS_URL.format(user_id),
        headers=auth_header,
        json=request_data,
    )
    handle_cli_response(response, verbose=False)
    return response
