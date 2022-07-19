"""Contains the db group of the commands for Fidesctl."""
import click

from fidesctl.cli.options import yes_flag
from fidesctl.cli.utils import handle_cli_response, with_analytics
from fidesctl.ctl.core import api as _api
from fidesctl.ctl.core.utils import echo_red


@click.group(name="db")
@click.pass_context
def database(ctx: click.Context) -> None:
    """
    Database utility commands
    """


@database.command(name="init")
@click.pass_context
@with_analytics
def db_init(ctx: click.Context) -> None:
    """
    Initialize the Fidesctl database.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.db_action(
            server_url=config.cli.server_url,
            action="init",
        )
    )


@database.command(name="reset")
@click.pass_context
@yes_flag
@with_analytics
def db_reset(ctx: click.Context, yes: bool) -> None:
    """
    Wipes all user-created data and resets the database back to its freshly initialized state.
    """
    config = ctx.obj["CONFIG"]
    if yes:
        are_you_sure = "y"
    else:
        echo_red(
            "This will drop all data from the Fides database and reload the default taxonomy!"
        )
        are_you_sure = input("Are you sure [y/n]? ")

    if are_you_sure.lower() == "y":
        handle_cli_response(
            _api.db_action(
                server_url=config.cli.server_url,
                action="reset",
            )
        )
    else:
        print("Aborting!")
