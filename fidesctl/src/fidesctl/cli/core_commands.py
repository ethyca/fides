"""Contains all of the core CLI commands for Fidesctl."""
import click

from fidesctl.cli.options import (
    dry_flag,
    fides_key_option,
    manifests_dir_argument,
    verbose_flag,
)
from fidesctl.cli.utils import pretty_echo
from fidesctl.core import (
    apply as _apply,
    evaluate as _evaluate,
    export as _export,
    generate_dataset as _generate_dataset,
    annotate_dataset as _annotate_dataset,
    parse as _parse,
)


@click.command()
@click.pass_context
@dry_flag
@click.option(
    "--diff",
    is_flag=True,
    help="Print the diff between the server's old and new states in Python DeepDiff format",
)
@manifests_dir_argument
def apply(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Validates local manifest files and then sends them to the server to be persisted.
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


@click.group(name="export")
@click.pass_context
def export(ctx: click.Context) -> None:
    """
    Parent export command.
    """


@export.command(name="systems")
@click.pass_context
@manifests_dir_argument
@dry_flag
def export_system(
    ctx: click.Context,
    manifests_dir: str,
    dry: bool,
) -> None:
    """
    Export a system in a data map format.
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _export.export_system(
        url=config.cli.server_url,
        system_list=taxonomy.system,
        headers=config.user.request_headers,
        manifests_dir=manifests_dir,
        dry=dry,
    )


@export.command(name="datasets")
@click.pass_context
@manifests_dir_argument
@dry_flag
def export_dataset(
    ctx: click.Context,
    manifests_dir: str,
    dry: bool,
) -> None:
    """
    Export a dataset in a data map format.
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _export.export_dataset(
        url=config.cli.server_url,
        dataset_list=taxonomy.dataset,
        headers=config.user.request_headers,
        manifests_dir=manifests_dir,
        dry=dry,
    )


@click.command()
@click.pass_context
@click.argument("connection_string", type=str)
@click.argument("output_filename", type=click.Path())
def generate_dataset(
    ctx: click.Context, connection_string: str, output_filename: str
) -> None:
    """
    Connect to a database directly via a SQLAlchemy-stlye connection string and
    generate a dataset manifest file that consists of every schema/table/field.

    This is a one-time operation that does not track the state of the database.
    It will need to be run again if the database schema changes.
    """

    _generate_dataset.generate_dataset(connection_string, output_filename)


@click.command()
@click.pass_context
@click.argument("source_type", type=click.Choice(["database"]))
@click.argument("connection_string", type=str)
@click.option("-m", "--manifest-dir", type=str, default="")
@click.option("-c", "--coverage-threshold", type=click.IntRange(0, 100), default=100)
def scan(
    ctx: click.Context,
    source_type: str,
    connection_string: str,
    manifest_dir: str,
    coverage_threshold: int,
) -> None:
    """
    Connect to a database directly via a SQLAlchemy-stlye connection string and
    compare the database objects to existing datasets.

    If there are fields within the database that aren't listed and categorized
    within one of the datasets, this counts as lacking coverage.

    Outputs missing fields and has a non-zero exit if coverage is
    under the stated threshold.
    """
    config = ctx.obj["CONFIG"]
    _generate_dataset.database_coverage(
        connection_string=connection_string,
        manifest_dir=manifest_dir,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )


@click.command()
@click.pass_context
@click.argument("input_filename", type=str)
@click.option(
    "-a",
    "--all-members",
    is_flag=True,
    help="Annotate all dataset members, not just fields",
)
@click.option(
    "-v",
    "--validate",
    is_flag=True,
    default=False,
    help="Strictly validate annotation inputs.",
)
def annotate_dataset(
    ctx: click.Context, input_filename: str, all_members: bool, validate: bool
) -> None:
    """
    Guided flow for annotating datasets. The dataset file will be edited in-place.
    """
    config = ctx.obj["CONFIG"]
    _annotate_dataset.annotate_dataset(
        config=config,
        dataset_file=input_filename,
        annotate_all=all_members,
        validate=validate,
    )


@click.command()
@click.pass_context
@manifests_dir_argument
@verbose_flag
def parse(ctx: click.Context, manifests_dir: str, verbose: bool = False) -> None:
    """
    Reads the resource files that are stored in MANIFESTS_DIR and its subdirectories to verify
    the validity of all manifest files.

    If the taxonomy is invalid, this command prints the error messages and triggers a non-zero exit code.
    """
    taxonomy = _parse.parse(manifests_dir)
    if verbose:
        pretty_echo(taxonomy.dict(), color="green")
