"""Contains all of the Utility-type CLI commands for Fidesctl."""
import os

import click
from fideslog.sdk.python.utils import OPT_OUT_COPY
import requests
import toml

from fidesctl.cli.utils import handle_cli_response, with_analytics
from fidesctl.core import api as _api
from fidesctl.core.utils import echo_green, echo_red


@click.command()
@click.pass_context
@click.argument("fides_directory_location", default=".", type=click.Path(exists=True))
def init(ctx: click.Context, fides_directory_location: str) -> None:
    """
    Initializes a Fidesctl instance, creating the default directory (`.fides/`) and
    the configuration file (`fidesctl_config.toml`).

    Additionally, requests the ability to respectfully collect anonymous usage data.
    """

    # Constants
    separate = lambda: print("-" * 10)
    fides_dir_name = ".fides"
    fides_dir_path = f"{fides_directory_location}/{fides_dir_name}"
    config_file_name = "fidesctl.toml"
    config_path = f"{fides_dir_path}/{config_file_name}"
    config = ctx.obj["CONFIG"]

    # List the values we want to include in the user-facing config
    included_values = {
        "api": {
            "database_user",
            "database_password",
            "database_host",
            "database_port",
            "database_name",
            "test_database_name",
            "log_level",
            "log_destination",
            "log_serialization",
        },
        "cli": {"server_url", "analytics_id"},
        "user": {"analytics_opt_out"},
    }

    click.echo("Initializing Fidesctl...")
    separate()

    # create the dir if it doesn't exist
    if not os.path.exists(fides_dir_path):
        os.mkdir(fides_dir_path)
        echo_green(f"Created a '{fides_dir_path}' directory.")
    else:
        click.echo(f"Directory '{fides_dir_path}' already exists.")
    separate()

    # create a config file if it doesn't exist
    if not os.path.isfile(config_path):
        config_docs_url = "https://ethyca.github.io/fides/installation/configuration/"
        config_message = f"""Created a config file at '{config_path}'. To learn more, see:
            {config_docs_url}"""
        config.user.analytics_opt_out = bool(input(OPT_OUT_COPY).lower() == "n")
        with open(config_path, "w") as config_file:
            config_dict = config.dict(include=included_values)
            toml.dump(config_dict, config_file)
        echo_green(config_message)

    else:
        click.echo(f"Configuration file already exists at '{config_path}'.")
    separate()

    click.echo(
        "For example policies to help get started, see: ethyca.github.io/fides/guides/policies/"
    )
    separate()

    echo_green("Fidesctl initialization complete.")


@click.command()
@click.pass_context
def ping(ctx: click.Context) -> None:
    """
    Sends a request to the Fidesctl API healthcheck endpoint and prints the response.
    """
    config = ctx.obj["CONFIG"]
    healthcheck_url = config.cli.server_url + "/health"
    echo_green(f"Pinging {healthcheck_url}...")
    try:
        handle_cli_response(with_analytics(ctx, _api.ping, url=healthcheck_url))
    except requests.exceptions.ConnectionError:
        echo_red("Connection failed, webserver is unreachable.")


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

    with_analytics(ctx, start_webserver)
