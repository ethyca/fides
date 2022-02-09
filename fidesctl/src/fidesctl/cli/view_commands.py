"""Contains the view group of the commands for Fidesctl."""
import click

from fidesctl.cli.utils import (
    pretty_echo,
)


@click.group(name="view")
@click.pass_context
def view(ctx: click.Context) -> None:
    """
    View configuration values within fidesctl
    """


@view.command(name="config")
@click.pass_context
def view_config(ctx: click.Context) -> None:
    """
    Prints the current fidesctl configuration values.
    """
    config = ctx.obj["CONFIG"]
    pretty_echo(config.dict(), color="green")
