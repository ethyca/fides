"""Contains the scan group of the commands for Fidesctl."""

import click

from fidesctl.cli.utils import with_analytics
from fidesctl.core import dataset as _dataset
from fidesctl.core import system as _system


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
    Connect to a database directly via a SQLAlchemy-style connection string and
    compare the database objects to existing datasets.

    If there are fields within the database that aren't listed and categorized
    within one of the datasets, this counts as lacking coverage.

    Outputs missing fields and has a non-zero exit if coverage is
    under the stated threshold.
    """
    config = ctx.obj["CONFIG"]
    with_analytics(
        ctx,
        _dataset.scan_dataset,
        connection_string=connection_string,
        manifest_dir=manifest_dir,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )


@scan.group(name="system")
@click.pass_context
def scan_system(ctx: click.Context) -> None:
    """
    Scan fidesctl System resources
    """


@scan_system.command(name="aws")
@click.pass_context
@click.option("-m", "--manifest-dir", type=str, default="")
@click.option("-o", "--organization", type=str, default="default_organization")
@click.option("-c", "--coverage-threshold", type=click.IntRange(0, 100), default=100)
def scan_system_aws(
    ctx: click.Context,
    manifest_dir: str,
    organization: str,
    coverage_threshold: int,
) -> None:
    """
    Connect to an aws account by leveraging a valid boto3 environment varible
    configuration and compares tracked resources to existing systems.
    Tracked resources: [Redshift, RDS]

    Outputs missing resources and has a non-zero exit if coverage is
    under the stated threshold.
    """
    config = ctx.obj["CONFIG"]
    with_analytics(
        ctx,
        _system.scan_system_aws,
        manifest_dir=manifest_dir,
        organization_key=organization,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )
