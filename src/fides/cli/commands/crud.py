"""Contains all of the CRUD-type CLI commands for fides."""
import click
import yaml

from fides.cli.options import fides_key_argument, resource_type_argument
from fides.cli.utils import handle_cli_response, print_divider, with_analytics
from fides.core import api as _api
from fides.core.api_helpers import get_server_resource, list_server_resources
from fides.core.utils import echo_green


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


@click.command(name="get")
@click.pass_context
@resource_type_argument
@fides_key_argument
@with_analytics
def get_resource(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    View a resource from the server as a YAML object.
    """
    config = ctx.obj["CONFIG"]
    resource = get_server_resource(
        url=config.cli.server_url,
        resource_type=resource_type,
        resource_key=fides_key,
        headers=config.user.request_headers,
        raw=True,
    )
    print_divider()
    echo_green(yaml.dump({resource_type: [resource]}))


@click.command(name="ls")
@click.pass_context
@resource_type_argument
@with_analytics
def list_resources(ctx: click.Context, resource_type: str) -> None:
    """
    Get a list of all resources of this type from the server and display them as YAML.
    """
    config = ctx.obj["CONFIG"]
    resources = list_server_resources(
        url=config.cli.server_url,
        resource_type=resource_type,
        headers=config.user.request_headers,
        exclude_keys=[],
        raw=True,
    )
    print_divider()
    echo_green(yaml.dump({resource_type: resources}))
