"""Contains all of the ungrouped CLI commands for fides."""

from datetime import datetime, timezone
from typing import Optional

import rich_click as click
import yaml

import fides
from fides.cli.options import (
    dry_flag,
    fides_key_argument,
    manifests_dir_argument,
    resource_type_argument,
    verbose_flag,
)
from fides.cli.utils import (
    FIDES_ASCII_ART,
    check_server,
    send_init_analytics,
    with_analytics,
)
from fides.common.utils import (
    echo_green,
    echo_red,
    handle_cli_response,
    pretty_echo,
    print_divider,
)
from fides.config.create import create_and_update_config_file
from fides.core import api as _api
from fides.core import audit as _audit
from fides.core import evaluate as _evaluate
from fides.core import parse as _parse
from fides.core import pull as _pull
from fides.core import push as _push
from fides.core.api_helpers import get_server_resource, list_server_resources
from fides.core.utils import git_is_dirty


@click.command()  # type: ignore
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


@click.command(name="get")  # type: ignore
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
    )
    print_divider()
    echo_green(yaml.dump({resource_type: [resource]}))


@click.command(name="ls")  # type: ignore
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
    )
    print_divider()
    if verbose:
        echo_green(yaml.dump({resource_type: resources}))
    else:
        if resources:
            sorted_fides_keys = sorted(
                {resource["fides_key"] for resource in resources if resource}  # type: ignore[index]
            )
            formatted_fides_keys = "\n  ".join(sorted_fides_keys)
            echo_green(
                f"List of resources of type '{resource_type}':\n  {formatted_fides_keys}"
            )
        else:
            echo_red(f"No {resource_type.capitalize()} resources found!")


@click.command()  # type: ignore
@click.pass_context
@click.argument("fides_dir", default=".", type=click.Path(exists=True))
@click.option(
    "--opt-in", is_flag=True, help="Automatically opt-in to anonymous usage analytics."
)
def init(ctx: click.Context, fides_dir: str, opt_in: bool) -> None:
    """
    Initializes a Fides instance by creating the default directory and
    configuration file if not present.
    """

    executed_at = datetime.now(timezone.utc)
    config = ctx.obj["CONFIG"]

    click.echo(FIDES_ASCII_ART)
    click.echo("Initializing fides...")

    config, config_path = create_and_update_config_file(
        config, fides_dir, opt_in=opt_in
    )

    print_divider()

    send_init_analytics(config.user.analytics_opt_out, config_path, executed_at)
    echo_green("fides initialization complete.")


@click.command()
@click.pass_context
@with_analytics
def status(ctx: click.Context) -> None:
    """
    Check Fides server availability.
    """
    config = ctx.obj["CONFIG"]
    cli_version = fides.__version__
    server_url = config.cli.server_url
    click.echo("Getting server status...")
    check_server(
        cli_version=cli_version,
        server_url=server_url,
    )


@click.command()  # type: ignore
@click.pass_context
@click.option("--port", "-p", type=int, default=8080)
def webserver(ctx: click.Context, port: int = 8080) -> None:
    """
    Start the Fides webserver.

    _Requires Redis and Postgres to be configured and running_
    """
    # This has to be here to avoid a circular dependency
    from fides.api.main import start_webserver

    start_webserver(port=port)


@click.command()
@click.pass_context
@with_analytics
def worker(ctx: click.Context) -> None:
    """
    Start a Celery worker for the Fides webserver.
    """
    # This has to be here to avoid a circular dependency
    from fides.api.worker import start_worker

    start_worker()


@click.command()  # type: ignore
@click.pass_context
@dry_flag
@click.option(
    "--diff",
    is_flag=True,
    help="Print any diffs between the local & server objects",
)
@manifests_dir_argument
@with_analytics
def push(ctx: click.Context, dry: bool, diff: bool, manifests_dir: str) -> None:
    """
    Parse local manifest files and upload them to the server.
    """

    config = ctx.obj["CONFIG"]
    taxonomy = _parse.parse(manifests_dir)
    _push.push(
        url=config.cli.server_url,
        taxonomy=taxonomy,
        headers=config.user.auth_header,
        dry=dry,
        diff=diff,
    )


@click.command()  # type: ignore
@click.pass_context
@manifests_dir_argument
@click.option(
    "--fides-key",
    "-k",
    help="The fides_key of a specific policy to evaluate.",
    default="",
)
@click.option(
    "-m",
    "--message",
    help="Describe the context of this evaluation.",
)
@click.option(
    "-a",
    "--audit",
    is_flag=True,
    help="Validate that the objects in this evaluation produce a valid data map.",
)
@click.option(
    "--dry",
    is_flag=True,
    help="Do not upload objects or results to the Fides webserver.",
)
@with_analytics
def evaluate(
    ctx: click.Context,
    manifests_dir: str,
    fides_key: str,
    message: str,
    audit: bool,
    dry: bool,
) -> None:
    """
    Evaluate System-level Privacy Declarations against Organization-level Policy Rules.
    """

    config = ctx.obj["CONFIG"]

    if config.cli.local_mode:
        dry = True
    else:
        taxonomy = _parse.parse(manifests_dir)
        _push.push(
            url=config.cli.server_url,
            taxonomy=taxonomy,
            headers=config.user.auth_header,
            dry=dry,
        )

    _evaluate.evaluate(
        url=config.cli.server_url,
        headers=config.user.auth_header,
        manifests_dir=manifests_dir,
        policy_fides_key=fides_key,
        message=message,
        local=config.cli.local_mode,
        dry=dry,
    )

    if audit:
        taxonomy = _parse.parse(manifests_dir)
        print_divider()
        pretty_echo("Auditing Organization Resource Compliance")
        _audit.audit_organizations(
            url=config.cli.server_url,
            headers=config.user.auth_header,
            include_keys=[
                organization.fides_key for organization in taxonomy.organization
            ],
        )
        print_divider()
        pretty_echo("Auditing System Resource Compliance")
        _audit.audit_systems(
            url=config.cli.server_url,
            headers=config.user.auth_header,
            include_keys=[system.fides_key for system in taxonomy.system or []],
        )


@click.command()
@click.pass_context
@manifests_dir_argument
@verbose_flag
@with_analytics
def parse(ctx: click.Context, manifests_dir: str, verbose: bool = False) -> None:
    """
    Parse all Fides objects located in the supplied directory.
    """
    taxonomy = _parse.parse(manifests_dir=manifests_dir)
    if verbose:
        pretty_echo(taxonomy.model_dump(mode="json"), color="green")


@click.command()  # type: ignore
@click.pass_context
@manifests_dir_argument
@click.option(
    "--all-resources",
    "-a",
    default=None,
    help="Pulls all locally missing resources from the server into this file.",
)
@with_analytics
def pull(ctx: click.Context, manifests_dir: str, all_resources: Optional[str]) -> None:
    """
    Update local resource files based on the state of the objects on the server.
    """

    # Make the resources that are pulled configurable
    config = ctx.obj["CONFIG"]
    # Do this to validate the manifests since they won't get parsed during the pull process
    _parse.parse(manifests_dir)
    if git_is_dirty(manifests_dir):
        echo_red(
            f"There are unstaged changes in your manifest directory: '{manifests_dir}' \nAborting pull!"
        )
        raise SystemExit(1)
    _pull.pull(
        url=config.cli.server_url,
        manifests_dir=manifests_dir,
        headers=config.user.auth_header,
        all_resources_file=all_resources,
    )
