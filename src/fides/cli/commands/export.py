"""Contains the export group of CLI commands for fides."""
import rich_click as click

from fides.cli.options import (
    dry_flag,
    manifests_dir_argument,
    organization_fides_key_option,
    output_directory_option,
)
from fides.cli.utils import with_analytics
from fides.core import export as _export
from fides.core import parse as _parse


@click.group(name="export")
@click.pass_context
def export(ctx: click.Context) -> None:
    """
    Export Fides data maps.
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
    Export systems in a data map format.
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _export.export_system(
        url=config.cli.server_url,
        system_list=taxonomy.system,
        headers=config.user.auth_header,
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
    Export datasets in a data map format.
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _export.export_dataset(
        url=config.cli.server_url,
        dataset_list=taxonomy.dataset,
        headers=config.user.auth_header,
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
    Export organizations in a data map format.
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _export.export_organization(
        url=config.cli.server_url,
        organization_list=taxonomy.organization,
        headers=config.user.auth_header,
        manifests_dir=manifests_dir,
        dry=dry,
    )


@export.command(name="datamap")
@click.pass_context
@output_directory_option
@organization_fides_key_option
@dry_flag
@click.option(
    "--csv",
    is_flag=True,
    help="Export using csv format",
)
@with_analytics
def export_datamap(
    ctx: click.Context,
    output_dir: str,
    org_key: str,
    dry: bool,
    csv: bool,
) -> None:
    """
    Export a data map using the standard Fides template.

    The data map is comprised of an Organization, Systems, and Datasets.
    """
    config = ctx.obj["CONFIG"]
    _export.export_datamap(
        url=config.cli.server_url,
        headers=config.user.auth_header,
        organization_fides_key=org_key,
        output_directory=output_dir,
        dry=dry,
        to_csv=csv,
    )
