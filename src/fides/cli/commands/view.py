"""Contains the view group of the commands for Fidesctl."""

import click

from fidesctl.cli.utils import pretty_echo, with_analytics


@click.group(name="view")
@click.pass_context
def view(ctx: click.Context) -> None:
    """
    View various resources types.
    """


@view.command(name="config")
@click.pass_context
@click.option(
    "--exclude-unset",
    is_flag=True,
    help="Only print configuration values explicitly set by the user.",
)
@with_analytics
def view_config(ctx: click.Context, exclude_unset: bool = False) -> None:
    """
    Prints the fidesctl configuration values.
    """
    config = ctx.obj["CONFIG"]
    config_dict = config.dict(exclude_unset=exclude_unset)
    pretty_echo(dict_object=config_dict, color="green")
