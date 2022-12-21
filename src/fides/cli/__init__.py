"""Contains the groups and setup for the CLI."""
from importlib.metadata import version
from platform import system

import click
from fideslog.sdk.python.client import AnalyticsClient

import fides
from fides.cli.utils import check_and_update_analytics_config, check_server
from fides.core.config import get_config
from fides.core.config.helpers import create_config_file

from .commands.annotate import annotate
from .commands.core import evaluate, parse, pull, push
from .commands.crud import delete, get_resource, list_resources
from .commands.db import database
from .commands.export import export
from .commands.generate import generate
from .commands.scan import scan
from .commands.util import deploy, init, status, webserver, worker
from .commands.view import view

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
LOCAL_COMMANDS = [deploy, evaluate, generate, init, scan, parse, view, webserver]
LOCAL_COMMAND_DICT = {
    command.name or str(command): command for command in LOCAL_COMMANDS
}
API_COMMANDS = [
    annotate,
    database,
    delete,
    export,
    get_resource,
    list_resources,
    status,
    pull,
    push,
    worker,
]
API_COMMAND_DICT = {command.name or str(command): command for command in API_COMMANDS}
ALL_COMMANDS = API_COMMANDS + LOCAL_COMMANDS
SERVER_CHECK_COMMAND_NAMES = [
    command.name for command in API_COMMANDS if command.name not in ["status", "worker"]
]
VERSION = fides.__version__
APP = fides.__name__
PACKAGE = "ethyca-fides"


@click.group(
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
    name="fides",
)
@click.version_option(version=VERSION)
@click.option(
    "--config-path",
    "-f",
    "config_path",
    default="",
    help="Path to a configuration file. Use 'fides view-config' to print the config. Not compatible with the 'fides webserver' subcommand.",
)
@click.option(
    "--local",
    is_flag=True,
    help="Run in 'local_mode'. This mode doesn't make API calls and can be used without the API server/database.",
)
@click.pass_context
def cli(ctx: click.Context, config_path: str, local: bool) -> None:
    """
    The parent group for the Fides CLI.
    """

    ctx.ensure_object(dict)
    config = get_config(config_path, verbose=True)

    # Dyanmically add commands to the CLI
    cli.commands = LOCAL_COMMAND_DICT

    if not (local or config.cli.local_mode):
        config.cli.local_mode = False
        cli.commands = {**cli.commands, **API_COMMAND_DICT}
    else:
        config.cli.local_mode = True

    # Run the help command if no subcommand is passed
    if not ctx.invoked_subcommand:
        click.echo(cli.get_help(ctx))

    # Check the server health and version if an API command is invoked
    if ctx.invoked_subcommand in SERVER_CHECK_COMMAND_NAMES:
        check_server(VERSION, str(config.cli.server_url), quiet=True)

    # Analytics requires explicit opt-in
    no_analytics = config.user.analytics_opt_out
    if not no_analytics:
        ctx.meta["ANALYTICS_CLIENT"] = AnalyticsClient(
            client_id=config.cli.analytics_id,
            developer_mode=config.test_mode,
            os=system(),
            product_name=APP + "-cli",
            production_version=version(PACKAGE),
        )

    # Setting the config context after all mutations
    ctx.obj["CONFIG"] = config


# Add all commands here before dynamically checking them in the CLI
for cli_command in ALL_COMMANDS:
    cli.add_command(cli_command)
