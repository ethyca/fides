"""Contains all of the CLI commands for Fidesctl."""
from fidesctl.src.fidesctl.core.config import generate_request_headers
import json
from typing import Optional

import click

import fidesctl
from fidesctl.core import (
    api as _api,
    apply as _apply,
    evaluate as _evaluate,
    generate_dataset as _generate_dataset,
)
from fidesctl.core.config import read_config

from .utils import (
    url_option,
    manifest_option,
    id_argument,
    object_type_argument,
    handle_cli_response,
    config_option,
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


########################
### Generic Commands ###
########################
@cli.command(hidden=True)
@url_option
@object_type_argument
@manifest_option
@config_option
def create(url: str, object_type: str, manifest: str, config: Optional[str]) -> None:
    """
    Create a new object directly from a JSON object.
    """
    parsed_manifest = json.loads(manifest)
    config = read_config(config)
    request_headers = generate_request_headers()
    handle_cli_response(
        _api.create(
            url,
            object_type,
            parsed_manifest,
            request_headers,
        )
    )


@cli.command(hidden=True)
@url_option
@object_type_argument
@id_argument
@config_option
def delete(url: str, object_type: str, object_id: str, config: Optional[str]) -> None:
    """
    Delete an object by its id.
    """
    handle_cli_response(
        _api.delete(
            url, object_type, object_id, read_conf(config).generate_request_headers()
        )
    )


@cli.command()
@url_option
@object_type_argument
@id_argument
@config_option
def find(url: str, object_type: str, object_id: str, config: Optional[str]) -> None:
    """
    Get an object by its fidesKey.
    """
    handle_cli_response(
        _api.find(
            url, object_type, object_id, read_conf(config).generate_request_headers()
        )
    )


@cli.command(hidden=True)
@url_option
@object_type_argument
@id_argument
@config_option
def get(url: str, object_type: str, object_id: str, config: Optional[str]) -> None:
    """
    Get an object by its id.
    """
    handle_cli_response(
        _api.get(
            url, object_type, object_id, read_conf(config).generate_request_headers()
        )
    )


@cli.command()
@url_option
@object_type_argument
@config_option
def show(url: str, object_type: str, config: Optional[str]) -> None:
    """
    List all objects of a certain type.
    """
    handle_cli_response(
        _api.show(url, object_type, generate_request_headers(read_config(config)))
    )


@cli.command(hidden=True)
@url_option
@manifest_option
@object_type_argument
@id_argument
@config_option
def update(
    url: str, object_type: str, object_id: str, manifest: str, config: Optional[str]
) -> None:
    """
    Update an existing object by its id.
    """
    parsed_manifest = json.loads(manifest)
    handle_cli_response(
        _api.update(
            url,
            object_type,
            object_id,
            parsed_manifest,
            read_conf(config).generate_request_headers(),
        )
    )


########################
### Special Commands ###
########################
@cli.command()
@url_option
@click.argument("manifest_dir", type=click.Path())
@config_option
def apply(url: str, manifest_dir: str, config: Optional[str]) -> None:
    """
    Send the manifest files to the server.
    """
    _apply.apply(url, manifest_dir, read_conf(config).generate_request_headers())


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
@config_option
def generate_dataset(
    connection_string: str, output_filename: str, config: Optional[str]
) -> None:
    """
    Generates a comprehensive dataset manifest from a database.

    Args:

        connection_string (str): A SQLAlchemy-compatible connection string

        output_filename (str): A path to where the manifest will be written
    """

    _generate_dataset.generate_dataset(
        connection_string, output_filename, read_conf(config).generate_request_headers()
    )


################
### Evaluate ###
################
@cli.command()
@url_option
@click.argument("manifest_dir", type=click.Path())
@click.argument("fides_key", type=str)
@config_option
def dry_evaluate(
    url: str, manifest_dir: str, fides_key: str, config: Optional[str]
) -> None:
    """
    Dry-Run evaluate a registry or system, either approving or denying
    based on organizational policies.
    """
    handle_cli_response(
        _evaluate.dry_evaluate(
            url, manifest_dir, fides_key, read_conf(config).generate_request_headers()
        )
    )


@cli.command()
@url_option
@click.option("-t", "--tag", help="optional commit tag")
@click.option("-m", "--message", help="optional commit message")
@click.argument(
    "object_type", type=click.Choice(["system", "registry"], case_sensitive=False)
)
@click.argument("fides_key", type=str)
@config_option
def evaluate(
    url: str,
    object_type: str,
    fides_key: str,
    tag: str,
    message: str,
    config: Optional[str],
) -> None:
    """
    Evaluate a registry or system, either approving or denying
    based on organizational policies.
    """

    # if the version tag is none, use git tag if available
    if tag is None:
        tag = fidesctl.__version__
    handle_cli_response(
        _evaluate.evaluate(
            url,
            object_type,
            fides_key,
            tag,
            message,
            read_conf(config).generate_request_headers(),
        )
    )
