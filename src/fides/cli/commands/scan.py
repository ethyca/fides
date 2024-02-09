"""Contains the scan group of the commands for fides."""

import rich_click as click

from fides.cli.options import (
    aws_access_key_id_option,
    aws_region_option,
    aws_secret_access_key_option,
    aws_session_token_option,
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
    Scan and report on discrepancies between Fides resource files and real infrastructure.
    """


@scan.group(name="dataset")
@click.pass_context
def scan_dataset(ctx: click.Context) -> None:
    """
    Scan and report on Fides Dataset resources.
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
    Scan a database directly using a SQLAlchemy-style connection string.

    _If there are fields within the database that aren't listed and categorized
    within one of the datasets, this counts as lacking coverage._
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
        headers=config.user.auth_header,
        local=config.cli.local_mode,
    )


@scan.group(name="system")
@click.pass_context
def scan_system(ctx: click.Context) -> None:
    """
    Scan and report on Fides System resources.
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
    Scan an Okta account and compare applications with annotated Fides Systems.
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
        headers=config.user.auth_header,
    )


@scan_system.command(name="aws")
@click.pass_context
@manifests_dir_argument
@credentials_id_option
@aws_access_key_id_option
@aws_secret_access_key_option
@aws_session_token_option
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
    session_token: str,
    region: str,
    org_key: str,
    coverage_threshold: int,
) -> None:
    """
    Scan an AWS account and compare objects with annotated Fides Systems.

    _Scannable resources: [Redshift, RDS, DynamoDb, S3]_
    """
    config = ctx.obj["CONFIG"]
    aws_config = handle_aws_credentials_options(
        fides_config=config,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        region=region,
        credentials_id=credentials_id,
    )

    _system.scan_system_aws(
        manifest_dir=manifests_dir,
        organization_key=org_key,
        aws_config=aws_config,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.auth_header,
    )
