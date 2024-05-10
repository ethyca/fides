"""Contains the generate group of CLI commands for fides."""

import rich_click as click

from fides.cli.options import (
    aws_access_key_id_option,
    aws_region_option,
    aws_secret_access_key_option,
    aws_session_token_option,
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
    Programmatically generate Fides objects.
    """


@generate.group(name="dataset")
@click.pass_context
def generate_dataset(ctx: click.Context) -> None:
    """
    Generate Fides datasets.
    """


@generate_dataset.command(name="db")  # type: ignore
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
    Generate a Fides dataset by walking a database and recording every schema/table/field.
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
    Generate Fides datasets from Google Cloud Platform.
    """


@generate_dataset_gcp.command(name="bigquery")  # type: ignore
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
    Generate a dataset object from BigQuery using a SQLAlchemy connection string.
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


@generate_dataset.group(name="aws")
@click.pass_context
def generate_dataset_aws(ctx: click.Context) -> None:
    """
    Generate Fides datasets from specific Amazon Web Services.
    """


@generate_dataset_aws.command(name="dynamodb")  # type: ignore
@click.pass_context
@click.argument("output_filename", type=str)
@credentials_id_option
@aws_access_key_id_option
@aws_secret_access_key_option
@aws_session_token_option
@aws_region_option
@include_null_flag
@with_analytics
def generate_dataset_dynamodb(
    ctx: click.Context,
    output_filename: str,
    include_null: bool,
    credentials_id: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    region: str,
) -> None:
    """
    Generate a dataset object from BigQuery using a SQLAlchemy connection string.
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

    bigquery_dataset = _dataset.generate_dynamo_db_datasets(aws_config)

    _dataset.write_dataset_manifest(
        file_name=output_filename,
        include_null=include_null,
        datasets=[bigquery_dataset],
    )


@generate.group(name="system")
@click.pass_context
def generate_system(ctx: click.Context) -> None:
    """
    Generate Fides systems.
    """


@generate_system.command(name="okta")  # type: ignore
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
    Generates systems from your Okta applications. Connects via
    an Okta admin account.
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
        headers=config.user.auth_header,
    )


@generate_system.command(name="aws")  # type: ignore
@click.pass_context
@click.argument("output_filename", type=str)
@credentials_id_option
@aws_access_key_id_option
@aws_secret_access_key_option
@aws_session_token_option
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
    session_token: str,
    region: str,
) -> None:
    """
    Connect to an aws account and generate a system manifest file that consists of every
    tracked resource.
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

    _system.generate_system_aws(
        file_name=output_filename,
        include_null=include_null,
        organization_key=org_key,
        aws_config=aws_config,
        url=config.cli.server_url,
        headers=config.user.auth_header,
    )
