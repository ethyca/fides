"""Contains the user group of commands for fides."""

import click

import requests
import toml


@click.group(name="user")
@click.pass_context
def user(ctx: click.Context) -> None:
    """
    Click command group for interacting with user-related functionality.
    """


@user.command()
@click.pass_context
def login(ctx: click.Context) -> None:
    """Use credentials to verify a user."""

    # If no username/password was provided, attempt to use the root
    config = ctx.obj["CONFIG"]
    username = config.security.oauth_root_client_id
    password = config.security.oauth_root_client_secret
    payload = {
        "client_id": username,
        "client_secret": password,
        "grant_type": "client_credentials",
    }

    # Hit the auth endpoint
    response = requests.post("http://localhost:8080/api/v1/oauth/token", data=payload)
    access_token = response.json()["access_token"]

    # Store the token in a .credentials file
    credentials_data = {"access_token": access_token}
    with open(".credentials", "w", encoding="utf-8") as credentials_file:
        credentials_file.write(toml.dumps(credentials_data))
