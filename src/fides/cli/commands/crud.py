"""Contains all of the CRUD-type CLI commands for fides."""
import rich_click as click
import yaml

from fides.cli.options import fides_key_argument, resource_type_argument
from fides.cli.utils import handle_cli_response, print_divider, with_analytics
from fides.core import api as _api
from fides.core.api_helpers import get_server_resource, list_server_resources
from fides.core.utils import echo_green, echo_red


@click.command()
@click.pass_context
@resource_type_argument
@fides_key_argument
@with_analytics
def delete(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    Delete an object from the server.
    """
    config = ctx.obj["CONFIG"]
    handle_cli_response(
        _api.delete(
            url=config.cli.server_url,
            resource_type=resource_type,
            resource_id=fides_key,
            headers=config.user.auth_header,
        ),
        verbose=False,
    )
    echo_green(
        f"{resource_type.capitalize()} with fides_key '{fides_key}' successfully deleted."
    )


@click.command(name="get")
@click.pass_context
@resource_type_argument
@fides_key_argument
@with_analytics
def get_resource(ctx: click.Context, resource_type: str, fides_key: str) -> None:
    """
    View an object from the server.
    """
    config = ctx.obj["CONFIG"]
    resource = get_server_resource(
        url=config.cli.server_url,
        resource_type=resource_type,
        resource_key=fides_key,
        headers=config.user.auth_header,
        raw=True,
    )
    print_divider()
    echo_green(yaml.dump({resource_type: [resource]}))


@click.command(name="ls")
@click.pass_context
@resource_type_argument
@with_analytics
@click.option(
    "--verbose", "-v", is_flag=True, help="Displays the entire object list as YAML."
)
def list_resources(ctx: click.Context, verbose: bool, resource_type: str) -> None:
    """
    View all objects of a single type from the server.
    """
    config = ctx.obj["CONFIG"]
    resources = list_server_resources(
        url=config.cli.server_url,
        resource_type=resource_type,
        headers=config.user.auth_header,
        exclude_keys=[],
        raw=True,
    )
    print_divider()
    if verbose:
        echo_green(yaml.dump({resource_type: resources}))
    else:
        if resources:
            sorted_fides_keys = sorted(
                {resource["fides_key"] for resource in resources if resource}
            )
            formatted_fides_keys = "\n  ".join(sorted_fides_keys)
            echo_green(f"{resource_type.capitalize()} list:\n  {formatted_fides_keys}")
        else:
            echo_red(f"No {resource_type.capitalize()} resources found!")
