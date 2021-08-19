"""Contains all of the CLI commands for Fides."""
import json

import click

from fidesctl.cli.options import (
    id_argument,
    manifest_option,
    object_type_argument,
)
from fidesctl.cli.utils import (
    handle_cli_response,
    pretty_echo,
)
from fidesctl.core import api as _api
from fidesctl.core import apply as _apply
from fidesctl.core import evaluate as _evaluate
from fidesctl.core import generate_dataset as _generate_dataset


@click.command()
@click.pass_context
def view_config(ctx: click.Context) -> None:
    """
    Print out the config values.
    """
    config = ctx.obj["CONFIG"]
    pretty_echo(config.dict(), color="green")


########################
### Generic Commands ###
########################
@click.command(hidden=True)
@click.pass_context
@object_type_argument
@manifest_option
def create(ctx: click.Context, object_type: str, manifest: str) -> None:
    """
    Create a new object directly from a JSON object.
    """
    parsed_manifest = json.loads(manifest)
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.create(
            url=config.cli.server_url,
            object_type=object_type,
            json_object=parsed_manifest,
            headers=config.user.request_headers,
        )
    )


@click.command(hidden=True)
@click.pass_context
@object_type_argument
@id_argument
def delete(ctx: click.Context, object_type: str, object_id: str) -> None:
    """
    Delete an object by its id.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.delete(
            url=config.cli.server_url,
            object_type=object_type,
            object_id=object_id,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@object_type_argument
@id_argument
def find(ctx: click.Context, object_type: str, object_id: str) -> None:
    """
    Get an object by its fidesKey.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.find(
            url=config.cli.server_url,
            object_type=object_type,
            object_key=object_id,
            headers=config.user.request_headers,
        )
    )


@click.command(hidden=True)
@click.pass_context
@object_type_argument
@id_argument
def get(ctx: click.Context, object_type: str, object_id: str) -> None:
    """
    Get an object by its id.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.get(
            url=config.cli.server_url,
            object_type=object_type,
            object_id=object_id,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@object_type_argument
def show(ctx: click.Context, object_type: str) -> None:
    """
    List all objects of a certain type.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.show(
            url=config.cli.server_url,
            object_type=object_type,
            headers=config.user.request_headers,
        )
    )


@click.command(hidden=True)
@click.pass_context
@manifest_option
@object_type_argument
@id_argument
def update(ctx: click.Context, object_type: str, object_id: str, manifest: str) -> None:
    """
    Update an existing object by its id.
    """
    parsed_manifest = json.loads(manifest)
    config = ctx.obj["CONFIG"]
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
@click.command()
@click.pass_context
@click.argument("manifest_dir", type=click.Path())
def apply(ctx: click.Context, manifest_dir: str) -> None:
    """
    Send the manifest files to the server.
    """
    config = ctx.obj["CONFIG"]
    _apply.apply(
        url=config.cli.server_url,
        manifests_dir=manifest_dir,
        headers=config.user.request_headers,
    )


@click.command()
@click.pass_context
def ping(ctx: click.Context, config_path: str = "") -> None:
    """
    Ping the Server.
    """
    config = ctx.obj["CONFIG"]
    click.secho(f"Pinging {config.cli.server_url}...", fg="green")
    _api.ping(config.cli.server_url)
    click.secho("Ping Successful!", fg="green")


@click.command()
@click.pass_context
@click.argument("connection_string", type=str)
@click.argument("output_filename", type=str)
def generate_dataset(
    ctx: click.Context, connection_string: str, output_filename: str
) -> None:
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
@click.command()
@click.pass_context
@click.argument("manifest_dir", type=click.Path())
@click.argument("fides_key", type=str)
def dry_evaluate(ctx: click.Context, manifest_dir: str, fides_key: str) -> None:
    """
    Dry-Run evaluate a registry or system, either approving or denying
    based on organizational policies.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _evaluate.dry_evaluate(
            url=config.cli.server_url,
            manifests_dir=manifest_dir,
            fides_key=fides_key,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@click.option("-t", "--tag", help="optional commit tag")
@click.option("-m", "--message", help="optional commit message")
@click.argument(
    "object_type", type=click.Choice(["system", "registry"], case_sensitive=False)
)
@click.argument("fides_key", type=str)
def evaluate(
    ctx: click.Context,
    object_type: str,
    fides_key: str,
    tag: str,
    message: str,
) -> None:
    """
    Evaluate a registry or system, either approving or denying
    based on organizational policies.
    """

    if tag is None:
        tag = "DEFAULT_TAG"
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _evaluate.evaluate(
            url=config.cli.server_url,
            object_type=object_type,
            fides_key=fides_key,
            tag=tag,
            message=message,
            headers=config.user.request_headers,
        )
    )
