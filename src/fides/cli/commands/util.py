"""Contains all of the Utility-type CLI commands for fides."""
from datetime import datetime, timezone
from os import environ
from subprocess import CalledProcessError
from typing import Optional

import rich_click as click

import fides
from fides.cli.utils import (
    FIDES_ASCII_ART,
    check_server,
    print_divider,
    send_init_analytics,
    with_analytics,
)
from fides.core.config.create import create_and_update_config_file
from fides.core.deploy import (
    check_docker_version,
    check_fides_uploads_dir,
    check_virtualenv,
    print_deploy_success,
    pull_specific_docker_image,
    start_application,
    teardown_application,
)
from fides.core.utils import echo_green


@click.command()
@click.pass_context
@click.argument("fides_dir", default=".", type=click.Path(exists=True))
@click.option(
    "--opt-in", is_flag=True, help="Automatically opt-in to anonymous usage analytics."
)
def init(ctx: click.Context, fides_dir: str, opt_in: bool) -> None:
    """
    Initializes a Fides instance by creating the default directory and
    configuration file if not present.
    """

    executed_at = datetime.now(timezone.utc)
    config = ctx.obj["CONFIG"]

    click.echo(FIDES_ASCII_ART)
    click.echo("Initializing fides...")

    config, config_path = create_and_update_config_file(
        config, fides_dir, opt_in=opt_in
    )

    print_divider()

    send_init_analytics(config.user.analytics_opt_out, config_path, executed_at)
    echo_green("fides initialization complete.")


@click.command()
@click.pass_context
@with_analytics
def status(ctx: click.Context) -> None:
    """
    Check Fides server availability.
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
    Start the Fides webserver.

    _Requires Redis and Postgres to be configured and running_
    """
    # This has to be here to avoid a circular dependency
    from fides.api.main import start_webserver

    start_webserver(port=port)


@click.command()
@click.pass_context
@with_analytics
def worker(ctx: click.Context) -> None:
    """
    Start a Celery worker for the Fides webserver.
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
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Use a custom ENV file for the Fides container to override settings.",
)
@click.option(
    "--image",
    type=str,
    help="Use a custom image for the Fides container instead of the default ('ethyca/fides').",
)
def up(
    ctx: click.Context,
    no_pull: bool = False,
    no_init: bool = False,
    env_file: Optional[click.Path] = None,
    image: Optional[str] = None,
) -> None:  # pragma: no cover
    """
    Starts a sample project via docker compose.
    """

    check_virtualenv()
    check_docker_version()
    config = ctx.obj["CONFIG"]
    echo_green("Docker version is compatible, starting deploy...")

    if not no_pull:
        pull_specific_docker_image()

    if env_file:
        print(f"> Using custom ENV file from: {env_file}")
        environ["FIDES_DEPLOY_ENV_FILE"] = str(env_file)

    if image:
        print(f"> Using custom image: {image}")
        environ["FIDES_DEPLOY_IMAGE"] = image

    try:
        check_fides_uploads_dir()
        print("> Starting application...")
        start_application()
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
