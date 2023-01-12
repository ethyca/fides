"""Contains the scan group of the commands for fides."""

import click

from fides.cli.options import (
    aws_access_key_id_option,
    aws_region_option,
    aws_secret_access_key_option,
    connection_string_option,
    coverage_threshold_option,
    credentials_id_option,
    manifests_dir_argument,
    okta_org_url_option,
    okta_token_option,
    organization_fides_key_option,
)
from fides.cli.utils import (
    handle_aws_credentials_options,
    handle_database_credentials_options,
    handle_okta_credentials_options,
    with_analytics,
)
from fides.core import dataset as _dataset
from fides.core import system as _system


@click.group(name="scan")
@click.pass_context
def scan(ctx: click.Context) -> None:
    """
    Scan external resource coverage against fides resources
    """


@scan.group(name="dataset")
@click.pass_context
def scan_dataset(ctx: click.Context) -> None:
    """
    Scan fides Dataset resources
    """


@scan_dataset.command(name="db")
@click.pass_context
@manifests_dir_argument
@credentials_id_option
@connection_string_option
@coverage_threshold_option
@with_analytics
def scan_dataset_db(
    ctx: click.Context,
    manifests_dir: str,
    connection_string: str,
    credentials_id: str,
    coverage_threshold: int,
) -> None:
    """
    Connect to a database directly via a SQLAlchemy-style connection string and
    compare the database objects to existing datasets. Connection string can be
    supplied as an option or a credentials reference to fides config.

    If there are fields within the database that aren't listed and categorized
    within one of the datasets, this counts as lacking coverage.

    Outputs missing fields and has a non-zero exit if coverage is
    under the stated threshold.
    """
    config = ctx.obj["CONFIG"]
    actual_connection_string = handle_database_credentials_options(
        fides_config=config,
        connection_string=connection_string,
        credentials_id=credentials_id,
    )

    _dataset.scan_dataset_db(
        connection_string=actual_connection_string,
        manifest_dir=manifests_dir,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )


@scan.group(name="system")
@click.pass_context
def scan_system(ctx: click.Context) -> None:
    """
    Scan fides System resources
    """


@scan_system.command(name="okta")
@click.pass_context
@manifests_dir_argument
@credentials_id_option
@okta_org_url_option
@okta_token_option
@organization_fides_key_option
@coverage_threshold_option
@with_analytics
def scan_system_okta(
    ctx: click.Context,
    manifests_dir: str,
    credentials_id: str,
    org_url: str,
    token: str,
    org_key: str,
    coverage_threshold: int,
) -> None:
    """
    Scans your existing systems and compares them to found Okta applications.
    Connect to an Okta admin account by providing an organization url and
    auth token or a credentials reference to fides config. Auth token and
    organization url can also be supplied by setting environment variables
    as defined by the okta python sdk.

    Outputs missing resources and has a non-zero exit if coverage is
    under the stated threshold.
    """

    config = ctx.obj["CONFIG"]
    okta_config = handle_okta_credentials_options(
        fides_config=config, token=token, org_url=org_url, credentials_id=credentials_id
    )

    _system.scan_system_okta(
        okta_config=okta_config,
        coverage_threshold=coverage_threshold,
        organization_key=org_key,
        manifest_dir=manifests_dir,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )


@scan_system.command(name="aws")
@click.pass_context
@manifests_dir_argument
@credentials_id_option
@aws_access_key_id_option
@aws_secret_access_key_option
@aws_region_option
@organization_fides_key_option
@coverage_threshold_option
@with_analytics
def scan_system_aws(
    ctx: click.Context,
    manifests_dir: str,
    credentials_id: str,
    access_key_id: str,
    secret_access_key: str,
    region: str,
    org_key: str,
    coverage_threshold: int,
) -> None:
    """
    Connect to an aws account and compares tracked resources to existing systems.
    Credentials can be supplied as options, a credentials reference to fides
    config, or boto3 environment configuration.
    Tracked resources: [Redshift, RDS, DynamoDb, S3]

    Outputs missing resources and has a non-zero exit if coverage is
    under the stated threshold.
    """
    config = ctx.obj["CONFIG"]
    aws_config = handle_aws_credentials_options(
        fides_config=config,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=region,
        credentials_id=credentials_id,
    )

    _system.scan_system_aws(
        manifest_dir=manifests_dir,
        organization_key=org_key,
        aws_config=aws_config,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )
