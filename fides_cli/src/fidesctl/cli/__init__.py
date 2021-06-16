"""Contains all of the CLI commands for Fidesctl."""
import json

import click

import fidesctl
from fidesctl.core import (
    api as _api,
    apply as _apply,
    evaluate as _evaluate,
    generate_dataset as _generate_dataset,
)

from .utils import (
    url_option,
    manifest_option,
    id_argument,
    object_type_argument,
    handle_cli_response,
)

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli() -> None:
    """
    The Fides CLI for managing Fides systems.
    """


@cli.command()
def version() -> None:
    """
    Get the current Fidesctl version.
    """
    click.echo(fidesctl.__version__)


####################
### Generic Commands
####################
@cli.command(hidden=True)
@url_option
@object_type_argument
@manifest_option
def create(url: str, object_type: str, manifest: str) -> None:
    """
    Create a new object directly from a JSON object.
    """
    parsed_manifest = json.loads(manifest)
    handle_cli_response(_api.create(url, object_type, parsed_manifest))


@cli.command(hidden=True)
@url_option
@object_type_argument
@id_argument
def delete(url: str, object_type: str, object_id: str) -> None:
    """
    Delete an object by its id.
    """
    handle_cli_response(_api.delete(url, object_type, object_id))


@cli.command()
@url_option
@object_type_argument
@id_argument
def find(url: str, object_type: str, object_id: str) -> None:
    """
    Get an object by its fidesKey.
    """
    handle_cli_response(_api.find(url, object_type, object_id))


@cli.command(hidden=True)
@url_option
@object_type_argument
@id_argument
def get(url: str, object_type: str, object_id: str) -> None:
    """
    Get an object by its id.
    """
    handle_cli_response(_api.get(url, object_type, object_id))


@cli.command()
@url_option
@object_type_argument
def show(url: str, object_type: str) -> None:
    """
    List all objects of a certain type.
    """
    handle_cli_response(_api.show(url, object_type))


@cli.command(hidden=True)
@url_option
@manifest_option
@object_type_argument
@id_argument
def update(url: str, object_type: str, object_id: str, manifest: str) -> None:
    """
    Update an existing object by its id.
    """
    parsed_manifest = json.loads(manifest)
    handle_cli_response(_api.update(url, object_type, object_id, parsed_manifest))


#########
### Special Commands
#########
@cli.command()
@url_option
@click.argument("manifest_dir", type=click.Path())
def apply(url: str, manifest_dir: str) -> None:
    """
    Send the manifest files to the server.
    """
    _apply.apply(url, manifest_dir)


@cli.command()
@url_option
def ping(url: str) -> None:
    """
    Ping the Server.
    """
    click.secho(f"Pinging {url}...", fg="green")
    _api.ping(url)
    click.secho("Ping Successful!", fg="green")


@cli.command()
@click.argument("connection_string", type=str)
@click.argument("output_filename", type=str)
def generate_dataset(connection_string: str, output_filename: str) -> None:
    """
    Generates a comprehensive dataset manifest from a database.

    Args:

        connection_string (str): A SQLAlchemy-compatible connection string

        output_filename (str): A path to where the manifest will be written
    """
    _generate_dataset.generate_dataset(connection_string, output_filename)


@cli.command()
@url_option
@click.argument("manifest_dir", type=click.Path())
@click.argument("fides_key", type=str)
@click.argument("dryrun", type=bool, default=True)
def evaluate(url: str, manifest_dir: str, fides_key: str, dryrun: bool) -> None:
    """
    Evaluate a registry or system, either approving or denying
    based on organizational policies.
    """
    handle_cli_response(_evaluate.evaluate(url, manifest_dir, fides_key))
