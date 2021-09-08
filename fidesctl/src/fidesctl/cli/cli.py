"""Contains all of the CLI commands for Fides."""
import click

from fidesctl.cli.options import (
    dry_flag,
    fides_key_argument,
    id_argument,
    manifests_dir_argument,
    resource_type_argument,
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
)


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
@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
def find(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    Get an resource by its fidesKey.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.find(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_key=fides_key,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@resource_type_argument
@id_argument
def delete(ctx: click.Context, resource_type: str, resource_id: str) -> None:
    """
    Delete an resource by its id.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.delete(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_id=resource_id,
            headers=config.user.request_headers,
        )
    )


@click.command(hidden=True)
@click.pass_context
@resource_type_argument
@id_argument
def get(ctx: click.Context, resource_type: str, resource_id: str) -> None:
    """
    Get an resource by its id.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.get(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_id=resource_id,
            headers=config.user.request_headers,
        )
    )


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


########################
### Special Commands ###
########################
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
    _apply.apply(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.request_headers,
        dry=dry,
        diff=diff,
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
@manifests_dir_argument
@click.option(
    "-k", "--fides-key", help="The fidesKey for the specific Policy to be evaluated."
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
    _apply.apply(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
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
