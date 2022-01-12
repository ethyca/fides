"""Contains all of the Utility-type CLI commands for Fidesctl."""
import click
import requests

from fidesctl.cli.options import yes_flag
from fidesctl.cli.utils import (
    handle_cli_response,
    pretty_echo,
)
from fidesctl.core import api as _api
from fidesctl.core.utils import echo_green, echo_red


@click.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """
    Initialize a Fides instance.
    """
    config = ctx.obj["CONFIG"]

    echo_green("Initializing Fides...\n")

    # create the .fidesctl dir if it doesn't exist
    echo_green("Created a '.fides' directory at the repository root.\n")

    # create a config file if it doesn't exist
    config_url = "https://ethyca.github.io/fides/installation/configuration/"
    config_message = """Created a '.fides/config.toml' file. To learn more, see:
        {}\n""".format(
        config_url
    )
    echo_green(config_message)

    # Write out the default taxonomy

    # Leave a note about generating manifests
    echo_green(
        """To learn more about automated manifest file generation, run:
        fidesctl generate -h\n"""
    )


@click.command()
@click.pass_context
def init_db(ctx: click.Context) -> None:
    """
    Initialize the Fidesctl database.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(_api.db_action(config.cli.server_url, "init"))


@click.command()
@click.pass_context
def ping(ctx: click.Context, config_path: str = "") -> None:
    """
    Sends a request to the Fidesctl API healthcheck endpoint and prints the response.
    """
    config = ctx.obj["CONFIG"]
    healthcheck_url = config.cli.server_url + "/health"
    echo_green(f"Pinging {healthcheck_url}...")
    try:
        handle_cli_response(_api.ping(healthcheck_url))
    except requests.exceptions.ConnectionError:
        echo_red("Connection failed, webserver is unreachable.")


@click.command()
@click.pass_context
@yes_flag
def reset_db(ctx: click.Context, yes: bool) -> None:
    """
    Wipes all user-created data and resets the database back to its freshly initialized state.
    """
    config = ctx.obj["CONFIG"]
    if yes:
        are_you_sure = "y"
    else:
        echo_red(
            "This will drop all data from the Fides database and reload the default taxonomy!"
        )
        are_you_sure = input("Are you sure [y/n]? ")

    if are_you_sure.lower() == "y":
        handle_cli_response(_api.db_action(config.cli.server_url, "reset"))
    else:
        print("Aborting!")


@click.command()
@click.pass_context
def view_config(ctx: click.Context) -> None:
    """
    Prints the current fidesctl configuration values.
    """
    config = ctx.obj["CONFIG"]
    pretty_echo(config.dict(), color="green")


@click.command()
@click.pass_context
def webserver(ctx: click.Context) -> None:
    """
    Starts the fidesctl API server using Uvicorn on port 8080.
    """
    try:
        from fidesapi.main import start_webserver
    except ModuleNotFoundError:
        echo_red('Packages not found, try: pip install "fidesctl[webserver]"')
        raise SystemExit

    start_webserver()
