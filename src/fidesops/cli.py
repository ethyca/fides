"""Sets up a simple fidesops CLI"""
import click

from fidesops.main import start_webserver


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """fidesops CLI"""
    ctx.ensure_object(dict)


@cli.command()
@click.pass_context
def webserver(ctx: click.Context) -> None:
    """
    Runs any pending DB migrations and starts the webserver.
    """
    start_webserver()
