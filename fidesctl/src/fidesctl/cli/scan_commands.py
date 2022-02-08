"""Contains the scan group of the commands for Fides."""
import click

from fidesctl.core import (
    dataset as _dataset,
)


@click.group(name="scan")
@click.pass_context
def scan(ctx: click.Context) -> None:
    """
    Scan external resource coverage against fidesctl resources
    """


@scan.command(name="dataset")
@click.pass_context
@click.argument("connection_string", type=str)
@click.option("-m", "--manifest-dir", type=str, default="")
@click.option("-c", "--coverage-threshold", type=click.IntRange(0, 100), default=100)
def scan_dataset(
    ctx: click.Context,
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
    _dataset.scan_dataset(
        connection_string=connection_string,
        manifest_dir=manifest_dir,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )
