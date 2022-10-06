"""Contains the groups and setup for the CLI."""
from importlib.metadata import version
from os import getenv
from platform import system

import click
from fideslog.sdk.python.client import AnalyticsClient

import fidesctl
from fidesctl.cli.utils import check_and_update_analytics_config, check_server
from fidesctl.ctl.core.config import get_config

from .commands.annotate import annotate
from .commands.core import apply, evaluate, parse, pull, push
from .commands.crud import delete, get, ls
from .commands.db import database
from .commands.export import export
from .commands.generate import generate
from .commands.scan import scan
from .commands.util import init, status, webserver
from .commands.view import view

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
LOCAL_COMMANDS = [evaluate, generate, init, scan, parse, view, webserver]
LOCAL_COMMAND_DICT = {
    command.name or str(command): command for command in LOCAL_COMMANDS
}
API_COMMANDS = [annotate, apply, database, delete, export, get, ls, status, pull, push]
API_COMMAND_DICT = {command.name or str(command): command for command in API_COMMANDS}
ALL_COMMANDS = API_COMMANDS + LOCAL_COMMANDS
SERVER_CHECK_COMMAND_NAMES = [
    command.name for command in API_COMMANDS if command.name not in ["status"]
]
VERSION = fidesctl.__version__
APP = fidesctl.__name__


@click.group(
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
    name="fidesctl",
)
@click.version_option(version=VERSION)
@click.option(
    "--config-path",
    "-f",
    "config_path",
    default="",
    help="Path to a configuration file. Use 'fidesctl view-config' to print the config. Not compatible with the 'fidesctl webserver' subcommand.",
)
@click.option(
    "--local",
    is_flag=True,
    help="Run in 'local_mode'. This mode doesn't make API calls and can be used without the API server/database.",
)
@click.pass_context
def cli(ctx: click.Context, config_path: str, local: bool) -> None:
    """
    The parent group for the Fidesctl CLI.
    """

    docs_link = "https://ethyca.github.io/fides/"
    click.secho(
        f"WARNING: 'Fidesctl' has been deprecated and replaced by a more robust 'Fides' tool, which includes existing 'fidesctl' functionality. Run `pip install ethyca-fides` to get the latest version of Fides and visit '{docs_link}' for up-to-date documentation.\n",
        fg="red",
    )
    ctx.ensure_object(dict)
    config = get_config(config_path)

    # Dyanmically add commands to the CLI
    cli.commands = LOCAL_COMMAND_DICT

    if not (local or config.cli.local_mode):
        config.cli.local_mode = False
        cli.commands = {**cli.commands, **API_COMMAND_DICT}
    else:
        config.cli.local_mode = True

    ctx.obj["CONFIG"] = config

    # Run the help command if no subcommand is passed
    if not ctx.invoked_subcommand:
        click.echo(cli.get_help(ctx))

    # Check the server health and version if an API command is invoked

    if ctx.invoked_subcommand in SERVER_CHECK_COMMAND_NAMES:
        check_server(VERSION, config.cli.server_url, quiet=True)

    # init also handles this workflow
    if ctx.invoked_subcommand != "init":
        check_and_update_analytics_config(ctx, config_path)

        # Analytics requires explicit opt-in
        if ctx.obj["CONFIG"].user.analytics_opt_out is False:
            ctx.meta["ANALYTICS_CLIENT"] = AnalyticsClient(
                client_id=ctx.obj["CONFIG"].cli.analytics_id,
                developer_mode=bool(getenv("FIDESCTL_TEST_MODE") == "True"),
                os=system(),
                product_name=APP + "-cli",
                production_version=version(APP),
            )


# Add all commands here before dynamically checking them in the CLI
for cli_command in ALL_COMMANDS:
    cli.add_command(cli_command)
