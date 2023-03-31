"""Contains the db group of the commands for fides."""
import rich_click as click

from fides.cli.options import yes_flag
from fides.cli.utils import handle_cli_response, with_analytics
from fides.core import api as _api
from fides.core.utils import echo_red


@click.group(name="db")
@click.pass_context
def database(ctx: click.Context) -> None:
    """
    Run actions against the application database.
    """


@database.command(name="init")
@click.pass_context
@with_analytics
def db_init(ctx: click.Context) -> None:
    """
    Initialize the Fides database.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.db_action(
            server_url=config.cli.server_url,
            headers=config.user.auth_header,
            action="init",
        )
    )


@database.command(name="reset")
@click.pass_context
@yes_flag
@with_analytics
def db_reset(ctx: click.Context, yes: bool) -> None:
    """
    Reset the database back to its initial state.
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
                headers=config.user.auth_header,
                action="reset",
            )
        )
    else:
        print("Aborting!")
