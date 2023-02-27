"""Contains all of the Utility-type CLI commands for fides."""
from datetime import datetime, timezone
from subprocess import CalledProcessError
from typing import Tuple

import click

import fides
from fides.cli.utils import (
    FIDES_ASCII_ART,
    check_server,
    print_divider,
    request_analytics_consent,
    send_init_analytics,
    with_analytics,
)
from fides.core.config import FidesConfig
from fides.core.config.docs import create_config_file
from fides.core.config.utils import replace_config_value
from fides.core.deploy import (
    check_docker_version,
    check_fides_uploads_dir,
    check_virtualenv,
    print_deploy_success,
    pull_specific_docker_image,
    seed_example_data,
    start_application,
    teardown_application,
)
from fides.core.utils import echo_green


def create_and_update_config_file(
    config: FidesConfig, fides_directory_location: str = "."
) -> Tuple[FidesConfig, str]:
    # request explicit consent for analytics collection
    config = request_analytics_consent(config=config)

    # create the config file as needed
    config_path = create_config_file(
        config=config, fides_directory_location=fides_directory_location
    )

    # Update the value in the config file if it differs from the default
    if not config.user.analytics_opt_out:
        replace_config_value(
            fides_directory_location=fides_directory_location,
            key="analytics_opt_out",
            old_value="true",
            new_value="false",
        )
    return (config, config_path)


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
    config = ctx.obj["CONFIG"]

    click.echo(FIDES_ASCII_ART)
    click.echo("Initializing fides...")

    config, config_path = create_and_update_config_file(
        config, fides_directory_location
    )

    print_divider()

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
@click.option("--port", "-p", type=int, default=8080)
def webserver(ctx: click.Context, port: int = 8080) -> None:
    """
    Starts the fides API server using Uvicorn.
    """
    # This has to be here to avoid a circular dependency
    from fides.api.main import start_webserver

    start_webserver(port=port)


@click.command()
@click.pass_context
@with_analytics
def worker(ctx: click.Context) -> None:
    """
    Starts a celery worker.
    """
    # This has to be here to avoid a circular dependency
    from fides.api.ops.worker import start_worker

    start_worker()


# NOTE: This behaves similarly to 'init' in that it is excluded from analytics
# in the main CLI logic. This allows us to run `fides init` _during_ the deploy
# command, once the sample project server is accessible, to allow us to
# immediately register it
@click.group(name="deploy")
@click.pass_context
def deploy(ctx: click.Context) -> None:
    """
    Deploy a sample project locally to try out Fides.
    """


@deploy.command()
@click.pass_context
@click.option(
    "--no-pull",
    is_flag=True,
    help="Use a local image instead of trying to pull from DockerHub.",
)
@click.option(
    "--no-init",
    is_flag=True,
    help="Disable the initialization of the Fides CLI, to run in headless mode.",
)
def up(ctx: click.Context, no_pull: bool = False, no_init: bool = False) -> None:
    """
    Starts the sample project via docker compose.
    """

    check_virtualenv()
    check_docker_version()
    config = ctx.obj["CONFIG"]
    echo_green("Docker version is compatible, starting deploy...")

    if not no_pull:
        pull_specific_docker_image()

    try:
        check_fides_uploads_dir()
        start_application()
        seed_example_data()
        click.clear()

        # Deployment is ready! Perform the same steps as `fides init` to setup CLI
        if not no_init:
            echo_green("Deployment successful! Initializing fides...")
            create_and_update_config_file(config=config)
        else:
            echo_green(
                "Deployment successful! Skipping CLI initialization (run 'fides init' to initialize)"
            )
        print_divider()

        print_deploy_success()
    except CalledProcessError:
        teardown_application()
        raise SystemExit(1)


@deploy.command()
@click.pass_context
def down(ctx: click.Context) -> None:
    """
    Stops the sample project and removes all volumes.
    """

    check_docker_version()
    teardown_application()
