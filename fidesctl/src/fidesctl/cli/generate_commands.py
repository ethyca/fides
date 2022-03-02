"""Contains the generate group of CLI commands for Fidesctl."""
import click

from fidesctl.core import dataset as _dataset, system as _system

from fidesctl.cli.options import (
    include_null_flag,
)


@click.group(name="generate")
@click.pass_context
def generate(ctx: click.Context) -> None:
    """
    Generate fidesctl resource types
    """


@generate.command(name="dataset")
@click.pass_context
@click.argument("connection_string", type=str)
@click.argument("output_filename", type=str)
@include_null_flag
def generate_dataset(
    ctx: click.Context, connection_string: str, output_filename: str, include_null: bool
) -> None:
    """
    Connect to a database directly via a SQLAlchemy-style connection string and
    generate a dataset manifest file that consists of every schema/table/field.

    This is a one-time operation that does not track the state of the database.
    It will need to be run again if the database schema changes.
    """

    _dataset.generate_dataset(connection_string, output_filename, include_null)


@generate.group(name="system")
@click.pass_context
def generate_system(ctx: click.Context) -> None:
    """
    Generate fidesctl System resources
    """


@generate_system.command(name="aws")
@click.pass_context
@click.argument("output_filename", type=str)
@include_null_flag
def generate_system_aws(
    ctx: click.Context,
    output_filename: str,
    include_null: bool,
) -> None:
    """
    Connect to an aws account by leveraging a boto3 environment variable
    configuration and generate a system manifest file that consists of every
    tracked resource. Tracked resources: [Redshift, RDS]

    This is a one-time operation that does not track the state of the aws resources.
    It will need to be run again if the tracked resources change.
    """

    _system.generate_system_aws(output_filename, include_null)
