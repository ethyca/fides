"""Contains reusable utils for the CLI commands."""

import json
import sys
from asyncio import run
from datetime import datetime, timezone
from os import getenv
from typing import Any, Callable, Dict

import click
from fideslog.sdk.python.event import AnalyticsEvent
from fideslog.sdk.python.exceptions import AnalyticsException
from fideslog.sdk.python.utils import OPT_OUT_COPY
from requests import Response

from fidesctl.core.config.utils import get_config_from_file, update_config_file
from fidesctl.core.utils import echo_red


def pretty_echo(dict_object: Dict, color: str = "white") -> None:
    """
    Given a dict-like object and a color, pretty click echo it.
    """
    click.secho(json.dumps(dict_object, indent=2), fg=color)


def handle_cli_response(response: Response, verbose: bool = True) -> Response:
    """Viewable CLI response"""
    if response.status_code >= 200 and response.status_code <= 299:
        if verbose:
            pretty_echo(response.json(), "green")
    else:
        try:
            pretty_echo(response.json(), "red")
        except json.JSONDecodeError:
            click.secho(response.text, fg="red")
        finally:
            sys.exit(1)
    return response


def check_and_update_analytics_config(ctx: click.Context, config_path: str) -> None:
    """
    Ensure the analytics-related config is present. If not,
    prompt the user to opt-in to analytics and/or update the
    config file with their preferences.
    """

    config_updates: Dict[str, Dict] = {}
    if ctx.obj["CONFIG"].user.analytics_opt_out is None:
        ctx.obj["CONFIG"].user.analytics_opt_out = bool(
            input(OPT_OUT_COPY).lower() == "n"
        )

        config_updates.update(
            user={"analytics_opt_out": ctx.obj["CONFIG"].user.analytics_opt_out}
        )

    if (
        ctx.obj["CONFIG"].user.analytics_opt_out is False
        and get_config_from_file(
            config_path,
            "cli",
            "analytics_id",
        )
        in ("", None)
    ):
        config_updates.update(cli={"analytics_id": ctx.obj["CONFIG"].cli.analytics_id})

    if len(config_updates) > 0:
        try:
            update_config_file(config_updates, config_path)
        except FileNotFoundError as err:
            echo_red(f"Failed to update config file ({config_path}): {err.strerror}")
            click.echo("Run 'fidesctl init' to create a configuration file.")


def with_analytics(ctx: click.Context, command_handler: Callable, **kwargs: Dict) -> Any:  # type: ignore
    """
    Send an `AnalyticsEvent` with details about the executed command,
    as long as the CLI has not been configured to opt out of analytics.

    :param ctx: The command's execution `click.Context` object
    :param command_handler: The handler function defining the evaluation logic for the analyzed command
    :param **kwargs: Any arguments that must be passed to the `command_handler` function
    """

    command = " ".join(filter(None, [ctx.info_name, ctx.invoked_subcommand]))
    error = None
    executed_at = datetime.now(timezone.utc)
    status_code = 0

    try:
        return command_handler(**kwargs)
    except Exception as err:
        error = type(err).__name__
        status_code = 1
        raise err
    finally:
        if (
            ctx.obj["CONFIG"].user.analytics_opt_out is False
        ):  # requires explicit opt-in
            event = AnalyticsEvent(
                "cli_command_executed",
                executed_at,
                command=command,
                docker=bool(getenv("RUNNING_IN_DOCKER") == "TRUE"),
                error=error,
                flags=None,  # TODO: Figure out if it's possible to capture this
                resource_counts=None,  # TODO: Figure out if it's possible to capture this
                status_code=status_code,
            )

            try:
                run(ctx.meta["ANALYTICS_CLIENT"].send(event))
            except AnalyticsException:
                pass  # cli analytics should fail silently
