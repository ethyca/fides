"""Contains the groups and setup for the CLI."""
import click

import fidesctl
from fidesctl.cli.cli import (
    apply,
    create,
    delete,
    dry_evaluate,
    evaluate,
    generate_dataset,
    get,
    show,
    ping,
    update,
    view_config,
)
from fidesctl.core.config import get_config

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
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


@cli.command()
def version() -> None:
    """
    Get the current Fidesctl version.
    """
    click.echo(fidesctl.__version__)


cli.add_command(apply)
cli.add_command(create)
cli.add_command(delete)
cli.add_command(dry_evaluate)
cli.add_command(evaluate)
cli.add_command(generate_dataset)
cli.add_command(get)
cli.add_command(show)
cli.add_command(ping)
cli.add_command(update)
cli.add_command(view_config)
