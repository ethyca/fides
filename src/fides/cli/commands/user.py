"""Contains the user group of commands for fides."""

import click
from typing import Dict, List

from fides.core.user import (
    create_user,
    get_access_token,
    write_credentials_file,
    CREDENTIALS_PATH,
    get_user_scopes,
    create_auth_header,
    read_credentials_file,
)
from fides.core.utils import echo_green, echo_red


@click.group(name="user")
@click.pass_context
def user(ctx: click.Context) -> None:
    """
    Click command group for interacting with user-related functionality.
    """


@user.command()
@click.pass_context
@click.argument("username", type=str)
@click.argument("password", type=str)
@click.option(
    "-f",
    "--first-name",
    default="",
    help="First name of the user.",
)
@click.option(
    "-l",
    "--last-name",
    default="",
    help="Last name of the user.",
)
def create(
    ctx: click.Context, username: str, password: str, first_name: str, last_name: str
) -> None:
    """
    Use credentials from the credentials file to create a new user.
    """

    config = ctx.obj["CONFIG"]
    client_id = config.security.oauth_root_client_id
    client_secret = config.security.oauth_root_client_secret
    access_token = get_access_token(client_id, client_secret)
    auth_header = create_auth_header(access_token)

    create_user(username, password, first_name, last_name, auth_header)


@user.command()
@click.option(
    "-u",
    "--username",
    default="",
    help="Username to authenticate with.",
)
@click.option(
    "-p",
    "--password",
    default="",
    help="Password to authenticate with.",
)
def login(username: str, password: str) -> None:
    """
    Use credentials to get a user access token and write a credentials file.

    If no username/password is provided, attempt to load an existing credentials file
    and use that username/password.
    """

    if not (username and password):
        try:
            credentials: Dict[str, str] = read_credentials_file()
        except FileNotFoundError:
            echo_red("No username/password provided and no credentials file found.")
            raise SystemExit(1)
        username = credentials["username"]
        password = credentials["password"]

    access_token = get_access_token(username, password)
    write_credentials_file(username, password, access_token)
    echo_green(f"Credentials file written to: {CREDENTIALS_PATH}")


@user.command()
@click.option(
    "-u",
    "--username",
    default="",
    help="Username to get scopes for.",
)
def scopes(username: str) -> None:
    """List the scopes avaible to the current user."""

    credentials: Dict[str, str] = read_credentials_file()
    username = credentials["username"]
    access_token = credentials["access_token"]

    auth_header = create_auth_header(access_token)
    scopes: List[str] = get_user_scopes(username, auth_header)
    for scope in scopes:
        print(scope)
