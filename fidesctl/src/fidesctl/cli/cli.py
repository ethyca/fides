"""Contains all of the CLI commands for Fides."""
import pprint

import click

from fidesapi.main import start_webserver
from fidesapi import database
from fidesctl.cli.options import (
    dry_flag,
    fides_key_argument,
    manifests_dir_argument,
    resource_type_argument,
    yes_flag,
    verbose_flag,
)
from fidesctl.cli.utils import (
    handle_cli_response,
    pretty_echo,
)
from fidesctl.core import (
    api as _api,
    apply as _apply,
    evaluate as _evaluate,
    generate_dataset as _generate_dataset,
    parse as _parse,
)
from fidesctl.core.utils import echo_green, echo_red


@click.command()
@click.pass_context
@dry_flag
@click.option(
    "--diff",
    is_flag=True,
    help="Outputs a detailed diff of the local resource files compared to the server resources.",
)
@manifests_dir_argument
def apply(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Send the manifest files to the server.
    """
    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _apply.apply(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.request_headers,
        dry=dry,
        diff=diff,
    )


@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
def delete(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    Delete an resource by its id.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.delete(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_id=fides_key,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@manifests_dir_argument
@click.option(
    "-k",
    "--fides-key",
    default="",
    help="The fides_key for the specific Policy to be evaluated.",
)
@click.option(
    "-m", "--message", help="Description of the changes this evaluation encapsulates."
)
@dry_flag
def evaluate(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
    message: str,
    dry: bool,
) -> None:
    """
    Evaluate a registry or system, either approving or denying
    based on organizational policies.

    Evaluate will always run the "apply" command before the
    evaluation, either dry or not depending on the flag
    passed to "evaluate".
    """

    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _apply.apply(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.request_headers,
        dry=dry,
    )

    _evaluate.evaluate(
        url=config.cli.server_url,
        headers=config.user.request_headers,
        manifests_dir=manifests_dir,
        fides_key=fides_key,
        message=message,
        dry=dry,
    )


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


@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
def get(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    Get an resource by its id.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.get(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_id=fides_key,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
def init_db(ctx: click.Context) -> None:
    """
    Initialize or upgrade the database by running all of the existing migrations.
    """
    config = ctx.obj["CONFIG"]
    database.init_db(config.api.database_url, fidesctl_config=config)


@click.command()
@click.pass_context
@resource_type_argument
def ls(ctx: click.Context, resource_type: str) -> None:  # pylint: disable=invalid-name
    """
    List all resources of a certain type.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.ls(
            url=config.cli.server_url,
            resource_type=resource_type,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@manifests_dir_argument
@verbose_flag
def parse(ctx: click.Context, manifests_dir: str, verbose: bool = False) -> None:
    """
    Parse the file(s) at the provided path into a Taxonomy and surface any validation errors.
    """

    taxonomy = _parse.parse(manifests_dir)
    if verbose:
        pprint.pprint(taxonomy)


@click.command()
@click.pass_context
def ping(ctx: click.Context, config_path: str = "") -> None:
    """
    Ping the Server.
    """
    config = ctx.obj["CONFIG"]
    healthcheck_url = config.cli.server_url + "/health"
    echo_green(f"Pinging {healthcheck_url}...")
    handle_cli_response(_api.ping(healthcheck_url))


@click.command()
@click.pass_context
@yes_flag
def reset_db(ctx: click.Context, yes: bool) -> None:
    """
    Drops all tables and metadata from the database and
    re-initializes the database.
    """
    config = ctx.obj["CONFIG"]
    database_url = config.api.database_url
    if yes:
        are_you_sure = "y"
    else:
        echo_red("This will drop all data from the Fides database!")
        are_you_sure = input("Are you sure [y/n]?")

    if are_you_sure.lower() == "y":
        database.reset_db(database_url)
        database.init_db(database_url, config)
        echo_green("Database reset!")
    else:
        print("Aborting!")


@click.command()
@click.pass_context
def view_config(ctx: click.Context) -> None:
    """
    Print out the config values.
    """
    config = ctx.obj["CONFIG"]
    pretty_echo(config.dict(), color="green")


@click.command()
@click.pass_context
def webserver(ctx: click.Context) -> None:
    """
    Starts the API webserver.
    """
    start_webserver()
