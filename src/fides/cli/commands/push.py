import rich_click as click
from click_default_group import DefaultGroup

from fides.cli.options import (
    diff_flag,
    dry_flag,
    fides_key_argument,
    manifests_dir_argument,
)
from fides.cli.utils import with_analytics, with_server_health_check
from fides.common.utils import echo_red
from fides.core import parse as _parse
from fides.core import push as _push


@click.group(cls=DefaultGroup, default="all", default_if_no_args=True)  # type: ignore
@click.pass_context
def push(ctx: click.Context) -> None:
    """
    Parse local manifest files and upload them to the server.
    """


@push.command(name="all")  # type: ignore
@click.pass_context
@dry_flag
@diff_flag
@manifests_dir_argument
@with_analytics
@with_server_health_check
def push_all(
    ctx: click.Context,
    dry: bool,
    diff: bool,
    manifests_dir: str,
) -> None:
    """
    Upload all local resources to server
    """

    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    # if the user has specified a specific fides_key, push only that dataset from taxonomy

    _push.push(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.auth_header,
        dry=dry,
        diff=diff,
    )


def push_by_key(
    ctx: click.Context,
    dry: bool,
    diff: bool,
    manifests_dir: str,
    fides_key: str,
    resource_type: str,
) -> None:
    """
    Parse local manifest files and upload the resource with matching `fides_key`
    """

    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)

    for resource in getattr(taxonomy, resource_type):
        if resource.fides_key == fides_key:
            setattr(taxonomy, resource_type, [resource])
            break
    else:
        echo_red(f"Dataset with fides_key '{fides_key}' not found.")
        return

    _push.push(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.auth_header,
        dry=dry,
        diff=diff,
    )


@push.command(name="dataset")
@click.pass_context
@dry_flag
@diff_flag
@fides_key_argument
@manifests_dir_argument
def dataset(
    ctx: click.Context,
    dry: bool,
    diff: bool,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Push a specific dataset identified by the `fides_key` argument to the server.
    """
    push_by_key(
        ctx=ctx,
        dry=dry,
        diff=diff,
        manifests_dir=manifests_dir,
        fides_key=fides_key,
        resource_type="dataset",
    )


@push.command(name="system")
@click.pass_context
@dry_flag
@diff_flag
@fides_key_argument
@manifests_dir_argument
def system(
    ctx: click.Context,
    dry: bool,
    diff: bool,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Push a specific system identified by the `fides_key` argument to the server.
    """
    push_by_key(
        ctx=ctx,
        dry=dry,
        diff=diff,
        manifests_dir=manifests_dir,
        fides_key=fides_key,
        resource_type="system",
    )


@push.command(name="category")
@click.pass_context
@dry_flag
@diff_flag
@fides_key_argument
@manifests_dir_argument
def category(
    ctx: click.Context,
    dry: bool,
    diff: bool,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Push a specific category identified by the `fides_key` argument to the server.
    """
    push_by_key(
        ctx=ctx,
        dry=dry,
        diff=diff,
        manifests_dir=manifests_dir,
        fides_key=fides_key,
        resource_type="category",
    )


@push.command(name="use")
@click.pass_context
@dry_flag
@diff_flag
@fides_key_argument
@manifests_dir_argument
def use(
    ctx: click.Context,
    dry: bool,
    diff: bool,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Push a specific use identified by the `fides_key` argument to the server.
    """
    push_by_key(
        ctx=ctx,
        dry=dry,
        diff=diff,
        manifests_dir=manifests_dir,
        fides_key=fides_key,
        resource_type="use",
    )


@push.command(name="subject")
@click.pass_context
@dry_flag
@diff_flag
@fides_key_argument
@manifests_dir_argument
def subject(
    ctx: click.Context,
    dry: bool,
    diff: bool,
    manifests_dir: str,
    fides_key: str,
) -> None:
    """
    Push a specific category identified by the `subject` argument to the server.
    """
    push_by_key(
        ctx=ctx,
        dry=dry,
        diff=diff,
        manifests_dir=manifests_dir,
        fides_key=fides_key,
        resource_type="category",
    )
