"""Contains the groups and setup for the CLI."""
import click

import fidesctl
from fidesctl.cli.cli import (
    apply,
    delete,
    evaluate,
    generate_dataset,
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


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=fidesctl.__version__)
@click.option(
    "--config-path",
    "-f",
    "config_path",
    default="",
    help="Optional configuration file",
)
@click.pass_context
def cli(ctx: click.Context, config_path: str) -> None:
    """
    The parent group for the Fides CLI.
    Loads the config and passes it within the context.
    """
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = get_config(config_path)


cli.add_command(apply)
cli.add_command(delete)
cli.add_command(evaluate)
cli.add_command(generate_dataset)
cli.add_command(get)
cli.add_command(init_db)
cli.add_command(ls)
cli.add_command(parse)
cli.add_command(ping)
cli.add_command(reset_db)
cli.add_command(view_config)
cli.add_command(webserver)
