"""Contains the export group of CLI commands for Fides."""
import click

from fidesctl.cli.options import (
    dry_flag,
    manifests_dir_argument,
)
from fidesctl.core import (
    export as _export,
    parse as _parse,
)


@click.group(name="export")
@click.pass_context
def export(ctx: click.Context) -> None:
    """
    Export fidesctl resource types
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
