"""Contains the groups and setup for the CLI."""
import click

import fidesctl
from fidesctl.core.config import get_config

from .annotate_commands import annotate
from .core_commands import (
    apply,
    evaluate,
    parse,
)
from .crud_commands import delete, get, ls
from .db_commands import database
from .export_commands import export
from .generate_commands import generate
from .scan_commands import scan
from .util_comands import init, ping, webserver
from .view_commands import view

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
LOCAL_COMMANDS = [evaluate, parse, view]
API_COMMANDS = [
    annotate,
    apply,
    delete,
    export,
    generate,
    scan,
    get,
    init,
    database,
    ls,
    ping,
    webserver,
] + LOCAL_COMMANDS


@click.group(
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
    name="fidesctl",
)
@click.version_option(version=fidesctl.__version__)
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

    ctx.ensure_object(dict)
    config = get_config(config_path)

    for command in LOCAL_COMMANDS:
        cli.add_command(command)

    # If local_mode is enabled, don't add unsupported commands
    if not (local or config.cli.local_mode):
        config.cli.local_mode = False
        for command in API_COMMANDS:
            cli.add_command(command)
    else:
        config.cli.local_mode = True
    ctx.obj["CONFIG"] = config

    if not ctx.invoked_subcommand:
        click.echo(cli.get_help(ctx))


# This is a special section used for auto-generating the CLI docs
# This has to be done due to the dynamic way in which commands are added for the real CLI group
cli_docs = cli

for cli_command in API_COMMANDS:
    cli_docs.add_command(cli_command)
