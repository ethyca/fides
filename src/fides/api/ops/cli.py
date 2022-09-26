"""Sets up a simple fidesops CLI"""
import logging

import click

from fidesops.main import start_webserver
from fidesops.ops.tasks import start_worker

logger = logging.getLogger(__name__)


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


@cli.command()
@click.pass_context
def worker(ctx: click.Context) -> None:
    """
    Starts a Celery worker
    """
    logger.info("Running Celery worker from CLI...")
    start_worker()
