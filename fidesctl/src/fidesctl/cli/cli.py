"""Contains all of the CLI commands for Fides."""
import click
import requests

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
    help="Print the diff between the server's old and new states in Python DeepDiff format",
)
@manifests_dir_argument
def apply(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Validates local manifest files and then sends them to the server to be persisted.
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
    Delete a resource on the server.
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
    help="The fides_key of the single policy that you wish to evaluate.",
)
@click.option(
    "-m",
    "--message",
    help="A message that you can supply to describe the context of this evaluation.",
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
    Compare your System's Privacy Declarations with your Organization's Policy Rules.

    All local resources are applied to the server before evaluation.

    If your policy evaluation fails, it is expected that you will need to
    either adjust your Privacy Declarations, Datasets, or Policies before trying again.
    """

    config = ctx.obj["CONFIG"]

    if config.cli.local_mode:
        dry = True
    else:
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
        policy_fides_key=fides_key,
        message=message,
        local=config.cli.local_mode,
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
    Connect to a database directly via a SQLAlchemy-stlye connection string and
    generate a dataset manifest file that consists of every schema/table/field.

    This is a one-time operation that does not track the state of the database.
    It will need to be run again if the database schema changes.
    """

    _generate_dataset.generate_dataset(connection_string, output_filename)


@click.command()
@click.pass_context
@click.argument("source_type", type=click.Choice(["database"]))
@click.argument("connection_string", type=str)
@click.option("-m", "--manifest-dir", type=str, default="")
@click.option("-c", "--coverage-threshold", type=click.IntRange(0, 100), default=100)
def scan(
    ctx: click.Context,
    source_type: str,
    connection_string: str,
    manifest_dir: str,
    coverage_threshold: int,
) -> None:
    """
    Connect to a database directly via a SQLAlchemy-stlye connection string and
    compare the database objects to existing datasets.

    If there are fields within the database that aren't listed and categorized
    within one of the datasets, this counts as lacking coverage.

    Outputs missing fields and has a non-zero exit if coverage is
    under the stated threshold.
    """
    config = ctx.obj["CONFIG"]
    _generate_dataset.database_coverage(
        connection_string=connection_string,
        manifest_dir=manifest_dir,
        coverage_threshold=coverage_threshold,
        url=config.cli.server_url,
        headers=config.user.request_headers,
    )


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
    "-v",
    "--validate",
    is_flag=True,
    default=False,
    help="Strictly validate annotation inputs.",
)
def annotate_dataset(
    ctx: click.Context, input_filename: str, all_members: bool, validate: bool
) -> None:
    """
    Guided flow for annotating datasets. The dataset file will be edited in-place.
    """
    try:
        from fidesctl.core import annotate_dataset as _annotate_dataset
    except ModuleNotFoundError:
        echo_red('Packages not found, try: pip install "fidesctl[webserver]"')
        raise SystemExit

    _annotate_dataset.annotate_dataset(
        input_filename, annotate_all=all_members, validate=validate
    )


@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
def get(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    View a resource from the server as a JSON object.
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
    Initialize the Fidesctl database.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(_api.db_action(config.cli.server_url, "init"))


@click.command()
@click.pass_context
@resource_type_argument
def ls(ctx: click.Context, resource_type: str) -> None:  # pylint: disable=invalid-name
    """
    Get a list of all resources of this type from the server and display them as JSON.
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
    Reads the resource files that are stored in MANIFESTS_DIR and its subdirectories to verify
    the validity of all manifest files.

    If the taxonomy is invalid, this command prints the error messages and triggers a non-zero exit code.
    """
    taxonomy = _parse.parse(manifests_dir)
    if verbose:
        pretty_echo(taxonomy.dict(), color="green")


@click.command()
@click.pass_context
def ping(ctx: click.Context, config_path: str = "") -> None:
    """
    Sends a request to the Fidesctl API healthcheck endpoint and prints the response.
    """
    config = ctx.obj["CONFIG"]
    healthcheck_url = config.cli.server_url + "/health"
    echo_green(f"Pinging {healthcheck_url}...")
    try:
        handle_cli_response(_api.ping(healthcheck_url))
    except requests.exceptions.ConnectionError:
        echo_red("Connection failed, webserver is unreachable.")


@click.command()
@click.pass_context
@yes_flag
def reset_db(ctx: click.Context, yes: bool) -> None:
    """
    Wipes all user-created data and resets the database back to its freshly initialized state.
    """
    config = ctx.obj["CONFIG"]
    if yes:
        are_you_sure = "y"
    else:
        echo_red(
            "This will drop all data from the Fides database and reload the default taxonomy!"
        )
        are_you_sure = input("Are you sure [y/n]? ")

    if are_you_sure.lower() == "y":
        handle_cli_response(_api.db_action(config.cli.server_url, "reset"))
    else:
        print("Aborting!")


@click.command()
@click.pass_context
def view_config(ctx: click.Context) -> None:
    """
    Prints the current fidesctl configuration values.
    """
    config = ctx.obj["CONFIG"]
    pretty_echo(config.dict(), color="green")


@click.command()
@click.pass_context
def webserver(ctx: click.Context) -> None:
    """
    Starts the fidesctl API server using Uvicorn on port 8080.
    """
    try:
        from fidesapi.main import start_webserver
    except ModuleNotFoundError:
        echo_red('Packages not found, try: pip install "fidesctl[webserver]"')
        raise SystemExit

    start_webserver()
