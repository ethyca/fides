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
from requests import Response


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
        error = type(err)
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
