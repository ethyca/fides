"""Contains the view group of the commands for fides."""

import click

from fides.cli.utils import pretty_echo, with_analytics


@click.group(name="view")
@click.pass_context
def view(ctx: click.Context) -> None:
    """
    View various resources types.
    """


@view.command(name="config")
@click.pass_context
@click.argument("section", default="", type=str)
@click.option(
    "--exclude-unset",
    is_flag=True,
    help="Only print configuration values explicitly set by the user.",
)
@with_analytics
def view_config(
    ctx: click.Context, section: str = "", exclude_unset: bool = False
) -> None:
    """
    Prints the fides configuration values.

    To only view a specific section of the config,
    supply the section name as an argument.
    """
    config = ctx.obj["CONFIG"]
    config_dict = config.dict(exclude_unset=exclude_unset)
    if section:
        config_dict = config_dict[section]
    pretty_echo(dict_object=config_dict, color="green")
