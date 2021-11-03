"""Contains all of the CLI commands for Fides."""
import pprint

import click

from fidesapi import database
from fidesapi.main import start_webserver
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
    annotate_dataset as _annotate_dataset,
    parse as _parse,
)
from fidesctl.core.utils import echo_green, echo_red


@click.command()
@click.pass_context
@dry_flag
@click.option(
    "--diff",
    is_flag=True,
    help="Print the diff between the server's old and new states in Python DeepDiff format",
)
@manifests_dir_argument
def apply(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Update server with your local resources.

    Reads the resource manifest files that are stored in MANIFESTS_DIR (and its subdirectories) and applies the resources to your server. If a named resource already exists, the resource is completely overwritten with the new description; if it doesn't exist, it's created.

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
    Delete a specified resource.

    Args:

        [resource type list] (string): the type of resource from the enumeration that you want to delete

        FIDES_KEY (string): the Fides key of the resource that you want to delete.
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
    help="The Fides key of the single policy that you wish to evaluate. This key is a string token that uniquely identifies the policy.",
)
@click.option(
    "-m",
    "--message",
    help="A message that you can supply to describe the purpose of this evaluation.",
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
    Assess your data's compliance to policies.

    This command will first `apply` the resources defined in MANIFESTS_DIR to your server and then assess your data's compliance to your policies or single policy.

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
    Connect a database to create a dataset.

    Automatically create a dataset .yml file by directly connecting the database.

    Args:

        connection_string (string): A SQLAlchemy-compatible connection string

        output_filename (str): A path to where the manifest will be written
    """

    _generate_dataset.generate_dataset(connection_string, output_filename)


@click.command()
@click.pass_context
@click.argument("input_filename", type=str)
@click.option(
    "-a",
    "--all-members",
    is_flag=True,
    help="Annotate all dataset members, not just fields",
)
@click.option(
    "-v", "--validate", is_flag=True, default=False, help="Validate annotation inputs"
)
def annotate_dataset(
    ctx: click.Context, input_filename: str, all_members: bool, validate: bool
) -> None:
    """
    Guided dataset annotation.

    Read and annotate a dataset.yml file to add data_categories in a guided UI. This command edits the input file in place.

    Args:

        input_filename: the dataset.yml file to be read and edited
    """
    _annotate_dataset.annotate_dataset(
        input_filename, annotate_all=all_members, validate=validate
    )


@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
def get(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    Print the resource as a JSON object.

    Args:

        [resource type list] (string): the type of resource from the enumeration that you want to retrieve

        FIDES_KEY (string): the Fides key of the resource that you want to retrieve
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
    Initialize and launch your Fides policy database.

    After you've initialized your database, you should add your policy resources by calling 'apply'.

    """
    config = ctx.obj["CONFIG"]
    database.init_db(config.api.database_url, fidesctl_config=config)


@click.command()
@click.pass_context
@resource_type_argument
def ls(ctx: click.Context, resource_type: str) -> None:  # pylint: disable=invalid-name
    """
    List resource objects.

    This command will print the JSON object for the specified resource.

    Args:

        [resource type list] (string): the type of resource from the enumeration that you want to retrieve
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
    Validate the taxonomy described by the manifest files.

    Reads the resource files that are stored in MANIFESTS_DIR and its subdirectories to verify presence of taxonomy valuse. If the taxonomy is successfully validated, the command prints a success message and returns 0. If invalid, the command prints one or more error messages and returns non-0.

    Note: No resources are applied to your server in this command. Enabling -v will print the taxonomy.
    """

    taxonomy = _parse.parse(manifests_dir)
    if verbose:
        pprint.pprint(taxonomy)


@click.command()
@click.pass_context
def ping(ctx: click.Context, config_path: str = "") -> None:
    """
    Confirm fidesctl is running.

    Sends a message to the Fides API health-check endpoint and prints the response.
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
    Full database cleanse.

    Removes the resources that you added through previous 'apply' calls, and then re-initializes the database by running `init-db`.

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
    Prints the current fidesctl configuration. You can modify the configuration by passing a configuration file to the 'fidesctl' command:

    $ fidesctl --config-path config_files
    """
    config = ctx.obj["CONFIG"]
    pretty_echo(config.dict(), color="green")


@click.command()
@click.pass_context
def webserver(ctx: click.Context) -> None:
    """
    Starts the fidesctl API server.
    """
    start_webserver()
