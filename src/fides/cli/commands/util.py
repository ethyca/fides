"""Contains all of the Utility-type CLI commands for fides."""
import os
from datetime import datetime, timezone

import click
import toml
from fideslog.sdk.python.utils import OPT_OUT_COPY, OPT_OUT_PROMPT

import fides
from fides.cli.utils import (
    FIDES_ASCII_ART,
    check_server,
    send_init_analytics,
    with_analytics,
)
from fides.ctl.core.demo import check_docker_version
from fides.ctl.core.utils import echo_green
from fides.ctl.core.demo import (
    start_application,
    teardown_application,
    seed_example_data,
)


@click.command()
@click.pass_context
@click.argument("fides_directory_location", default=".", type=click.Path(exists=True))
def init(ctx: click.Context, fides_directory_location: str) -> None:
    """
    Initializes a fides instance, creating the default directory (`.fides/`) and
    the configuration file (`fides.toml`) if necessary.

    Additionally, requests the ability to respectfully collect anonymous usage data.
    """

    executed_at = datetime.now(timezone.utc)
    separate = lambda: print("-" * 10, end=None)
    fides_dir_name = ".fides"
    fides_dir_path = f"{fides_directory_location}/{fides_dir_name}"
    config_file_name = "fides.toml"
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
    click.echo(FIDES_ASCII_ART)
    click.echo("Initializing fides...")
    separate()

    # create the .fides dir if it doesn't exist
    if not os.path.exists(fides_dir_path):
        os.mkdir(fides_dir_path)
        echo_green(f"Created a '{fides_dir_path}' directory.")
    else:
        click.echo(f"Directory '{fides_dir_path}' already exists.")

    separate()

    # create a fides.toml config file if it doesn't exist
    if not os.path.isfile(config_path):
        # request explicit consent for analytics collection
        click.echo(OPT_OUT_COPY, nl=False)
        config.user.analytics_opt_out = bool(input(OPT_OUT_PROMPT).lower() == "n")

        separate()

        with open(config_path, "w", encoding="utf-8") as config_file:
            config_dict = config.dict(include=included_values)
            toml.dump(config_dict, config_file)

        echo_green(f"Created a fides config file: {config_path}")
        click.echo("To learn more about configuring fides, see:")
        click.echo("\thttps://ethyca.github.io/fides/installation/configuration/")

    else:
        click.echo(f"Configuration file already exists: {config_path}")

    separate()
    click.echo("For example policies and help getting started, see:")
    click.echo("\thttps://ethyca.github.io/fides/guides/policies/")
    separate()

    send_init_analytics(config.user.analytics_opt_out, config_path, executed_at)

    echo_green("fides initialization complete.")


@click.command()
@click.pass_context
@with_analytics
def status(ctx: click.Context) -> None:
    """
    Sends a request to the fides API healthcheck endpoint and prints the response.
    """
    config = ctx.obj["CONFIG"]
    cli_version = fides.__version__
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
    Starts the fides API server using Uvicorn on port 8080.
    """
    # This has to be here to avoid a circular dependency
    from fides.api.main import start_webserver

    start_webserver()


@click.command()
@click.pass_context
@with_analytics
def worker(ctx: click.Context) -> None:
    """
    Starts a celery worker.
    """
    # This has to be here to avoid a circular dependency
    from fides.api.ops.tasks import start_worker

    start_worker()


@click.command()
@click.pass_context
@with_analytics
@click.option(
    "-d",
    "--detached",
    is_flag=True,
    help="Runs the application in the background after setup.",
)
def demo(ctx: click.Context, detached: bool = False) -> None:
    """
    Starts the application via docker compose.
    """
    # TODO: make sure that `init` gets run before the demo command spins up

    try:
        check_docker_version()
        start_application()
        seed_example_data()
    except:
        pass
    finally:
        teardown_application()
