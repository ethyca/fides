"""Contains the generate group of CLI commands for fides."""
import click

from fides.cli.options import (
    aws_access_key_id_option,
    aws_region_option,
    aws_secret_access_key_option,
    connection_string_option,
    credentials_id_option,
    include_null_flag,
    okta_org_url_option,
    okta_token_option,
    organization_fides_key_option,
)
from fides.cli.utils import (
    handle_aws_credentials_options,
    handle_bigquery_config_options,
    handle_database_credentials_options,
    handle_okta_credentials_options,
    with_analytics,
)
from fides.core import dataset as _dataset
from fides.core import system as _system


@click.group(name="generate")
@click.pass_context
def generate(ctx: click.Context) -> None:
    """
    Generate fides resource types
    """


@generate.group(name="dataset")
@click.pass_context
def generate_dataset(ctx: click.Context) -> None:
    """
    Generate fides Dataset resources
    """


@generate_dataset.command(name="db")
@click.pass_context
@click.argument("output_filename", type=str)
@credentials_id_option
@connection_string_option
@include_null_flag
@with_analytics
def generate_dataset_db(
    ctx: click.Context,
    output_filename: str,
    connection_string: str,
    credentials_id: str,
    include_null: bool,
) -> None:
    """
    Connect to a database directly via a SQLAlchemy-style connection string and
    generate a dataset manifest file that consists of every schema/table/field.
    Connection string can be supplied as an option or a credentials reference
    to fides config.

    This is a one-time operation that does not track the state of the database.
    It will need to be run again if the database schema changes.
    """
    actual_connection_string = handle_database_credentials_options(
        fides_config=ctx.obj["CONFIG"],
        connection_string=connection_string,
        credentials_id=credentials_id,
    )

    _dataset.generate_dataset_db(
        connection_string=actual_connection_string,
        file_name=output_filename,
        include_null=include_null,
    )


@generate_dataset.group(name="gcp")
@click.pass_context
def generate_dataset_gcp(ctx: click.Context) -> None:
    """
    Generate fides Dataset resources for Google Cloud Platform
    """


@generate_dataset_gcp.command(name="bigquery")
@click.pass_context
@click.argument("dataset_name", type=str)
@click.argument("output_filename", type=str)
@credentials_id_option
@click.option("--keyfile-path", type=str)
@include_null_flag
@with_analytics
def generate_dataset_bigquery(
    ctx: click.Context,
    dataset_name: str,
    output_filename: str,
    keyfile_path: str,
    credentials_id: str,
    include_null: bool,
) -> None:
    """
    Connect to a BigQuery dataset directly via a SQLAlchemy connection and
    generate a dataset manifest file that consists of every schema/table/field.
    A path to a google authorization keyfile can be supplied as an option, or a
    credentials reference to fides config.

    This is a one-time operation that does not track the state of the dataset.
    It will need to be run again if the dataset schema changes.
    """

    bigquery_config = handle_bigquery_config_options(
        fides_config=ctx.obj["CONFIG"],
        dataset=dataset_name,
        keyfile_path=keyfile_path,
        credentials_id=credentials_id,
    )

    bigquery_datasets = _dataset.generate_bigquery_datasets(bigquery_config)

    _dataset.write_dataset_manifest(
        file_name=output_filename, include_null=include_null, datasets=bigquery_datasets
    )


@generate.group(name="system")
@click.pass_context
def generate_system(ctx: click.Context) -> None:
    """
    Generate fides System resources
    """


@generate_system.command(name="okta")
@click.pass_context
@click.argument("output_filename", type=str)
@credentials_id_option
@okta_org_url_option
@okta_token_option
@include_null_flag
@organization_fides_key_option
@with_analytics
def generate_system_okta(
    ctx: click.Context,
    output_filename: str,
    credentials_id: str,
    token: str,
    org_url: str,
    include_null: bool,
    org_key: str,
) -> None:
    """
    Generates systems for your Okta applications. Connect to an Okta admin
    account by providing an organization url and auth token or a credentials
    reference to fides config. Auth token and organization url can also
    be supplied by setting environment variables as defined by the okta python sdk.

    This is a one-time operation that does not track the state of the okta resources.
    It will need to be run again if the tracked resources change.
    """
    config = ctx.obj["CONFIG"]
    okta_config = handle_okta_credentials_options(
        fides_config=config,
        token=token,
        org_url=org_url,
        credentials_id=credentials_id,
    )

    _system.generate_system_okta(
        okta_config=okta_config,
        file_name=output_filename,
        include_null=include_null,
        organization_key=org_key,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )


@generate_system.command(name="aws")
@click.pass_context
@click.argument("output_filename", type=str)
@credentials_id_option
@aws_access_key_id_option
@aws_secret_access_key_option
@aws_region_option
@include_null_flag
@organization_fides_key_option
@with_analytics
def generate_system_aws(
    ctx: click.Context,
    output_filename: str,
    include_null: bool,
    org_key: str,
    credentials_id: str,
    access_key_id: str,
    secret_access_key: str,
    region: str,
) -> None:
    """
    Connect to an aws account and generate a system manifest file that consists of every
    tracked resource.
    Credentials can be supplied as options, a credentials
    reference to fides config, or boto3 environment configuration.
    Tracked resources: [Redshift, RDS, DynamoDb, S3]

    This is a one-time operation that does not track the state of the aws resources.
    It will need to be run again if the tracked resources change.
    """
    config = ctx.obj["CONFIG"]
    aws_config = handle_aws_credentials_options(
        fides_config=config,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=region,
        credentials_id=credentials_id,
    )

    _system.generate_system_aws(
        file_name=output_filename,
        include_null=include_null,
        organization_key=org_key,
        aws_config=aws_config,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )
