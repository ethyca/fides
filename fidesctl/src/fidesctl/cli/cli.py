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
    help="In addition to printing the number of changed resources, the command prints a diff between the server's old and new states. The diff is in Python DeepDiff format."
)
@manifests_dir_argument
def apply(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Reads the resource manifest files that are stored in MANIFESTS_DIR (and its subdirectories) and applies the resources to your server. If a named resource already exists, the resource is completely overwritten with the new description; if it doesn't exist, it's created.

    The files in the MANIFESTS_DIR tree must be in YAML format and may only describe Fides resources. If you include any other file, the command will fail and the valid resource manifests will be ignored. 
    
    As it processes the manifests, the command announces how many resources it has created, updated, and deleted.
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
    Deletes the resource object identified by the arguments. 

    * The first argument is the type of resource that you want to delete; it must be one of the values listed in Usage.

    * The second argument (FIDES_KEY) is the fides key of the resource that you want to delete. The key is given as the fides-key property in the manifest file that defines the resource. To print resource objects (including an object's fides-key property) to the terminal, call 'fidesctl ls resource-type'.
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
    help="The fides key of the single policy that you wish to evaluate. The key is a string token that uniquely identifies the policy. A policy's fides key is given as the fides-key property in the manifest file that defines the policy resource. To print the policy resources to the terminal, call 'fidesctl ls policy'."
)
@click.option(
    "-m", "--message", help="A message that you can supply to describe the purpose of this evaluation."
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
     Applies the resources defined in MANIFESTS_DIR to your server and then assesses your data's compliance to your policies (or to a single policy if you use the --fides-key option). A failure means that you're trying to publish data that shouldn't be published; it's expected that you'll correct the data (or adjust the policy) before your next app deployment.
    
    'evaluate' applies your resources by calling 'apply'. Thus, you don't have to call 'apply' yourself before you call 'evaluate'.
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
    Prints a JSON object that describes the resource object identified by the arguments. 

    * The first argument is the type of resource that you want to retrieve; it must be one of the values listed in Usage.

    * The second argument (FIDES_KEY) is the fides key of the resource that you want to retrieve. The key is given as the fides-key property in the manifest file that defines the resource. To print resource objects (including an object's fides-key property) to the terminal, call 'fidesctl ls resource-type'.
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
    Initializes and launches your Fides policy database. After you've initialized your database, you should add your policy resources by calling 'apply'.

    """
    config = ctx.obj["CONFIG"]
    database.init_db(config.api.database_url, fidesctl_config=config)


@click.command()
@click.pass_context
@resource_type_argument
def ls(ctx: click.Context, resource_type: str) -> None:  # pylint: disable=invalid-name
    """
    Prints a series of JSON objects that describe the resource objects of the type specified by the argument. The argument must be one of the values listed in Usage.
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
    Validates the taxonomy that's described by the resource manifest files that are stored in MANIFESTS_DIR and its subdirectories. If the taxonomy is successfully validated, the command prints a success message ("Taxonomy successfully created.") and returns 0. If its invalid, the command prints one or more error messages and returns non-0. 

    The taxonomy itself isn't printed by default. To print it, include the --verbose option.

    The resources that make up the taxonomy aren't applied to your server. 
    """

    taxonomy = _parse.parse(manifests_dir)
    if verbose:
        pprint.pprint(taxonomy)


@click.command()
@click.pass_context
def ping(ctx: click.Context, config_path: str = "") -> None:
    """
    Sends a message to the fides API healthcheck endpoint and prints the response.
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
    Removes the resources that you added through previous 'apply' calls, and then re-initializes the database by calling 'init-db'.

    Before it removes the resources, the command prompts you to confirm the removal. To suppress the prompt, include the '--yes' option.
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
