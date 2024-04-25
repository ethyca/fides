"""Contains the user command group for the fides CLI."""

import rich_click as click

from fides.cli.options import (
    first_name_option,
    last_name_option,
    password_argument,
    password_option,
    username_argument,
    username_option,
)
from fides.core.user import create_command, get_permissions_command, login_command


@click.group(name="user")
@click.pass_context
def user(ctx: click.Context) -> None:
    """
    Click command group for interacting with user-related functionality.
    """


@user.command()
@click.pass_context
@username_argument
@password_argument
@first_name_option
@last_name_option
def create(
    ctx: click.Context, username: str, password: str, first_name: str, last_name: str
) -> None:
    """
    Use the credentials file to create a new user. Gives full permissions to the new user.
    """
    config = ctx.obj["CONFIG"]
    server_url = config.cli.server_url
    create_command(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        server_url=server_url,
    )


@user.command()
@click.pass_context
@username_option
@password_option
def login(ctx: click.Context, username: str, password: str) -> None:
    """
    Authenticate with the webserver and generate a user access token.
    Then store those credentials in a credentials file.
    """
    config = ctx.obj["CONFIG"]
    server_url = config.cli.server_url
    login_command(username=username, password=password, server_url=server_url)


@user.command(name="permissions")
@click.pass_context
def get_permissions(ctx: click.Context) -> None:
    """
    List the directly-assigned scopes and roles available to the current user.
    """
    config = ctx.obj["CONFIG"]
    server_url = config.cli.server_url
    get_permissions_command(server_url=server_url)
