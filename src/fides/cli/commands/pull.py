from typing import Optional

import rich_click as click
from click_default_group import DefaultGroup

from fides.cli.options import fides_key_argument, manifests_dir_argument
from fides.cli.utils import with_analytics, with_server_health_check
from fides.common.utils import echo_red
from fides.core import parse as _parse
from fides.core import pull as _pull
from fides.core.utils import git_is_dirty


@click.group(cls=DefaultGroup, default="all", default_if_no_args=True)  # type: ignore
@click.pass_context
def pull(ctx: click.Context) -> None:
    """
    Update local resource files based on the state of the objects on the server.
    """


@pull.command(name="all")  # type: ignore
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
@fides_key_argument
@manifests_dir_argument
def dataset(
    ctx: click.Context,
    fides_key: str,
    manifests_dir: str,
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


@pull.command(name="system")  # type: ignore
@click.pass_context
@fides_key_argument
@manifests_dir_argument
def system(
    ctx: click.Context,
    fides_key: str,
    manifests_dir: str,
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


@pull.command(name="data_category")  # type: ignore
@click.pass_context
@fides_key_argument
@manifests_dir_argument
def data_category(
    ctx: click.Context,
    fides_key: str,
    manifests_dir: str,
) -> None:
    """
    Retrieve a specific data_category from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="data_category",
        all_resources_file=None,
    )


@pull.command(name="data_use")  # type: ignore
@click.pass_context
@fides_key_argument
@manifests_dir_argument
def data_use(
    ctx: click.Context,
    fides_key: str,
    manifests_dir: str,
) -> None:
    """
    Retrieve a specific data_use from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="data_use",
        all_resources_file=None,
    )


@pull.command(name="data_subject")  # type: ignore
@click.pass_context
@fides_key_argument
@manifests_dir_argument
def data_subject(
    ctx: click.Context,
    fides_key: str,
    manifests_dir: str,
) -> None:
    """
    Retrieve a specific data_subject from the server and update the local manifest files.
    """

    config = ctx.obj["CONFIG"]
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        fides_key=fides_key,
        resource_type="data_subject",
        all_resources_file=None,
    )
