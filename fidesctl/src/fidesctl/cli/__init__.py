"""Contains the groups and setup for the CLI."""
import click

import fidesctl
from fidesctl.cli.cli import (
    apply,
    delete,
    evaluate,
    generate_dataset,
    annotate_dataset,
    get,
    init_db,
    ls,
    parse,
    ping,
    reset_db,
    view_config,
    webserver,
)
from fidesctl.core.config import get_config

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True, chain=True)
@click.version_option(version=fidesctl.__version__)
@click.option(
    "--config-path",
    "-f",
    "config_path",
    default="",
    help="Optional configuration file",
)
@click.option(
    "--local",
    is_flag=True,
    help="Do not make any API calls to the webserver.",
)
@click.pass_context
def cli(ctx: click.Context, config_path: str, local: bool) -> None:
    """
    The parent group for the Fidesctl CLI.
    """

    local_commands = [evaluate, parse, view_config]
    all_commands = [
        annotate_dataset,
        apply,
        delete,
        generate_dataset,
        get,
        init_db,
        ls,
        ping,
        reset_db,
        webserver,
    ] + local_commands

    ctx.ensure_object(dict)
    config = get_config(config_path)

    if local or config.cli.local_mode:
        config.cli.local_mode = True
        for command in local_commands:
            cli.add_command(command)
    else:
        for command in all_commands:
            cli.add_command(command)
    ctx.obj["CONFIG"] = config

    if not ctx.invoked_subcommand:
        click.echo(cli.get_help(ctx))
