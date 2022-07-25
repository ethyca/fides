"""Contains all of the Utility-type CLI commands for Fidesctl."""
import os
from datetime import datetime, timezone

import click
import toml
from fideslog.sdk.python.utils import OPT_OUT_COPY, OPT_OUT_PROMPT

import fidesctl
from fidesctl.cli.utils import (
    FIDESCTL_ASCII_ART,
    check_server,
    send_init_analytics,
    with_analytics,
)
from fidesctl.ctl.core.utils import echo_green


@click.command()
@click.pass_context
@click.argument("fides_directory_location", default=".", type=click.Path(exists=True))
def init(ctx: click.Context, fides_directory_location: str) -> None:
    """
    Initializes a Fidesctl instance, creating the default directory (`.fides/`) and
    the configuration file (`fidesctl.toml`) if necessary.

    Additionally, requests the ability to respectfully collect anonymous usage data.
    """

    executed_at = datetime.now(timezone.utc)
    separate = lambda: print("-" * 10, end=None)
    fides_dir_name = ".fides"
    fides_dir_path = f"{fides_directory_location}/{fides_dir_name}"
    config_file_name = "fidesctl.toml"
    config_path = f"{fides_dir_path}/{config_file_name}"
    config = ctx.obj["CONFIG"]

    included_values = {
        "database": {
            "server",
            "user",
            "password",
            "port",
            "db",
            "test_db",
        },
        "logging": {
            "level",
            "destination",
            "serialization",
        },
        "cli": {"server_protocol", "server_host", "server_port", "analytics_id"},
        "user": {"analytics_opt_out"},
    }
    click.echo(FIDESCTL_ASCII_ART)
    click.echo("Initializing Fidesctl...")
    separate()

    # create the .fides dir if it doesn't exist
    if not os.path.exists(fides_dir_path):
        os.mkdir(fides_dir_path)
        echo_green(f"Created a '{fides_dir_path}' directory.")
    else:
        click.echo(f"Directory '{fides_dir_path}' already exists.")

    separate()

    # create a fidesctl.toml config file if it doesn't exist
    if not os.path.isfile(config_path):
        # request explicit consent for analytics collection
        click.echo(OPT_OUT_COPY, nl=False)
        config.user.analytics_opt_out = bool(input(OPT_OUT_PROMPT).lower() == "n")

        separate()

        with open(config_path, "w") as config_file:
            config_dict = config.dict(include=included_values)
            toml.dump(config_dict, config_file)

        echo_green(f"Created a fidesctl config file: {config_path}")
        click.echo("To learn more about configuring fidesctl, see:")
        click.echo("\thttps://ethyca.github.io/fides/installation/configuration/")

    else:
        click.echo(f"Configuration file already exists: {config_path}")

    separate()
    click.echo("For example policies and help getting started, see:")
    click.echo("\thttps://ethyca.github.io/fides/guides/policies/")
    separate()

    send_init_analytics(config.user.analytics_opt_out, config_path, executed_at)

    echo_green("Fidesctl initialization complete.")


@click.command()
@click.pass_context
@with_analytics
def status(ctx: click.Context) -> None:
    """
    Sends a request to the Fidesctl API healthcheck endpoint and prints the response.
    """
    config = ctx.obj["CONFIG"]
    cli_version = fidesctl.__version__
    server_url = config.cli.server_url
    click.echo("Getting server status...")
    check_server(
        cli_version=cli_version,
        server_url=server_url,
    )


@click.command()
@click.pass_context
@with_analytics
def webserver(ctx: click.Context) -> None:
    """
    Starts the fidesctl API server using Uvicorn on port 8080.
    """
    # This has to be here to avoid a circular dependency
    from fidesctl.api.main import start_webserver

    start_webserver()
