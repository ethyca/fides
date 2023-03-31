"""Contains all of the core CLI commands for fides."""
from typing import Optional

import rich_click as click

from fides.cli.options import dry_flag, manifests_dir_argument, verbose_flag
from fides.cli.utils import pretty_echo, print_divider, with_analytics
from fides.core import audit as _audit
from fides.core import evaluate as _evaluate
from fides.core import parse as _parse
from fides.core import pull as _pull
from fides.core import push as _push
from fides.core.utils import echo_red, git_is_dirty


@click.command()
@click.pass_context
@dry_flag
@click.option(
    "--diff",
    is_flag=True,
    help="Print any diffs between the local & server objects",
)
@manifests_dir_argument
@with_analytics
def push(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Parse local manifest files and upload them to the server.
    """

    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _push.push(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.auth_header,
        dry=dry,
        diff=diff,
    )


@click.command()
@click.pass_context
@manifests_dir_argument
@click.option(
    "--fides-key",
    "-k",
    help="The fides_key of a specific policy to evaluate.",
    default="",
)
@click.option(
    "-m",
    "--message",
    help="Describe the context of this evaluation.",
)
@click.option(
    "-a",
    "--audit",
    is_flag=True,
    help="Validate that the objects in this evaluation produce a valid data map.",
)
@click.option(
    "--dry",
    is_flag=True,
    help="Do not upload objects or results to the Fides webserver.",
)
@with_analytics
def evaluate(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
    message: str,
    audit: bool,
    dry: bool,
) -> None:
    """
    Evaluate System-level Privacy Declarations against Organization-level Policy Rules.
    """

    config = ctx.obj["CONFIG"]

    if config.cli.local_mode:
        dry = True
    else:
        taxonomy = _parse.parse(manifests_dir)
        _push.push(
            url=config.cli.server_url,
            taxonomy=taxonomy,
            headers=config.user.auth_header,
            dry=dry,
        )

    _evaluate.evaluate(
        url=config.cli.server_url,
        headers=config.user.auth_header,
        manifests_dir=manifests_dir,
        policy_fides_key=fides_key,
        message=message,
        local=config.cli.local_mode,
        dry=dry,
    )

    if audit:
        print_divider()
        pretty_echo("Auditing Organization Resource Compliance")
        _audit.audit_organizations(
            url=config.cli.server_url,
            headers=config.user.auth_header,
            include_keys=[
                organization.fides_key for organization in taxonomy.organization
            ],
        )
        print_divider()
        pretty_echo("Auditing System Resource Compliance")
        _audit.audit_systems(
            url=config.cli.server_url,
            headers=config.user.auth_header,
            include_keys=[system.fides_key for system in taxonomy.system],
        )


@click.command()
@click.pass_context
@manifests_dir_argument
@verbose_flag
@with_analytics
def parse(ctx: click.Context, manifests_dir: str, verbose: bool = False) -> None:
    """
    Parse all Fides objects located in the supplied directory.
    """
    taxonomy = _parse.parse(manifests_dir=manifests_dir)
    if verbose:
        pretty_echo(taxonomy.dict(), color="green")


@click.command()
@click.pass_context
@manifests_dir_argument
@click.option(
    "--all-resources",
    "-a",
    default=None,
    help="Pulls all locally missing resources from the server into this file.",
)
@with_analytics
def pull(ctx: click.Context, manifests_dir: str, all_resources: Optional[str]) -> None:
    """
    Update local resource files based on the state of the objects on the server.
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
    )
