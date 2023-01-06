"""Contains the user group of commands for fides."""

import click

import requests
import toml

from fides.core.utils import echo_red


@click.group(name="user")
@click.pass_context
def user(ctx: click.Context) -> None:
    """
    Click command group for interacting with user-related functionality.
    """


@user.command()
@click.pass_context
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
def login(ctx: click.Context, username: str, password: str) -> None:
    """Use credentials to get a user access token."""

    # If no username/password was provided, attempt to use the root
    config = ctx.obj["CONFIG"]
    username = username or config.security.oauth_root_client_id
    password = password or config.security.oauth_root_client_secret
    payload = {
        "client_id": username,
        "client_secret": password,
        "grant_type": "client_credentials",
    }

    # Get the access token from the auth endpoint
    response = requests.post("http://localhost:8080/api/v1/oauth/token", data=payload)
    if response.status_code != 200:
        echo_red("Authentication failed!")
        raise SystemExit(1)
    access_token = response.json()["access_token"]

    # Store the token in a .credentials file
    credentials_data = {"access_token": access_token}
    credentials_path = ".credentials"
    print(f"Writing credentials to: '{credentials_path}'...")
    with open(credentials_path, "w", encoding="utf-8") as credentials_file:
        credentials_file.write(toml.dumps(credentials_data))
    print("Credentials successfully created.")
