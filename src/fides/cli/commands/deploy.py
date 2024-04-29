"""Contains all of the deploy group of CLI commands for fides."""

from os import environ
from subprocess import CalledProcessError
from typing import Optional

import rich_click as click

from fides.common.utils import echo_green, print_divider
from fides.config.create import create_and_update_config_file
from fides.core.deploy import (
    check_docker_version,
    check_fides_uploads_dir,
    check_virtualenv,
    print_deploy_success,
    pull_specific_docker_image,
    start_application,
    teardown_application,
)


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


@deploy.command()  # type: ignore
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
    try:
        check_docker_version()
    except:  # pylint: disable=bare-except
        response = click.confirm(
            "WARNING: Encountered an error while checking Docker versions. Would you like to attempt a deploy anyway?"
        )
        if not response:
            raise SystemExit("Deploy aborted!")
    else:
        echo_green("Docker version is compatible, starting deploy...")

    config = ctx.obj["CONFIG"]

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
