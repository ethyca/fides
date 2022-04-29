"""Contains the scan group of the commands for Fidesctl."""

import click

from fidesctl.cli.options import coverage_threshold_option, manifests_dir_argument
from fidesctl.cli.utils import with_analytics
from fidesctl.core import dataset as _dataset
from fidesctl.core import system as _system


@click.group(name="scan")
@click.pass_context
def scan(ctx: click.Context) -> None:
    """
    Scan external resource coverage against fidesctl resources
    """


@scan.group(name="dataset")
@click.pass_context
def scan_dataset(ctx: click.Context) -> None:
    """
    Scan fidesctl Dataset resources
    """


@scan_dataset.command(name="db")
@click.pass_context
@click.argument("connection_string", type=str)
@manifests_dir_argument
@coverage_threshold_option
@with_analytics
def scan_dataset_db(
    ctx: click.Context,
    connection_string: str,
    manifests_dir: str,
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
    _dataset.scan_dataset_db(
        connection_string=connection_string,
        manifest_dir=manifests_dir,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )


@scan_dataset.command(name="okta")
@click.pass_context
@click.argument("org_url", type=str)
@manifests_dir_argument
@coverage_threshold_option
@with_analytics
def scan_dataset_okta(
    ctx: click.Context,
    org_url: str,
    manifests_dir: str,
    coverage_threshold: int,
) -> None:
    """
    Scans your existing datasets and compares them to found Okta applications.
    Connect to an Okta admin account by providing an organization url. Auth token
    can be supplied by setting the environment variable OKTA_CLIENT_TOKEN.

    Outputs missing resources and has a non-zero exit if coverage is
    under the stated threshold.
    """

    config = ctx.obj["CONFIG"]
    _dataset.scan_dataset_okta(
        org_url=org_url,
        coverage_threshold=coverage_threshold,
        manifest_dir=manifests_dir,
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
@manifests_dir_argument
@click.option("-o", "--organization", type=str, default="default_organization")
@coverage_threshold_option
@with_analytics
def scan_system_aws(
    ctx: click.Context,
    manifests_dir: str,
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
    _system.scan_system_aws(
        manifest_dir=manifests_dir,
        organization_key=organization,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )
