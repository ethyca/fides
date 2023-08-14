"""Contains the view group of the commands for fides."""

import rich_click as click
from toml import dumps

from fides.cli.utils import with_analytics
from fides.common.utils import echo_red, print_divider
from fides.core.utils import get_credentials_path, read_credentials_file


@click.group(name="view")
@click.pass_context
def view(ctx: click.Context) -> None:
    """
    View various resources types.
    """


@view.command(name="config")  # type: ignore
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
    Prints the configuration values being used for this command-line instance.

    _Note: To see the configuration values being used by the webserver, `GET` the `/api/v1/config` endpoint._
    """
    config = ctx.obj["CONFIG"]
    config_dict = config.dict(exclude_unset=exclude_unset)
    if section:
        config_dict = config_dict[section]

    print_divider()
    print(dumps(config_dict))


@view.command(name="credentials")
@click.pass_context
@with_analytics
def view_credentials(ctx: click.Context) -> None:
    """
    Prints the credentials file.
    """
    credentials_path = get_credentials_path()
    try:
        credentials = read_credentials_file(credentials_path)
    except FileNotFoundError:
        echo_red(f"No credentials file found at path: {credentials_path}")
        raise SystemExit(1)

    print_divider()
    print(dumps(credentials.dict()))
