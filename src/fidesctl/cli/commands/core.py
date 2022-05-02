"""Contains all of the core CLI commands for Fidesctl."""
import click

from fidesctl.cli.options import (
    dry_flag,
    fides_key_option,
    manifests_dir_argument,
    verbose_flag,
)
from fidesctl.cli.utils import pretty_echo, with_analytics
from fidesctl.core import apply as _apply
from fidesctl.core import evaluate as _evaluate
from fidesctl.core import parse as _parse


@click.command()
@click.pass_context
@dry_flag
@click.option(
    "--diff",
    is_flag=True,
    help="Include any changes between server and local resources in the command output",
)
@manifests_dir_argument
@with_analytics
def apply(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Validate local manifest files and persist any changes via the API server.
    """

    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _apply.apply(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.request_headers,
        dry=dry,
        diff=diff,
    )


@click.command()
@click.pass_context
@manifests_dir_argument
@fides_key_option
@click.option(
    "-m",
    "--message",
    help="A message that you can supply to describe the context of this evaluation.",
)
@dry_flag
@with_analytics
def evaluate(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
    message: str,
    dry: bool,
) -> None:
    """
    Compare your System's Privacy Declarations with your Organization's Policy Rules.

    All local resources are applied to the server before evaluation.

    If your policy evaluation fails, it is expected that you will need to
    either adjust your Privacy Declarations, Datasets, or Policies before trying again.
    """

    config = ctx.obj["CONFIG"]

    if config.cli.local_mode:
        dry = True
    else:
        taxonomy = _parse.parse(manifests_dir)
        _apply.apply(
            url=config.cli.server_url,
            taxonomy=taxonomy,
            headers=config.user.request_headers,
            dry=dry,
        )

    _evaluate.evaluate(
        url=config.cli.server_url,
        headers=config.user.request_headers,
        manifests_dir=manifests_dir,
        policy_fides_key=fides_key,
        message=message,
        local=config.cli.local_mode,
        dry=dry,
    )


@click.command()
@click.pass_context
@manifests_dir_argument
@verbose_flag
@with_analytics
def parse(ctx: click.Context, manifests_dir: str, verbose: bool = False) -> None:
    """
    Reads the resource files that are stored in MANIFESTS_DIR and its subdirectories to verify
    the validity of all manifest files.

    If the taxonomy is invalid, this command prints the error messages and triggers a non-zero exit code.
    """
    taxonomy = _parse.parse(manifests_dir=manifests_dir)
    if verbose:
        pretty_echo(taxonomy.dict(), color="green")
