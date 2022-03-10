"""Contains the groups and setup for the CLI."""
import click
from fideslog.sdk.python.utils import generate_client_id, FIDESCTL_API

import fidesctl
from fidesctl.cli.utils import send_anonymous_event
from fidesctl.core.config import get_config
from fidesctl.core.config.utils import update_config_file
from fidesctl.core.utils import echo_red

from .annotate_commands import annotate
from .core_commands import apply, evaluate, parse
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

# This will be removed when the fideslog SDK is updated to expose it.
OPT_OUT_COPY = """
Fides needs your permission to send Ethyca a limited set of anonymous usage statistics.
Ethyca will only use this anonymous usage data to improve the product experience, and will never collect sensitive or personal data.

***
Don't believe us? Check out the open-source code here:
    https://github.com/ethyca/fideslog
***

To opt-out of all telemetry, press "n". To continue with telemetry, press any other key.
"""


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

    if ctx.obj["CONFIG"].user.analytics_opt_out is None:
        ctx.obj["CONFIG"].user.analytics_opt_out = bool(
            input(OPT_OUT_COPY).lower() == "n"
        )
        ctx.obj["CONFIG"].user.analytics_id = ctx.obj[
            "CONFIG"
        ].cli.analytics_id or generate_client_id(FIDESCTL_API)

        config_updates = {
            "cli": {"analytics_id": ctx.obj["CONFIG"].user.analytics_id},
            "user": {"analytics_opt_out": ctx.obj["CONFIG"].user.analytics_opt_out},
        }

        try:
            update_config_file(config_updates)
        except FileNotFoundError as err:
            echo_red(f"Failed to update config file: {err.strerror}")

    if not ctx.obj["CONFIG"].user.analytics_opt_out:
        send_anonymous_event(
            command=ctx.invoked_subcommand, client_id=ctx.obj["CONFIG"].cli.analytics_id
        )


# This is a special section used for auto-generating the CLI docs
# This has to be done due to the dynamic way in which commands are added for the real CLI group
cli_docs = cli

for cli_command in API_COMMANDS:
    cli_docs.add_command(cli_command)
