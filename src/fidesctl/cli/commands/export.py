"""Contains the export group of CLI commands for Fidesctl."""
import click

from fidesctl.cli.options import dry_flag, manifests_dir_argument
from fidesctl.cli.utils import with_analytics
from fidesctl.core import export as _export
from fidesctl.core import parse as _parse


@click.group(name="export")
@click.pass_context
def export(ctx: click.Context) -> None:
    """
    Export fidesctl resource types
    """


@export.command(name="system")
@click.pass_context
@manifests_dir_argument
@dry_flag
@with_analytics
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


@export.command(name="dataset")
@click.pass_context
@manifests_dir_argument
@dry_flag
@with_analytics
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


@export.command(name="organization")
@click.pass_context
@manifests_dir_argument
@dry_flag
@with_analytics
def export_organization(
    ctx: click.Context,
    manifests_dir: str,
    dry: bool,
) -> None:
    """
    Export an organization in a data map format.
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _export.export_organization(
        url=config.cli.server_url,
        organization_list=taxonomy.organization,
        headers=config.user.request_headers,
        manifests_dir=manifests_dir,
        dry=dry,
    )


@export.command(name="datamap")
@click.pass_context
@manifests_dir_argument
@dry_flag
@click.option(
    "--csv",
    is_flag=True,
    help="Export using csv format",
)
@with_analytics
def export_datamap(
    ctx: click.Context,
    manifests_dir: str,
    dry: bool,
    csv: bool,
) -> None:
    """
    Export a formatted data map to excel using template

    The csv flag can be used to output data as csv instead
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _export.export_datamap(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.request_headers,
        manifests_dir=manifests_dir,
        dry=dry,
        to_csv=csv,
    )
