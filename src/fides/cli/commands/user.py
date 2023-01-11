"""Contains the user group of commands for fides."""

from typing import List

import click

from fides.core.user import (
    create_auth_header,
    create_user,
    get_access_token,
    get_user_permissions,
    read_credentials_file,
    update_user_permissions,
    write_credentials_file,
    Credentials,
)
from fides.core.utils import echo_green, echo_red
from fides.lib.oauth.scopes import SCOPES
from fides.cli.options import username, password, first_name, last_name


@click.group(name="user")
@click.pass_context
def user(ctx: click.Context) -> None:
    """
    Click command group for interacting with user-related functionality.
    """


@user.command()
@click.pass_context
@username
@password
@first_name
@last_name
def create(
    ctx: click.Context, username: str, password: str, first_name: str, last_name: str
) -> None:
    """
    Use credentials from the credentials file to create a new user.

    Gives full permissions to the new user.
    """
    config = ctx.obj["CONFIG"]
    server_url = config.cli.server_url

    try:
        credentials = read_credentials_file()
    except FileNotFoundError:
        echo_red("No credentials file found.")
        raise SystemExit(1)

    access_token = credentials.access_token
    auth_header = create_auth_header(access_token)
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


@user.command()
@click.pass_context
@username
@password
def login(ctx: click.Context, username: str, password: str) -> None:
    """
    Use credentials to get a user access token and write it to a credentials file.
    """
    config = ctx.obj["CONFIG"]
    server_url = config.cli.server_url

    user_id, access_token = get_access_token(
        username=username, password=password, server_url=server_url
    )
    echo_green(f"Logged in as user: {username}")
    credentials = Credentials(
        username=username, password=password, user_id=user_id, access_token=access_token
    )
    credentials_path = write_credentials_file(credentials)
    echo_green(f"Credentials file written to: {credentials_path}")


@user.command(name="permissions")
@click.pass_context
def get_permissions(ctx: click.Context) -> None:
    """List the scopes avaible to the current user."""
    config = ctx.obj["CONFIG"]
    server_url = config.cli.server_url

    credentials = read_credentials_file()
    user_id = credentials.user_id
    access_token = credentials.access_token

    auth_header = create_auth_header(access_token)
    permissions: List[str] = get_user_permissions(user_id, auth_header, server_url)

    print("Permissions:")
    for permission in permissions:
        print(f"\t{permission}")
