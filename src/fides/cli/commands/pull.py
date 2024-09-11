from typing import Optional

import rich_click as click

from fides.cli.options import fides_key_argument, manifests_dir_argument
from fides.cli.utils import with_analytics, with_server_health_check
from fides.common.utils import echo_green, echo_red
from fides.core import parse as _parse
from fides.core import pull as _pull
from fides.core.utils import git_is_dirty


@click.group(invoke_without_command=True)  # type: ignore
@click.pass_context
@manifests_dir_argument
@click.option(
    "--all-resources",
    "-a",
    default=None,
    help="Pulls all locally missing resources from the server into this file.",
)
def pull(ctx: click.Context, manifests_dir: str, all_resources: Optional[str]) -> None:
    """
    Update local resource files based on the state of the objects on the server.
    """
    if not ctx.invoked_subcommand:
        ctx.invoke(pull_all, manifests_dir=manifests_dir, all_resources=all_resources)


@pull.command(name="")  # type: ignore
@click.pass_context
@manifests_dir_argument
@click.option(
    "--all-resources",
    "-a",
    default=None,
    help="Pulls all locally missing resources from the server into this file.",
)
@with_analytics
@with_server_health_check
def pull_all(
    ctx: click.Context,
    manifests_dir: str,
    all_resources: Optional[str],
) -> None:
    """
    Retrieve all resources from the server and update the local manifest files.
    """

    # Make the resources that are pulled configurable
    config = ctx.obj["CONFIG"]
    # Do this to validate the manifests since they won't get parsed during the pull process
    _parse.parse(manifests_dir)
    if git_is_dirty(manifests_dir):
        echo_red(
            f"There are unstaged changes in your manifest directory: '{manifests_dir}' \nAborting pull!"
        )
        raise SystemExit(1)
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        all_resources_file=all_resources,
        fides_key=None,
        resource_type=None,
    )


@pull.command(name="dataset")  # type: ignore
@click.pass_context
@manifests_dir_argument
@fides_key_argument
def dataset(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Retrieve a specific dataset from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="dataset",
        all_resources_file=None,
    )
    echo_green(f"Successfully pulled {fides_key} resources from the server.")


@pull.command(name="system")  # type: ignore
@click.pass_context
@manifests_dir_argument
@fides_key_argument
def system(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Retrieve a specific system from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="system",
        all_resources_file=None,
    )
    echo_green(f"Successfully pulled {fides_key} resources from the server.")


@pull.command(name="category")  # type: ignore
@click.pass_context
@manifests_dir_argument
@fides_key_argument
def category(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Retrieve a specific category from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="category",
        all_resources_file=None,
    )
    echo_green(f"Successfully pulled {fides_key} resources from the server.")


@pull.command(name="use")  # type: ignore
@click.pass_context
@manifests_dir_argument
@fides_key_argument
def use(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Retrieve a specific use from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="use",
        all_resources_file=None,
    )
    echo_green(f"Successfully pulled {fides_key} resources from the server.")


@pull.command(name="subject")  # type: ignore
@click.pass_context
@manifests_dir_argument
@fides_key_argument
def subject(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Retrieve a specific subject from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="subject",
        all_resources_file=None,
    )
    echo_green(f"Successfully pulled {fides_key} resources from the server.")
