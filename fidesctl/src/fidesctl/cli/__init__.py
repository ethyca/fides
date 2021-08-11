"""Contains all of the CLI commands for Fidesctl."""
import json
from typing import Dict, Optional

import click
import fidesctl

from fidesctl.core import api as _api
from fidesctl.core import apply as _apply
from fidesctl.core import evaluate as _evaluate
from fidesctl.core import generate_dataset as _generate_dataset
from fidesctl.core.config import get_config, generate_request_headers

from .utils import (
    config_option,
    handle_cli_response,
    id_argument,
    manifest_option,
    object_type_argument,
    pretty_echo,
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


@cli.command()
@config_option
def config(config_path: str) -> None:
    """
    Print out the config values.
    """
    config = get_config(config_path)
    pretty_echo(config.dict(), color="green")


########################
### Generic Commands ###
########################
@cli.command(hidden=True)
@object_type_argument
@manifest_option
@config_option
def create(object_type: str, manifest: str, config_path: str = None) -> None:
    """
    Create a new object directly from a JSON object.
    """
    parsed_manifest = json.loads(manifest)
    config = get_config(config_path)
    handle_cli_response(
        _api.create(
            config.cli.server_url,
            object_type,
            parsed_manifest,
            config.user.request_headers,
        )
    )


@cli.command(hidden=True)
@object_type_argument
@id_argument
@config_option
def delete(object_type: str, object_id: str, config_path: str) -> None:
    """
    Delete an object by its id.
    """
    config = get_config(config_path)
    handle_cli_response(
        _api.delete(
            config.cli.server_url, object_type, object_id, config.user.request_headers
        )
    )


@cli.command()
@object_type_argument
@id_argument
@config_option
def find(object_type: str, object_id: str, config_path: str) -> None:
    """
    Get an object by its fidesKey.
    """
    config = get_config(config_path)
    handle_cli_response(
        _api.find(
            config.cli.server_url, object_type, object_id, config.user.request_headers
        )
    )


@cli.command(hidden=True)
@object_type_argument
@id_argument
@config_option
def get(object_type: str, object_id: str, config_path: str) -> None:
    """
    Get an object by its id.
    """
    config = get_config(config_path)
    handle_cli_response(
        _api.get(
            config.cli.server_url, object_type, object_id, config.user.request_headers
        )
    )


@cli.command()
@object_type_argument
@config_option
def show(object_type: str, config_path: str) -> None:
    """
    List all objects of a certain type.
    """
    config = get_config(config_path)
    handle_cli_response(
        _api.show(config.cli.server_url, object_type, config.user.request_headers)
    )


@cli.command(hidden=True)
@manifest_option
@object_type_argument
@id_argument
@config_option
def update(object_type: str, object_id: str, manifest: str, config_path: str) -> None:
    """
    Update an existing object by its id.
    """
    parsed_manifest = json.loads(manifest)
    config = get_config(config_path)
    handle_cli_response(
        _api.update(
            config.cli.server_url,
            object_type,
            object_id,
            parsed_manifest,
            config.user.request_headers,
        )
    )


########################
### Special Commands ###
########################
@cli.command()
@click.argument("manifest_dir", type=click.Path())
@config_option
def apply(manifest_dir: str, config_path: str) -> None:
    """
    Send the manifest files to the server.
    """
    config = get_config(config_path)
    _apply.apply(config.cli.server_url, manifest_dir, config.user.request_headers)


@cli.command()
def ping(config_path: str) -> None:
    """
    Ping the Server.
    """
    config = get_config(config_path)
    click.secho(f"Pinging {config.server_url}...", fg="green")
    _api.ping(config.server_url)
    click.secho("Ping Successful!", fg="green")


@cli.command()
@click.argument("connection_string", type=str)
@click.argument("output_filename", type=str)
@config_option
def generate_dataset(connection_string: str, output_filename: str) -> None:
    """
    Generates a comprehensive dataset manifest from a database.

    Args:

        connection_string (str): A SQLAlchemy-compatible connection string

        output_filename (str): A path to where the manifest will be written
    """

    _generate_dataset.generate_dataset(connection_string, output_filename)


################
### Evaluate ###
################
@cli.command()
@click.argument("manifest_dir", type=click.Path())
@click.argument("fides_key", type=str)
@config_option
def dry_evaluate(manifest_dir: str, fides_key: str, config_path: str) -> None:
    """
    Dry-Run evaluate a registry or system, either approving or denying
    based on organizational policies.
    """
    config = get_config(config_path)
    request_headers = generate_request_headers(config.user_id, config.user_api_key)
    handle_cli_response(
        _evaluate.dry_evaluate(
            config.server_url, manifest_dir, fides_key, request_headers
        )
    )


@cli.command()
@click.option("-t", "--tag", help="optional commit tag")
@click.option("-m", "--message", help="optional commit message")
@click.argument(
    "object_type", type=click.Choice(["system", "registry"], case_sensitive=False)
)
@click.argument("fides_key", type=str)
@config_option
def evaluate(
    object_type: str,
    fides_key: str,
    tag: str,
    message: str,
    config_path: str,
) -> None:
    """
    Evaluate a registry or system, either approving or denying
    based on organizational policies.
    """

    # if the version tag is none, use git tag if available
    if tag is None:
        tag = fidesctl.__version__
    config = get_config(config_path)
    request_headers = generate_request_headers(config.user_id, config.user_api_key)
    handle_cli_response(
        _evaluate.evaluate(
            config.server_url,
            object_type,
            fides_key,
            tag,
            message,
            request_headers,
        )
    )
