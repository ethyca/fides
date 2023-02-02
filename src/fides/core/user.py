"""Module for interaction with User endpoints/commands."""
import json
from os import getenv
from os.path import isfile
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import toml
from pydantic import BaseModel

from fides.cli.utils import handle_cli_response
from fides.core.config import get_config
from fides.core.utils import echo_green, echo_red
from fides.lib.cryptography.cryptographic_util import str_to_b64_str
from fides.lib.oauth.scopes import SCOPES

config = get_config()
CREATE_USER_PATH = "/api/v1/user"
LOGIN_PATH = "/api/v1/login"
USER_PERMISSIONS_PATH = "/api/v1/user/{}/permission"


class Credentials(BaseModel):
    """
    User credentials for the CLI.
    """

    username: str
    password: str
    user_id: str
    access_token: str


def get_credentials_path() -> str:
    """
    Returns the default credentials path or the path set as an environment variable.
    """
    default_credentials_file_path = f"{str(Path.home())}/.fides_credentials"
    credentials_path = getenv("FIDES_CREDENTIALS_PATH", default_credentials_file_path)
    return credentials_path


def get_access_token(username: str, password: str, server_url: str) -> Tuple[str, str]:
    """
    Get a user access token from the webserver.
    """
    payload = {
        "username": username,
        "password": str_to_b64_str(password),
    }

    response = requests.post(server_url + LOGIN_PATH, json=payload)
    handle_cli_response(response, verbose=False)
    user_id: str = response.json()["user_data"]["id"]
    access_token: str = response.json()["token_data"]["access_token"]
    return (user_id, access_token)


def write_credentials_file(credentials: Credentials, credentials_path: str) -> str:
    """Write the user credentials file."""
    with open(credentials_path, "w", encoding="utf-8") as credentials_file:
        credentials_file.write(toml.dumps(credentials.dict()))
    return credentials_path


def read_credentials_file(
    credentials_path: str,
) -> Credentials:
    """Read and return the credentials file."""
    if not isfile(credentials_path):
        raise FileNotFoundError
    with open(credentials_path, "r", encoding="utf-8") as credentials_file:
        credentials = Credentials.parse_obj(toml.load(credentials_file))
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


def create_user(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    auth_header: Dict[str, str],
    server_url: str,
) -> requests.Response:
    """Create a user."""
    request_data = {
        "username": username,
        "password": str_to_b64_str(password),
        "first_name": first_name,
        "last_name": last_name,
    }
    response = requests.post(
        server_url + CREATE_USER_PATH,
        headers=auth_header,
        data=json.dumps(request_data),
    )
    handle_cli_response(response, verbose=False)
    return response


def get_user_permissions(
    user_id: str, auth_header: Dict[str, str], server_url: str
) -> List[str]:
    """
    List all of the user permissions for the provided user.
    """
    get_permissions_path = USER_PERMISSIONS_PATH.format(user_id)
    response = requests.get(
        server_url + get_permissions_path,
        headers=auth_header,
    )

    handle_cli_response(response, verbose=False)
    return response.json()["scopes"]


def update_user_permissions(
    user_id: str, scopes: List[str], auth_header: Dict[str, str], server_url: str
) -> requests.Response:
    """
    Update user permissions for a given user.
    """
    request_data = {"scopes": scopes, "id": user_id}
    set_permissions_path = USER_PERMISSIONS_PATH.format(user_id)
    response = requests.put(
        server_url + set_permissions_path,
        headers=auth_header,
        json=request_data,
    )
    handle_cli_response(response=response, verbose=False)
    return response


def create_command(
    username: str, password: str, first_name: str, last_name: str, server_url: str
) -> None:
    """
    Given new user information, create a new user via the API using
    the local credentials file.
    """

    auth_header = get_auth_header()
    user_response = create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        auth_header=auth_header,
        server_url=server_url,
    )
    user_id = user_response.json()["id"]
    update_user_permissions(
        user_id=user_id, scopes=SCOPES, auth_header=auth_header, server_url=server_url
    )
    echo_green(f"User: '{username}' created and assigned permissions.")


def login_command(username: str, password: str, server_url: str) -> None:
    """
    Given a username and password, request an access_token from the API and
    store all user information in a local credentials file.
    """
    user_id, access_token = get_access_token(
        username=username, password=password, server_url=server_url
    )
    echo_green(f"Logged in as user: {username}")
    credentials = Credentials(
        username=username, password=password, user_id=user_id, access_token=access_token
    )
    credentials_path = get_credentials_path()
    write_credentials_file(credentials, credentials_path)
    echo_green(f"Credentials file written to: {credentials_path}")


def get_permissions_command(server_url: str) -> None:
    """
    Get user permissions from the API.
    """
    credentials_path = get_credentials_path()
    credentials = read_credentials_file(credentials_path)
    user_id = credentials.user_id
    auth_header = get_auth_header()
    permissions: List[str] = get_user_permissions(user_id, auth_header, server_url)

    print("Permissions:")
    for permission in permissions:
        print(f"\t{permission}")
