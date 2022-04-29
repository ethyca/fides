"""Contains all of the CRUD-type CLI commands for Fidesctl."""

import click

from fidesctl.cli.options import fides_key_argument, resource_type_argument
from fidesctl.cli.utils import handle_cli_response, with_analytics
from fidesctl.core import api as _api


@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
@with_analytics
def delete(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    Delete a resource on the server.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.delete(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_id=fides_key,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
@with_analytics
def get(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    View a resource from the server as a JSON object.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.get(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_id=fides_key,
            headers=config.user.request_headers,
        )
    )


@click.command()
@click.pass_context
@resource_type_argument
@with_analytics
def ls(ctx: click.Context, resource_type: str) -> None:  # pylint: disable=invalid-name
    """
    Get a list of all resources of this type from the server and display them as JSON.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.ls(
            url=config.cli.server_url,
            resource_type=resource_type,
            headers=config.user.request_headers,
        )
    )
