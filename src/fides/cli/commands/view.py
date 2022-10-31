"""Contains the view group of the commands for fides."""

import click
from toml import dumps as toml_dumps

from fides.cli.utils import print_divider, with_analytics


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
    Prints the configuration values being used.
    """
    config = ctx.obj["CONFIG"]
    config_dict = config.dict(exclude_unset=exclude_unset)
    if section:
        config_dict = config_dict[section]

    print_divider()
    print(toml_dumps(config_dict))
