"""Contains reusable utils for the CLI commands."""

import json
import sys
from datetime import datetime, timezone
from functools import update_wrapper
from importlib.metadata import version
from os import getenv
from platform import system
from typing import Any, Callable, Dict

import click
import requests
from fideslog.sdk.python.client import AnalyticsClient
from fideslog.sdk.python.event import AnalyticsEvent
from fideslog.sdk.python.exceptions import AnalyticsError
from fideslog.sdk.python.utils import (
    FIDESCTL_CLI,
    OPT_OUT_COPY,
    OPT_OUT_PROMPT,
    generate_client_id,
)

import fidesctl
from fidesctl.core import api as _api
from fidesctl.core.config.utils import get_config_from_file, update_config_file
from fidesctl.core.utils import check_response, echo_green, echo_red


def check_server(cli_version: str, server_url: str) -> None:
    """Runs a health check and a version check against the server."""

    healthcheck_url = server_url + "/health"
    try:
        health_response = check_response(_api.ping(healthcheck_url))
    except requests.exceptions.ConnectionError:
        echo_red(
            f"Connection failed, webserver is unreachable at URL:\n{healthcheck_url}."
        )
        raise SystemExit(1)

    server_version = health_response.json()["version"]
    if str(server_version) == str(cli_version):
        echo_green(
            "Server is reachable and the client/server application versions match."
        )
    else:
        echo_red(
            f"Mismatched versions!\nServer Version: {server_version}\nCLI Version: {cli_version}"
        )


def pretty_echo(dict_object: Dict, color: str = "white") -> None:
    """
    Given a dict-like object and a color, pretty click echo it.
    """
    click.secho(json.dumps(dict_object, indent=2), fg=color)


def handle_cli_response(
    response: requests.Response, verbose: bool = True
) -> requests.Response:
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
        click.echo(OPT_OUT_COPY)
        ctx.obj["CONFIG"].user.analytics_opt_out = bool(
            input(OPT_OUT_PROMPT).lower() == "n"
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


def send_init_analytics(opt_out: bool, config_path: str, executed_at: datetime) -> None:
    """
    Create a new `AnalyticsClient` and send an `AnalyticsEvent` representing
    the execution of `fidesctl init` by a user.
    """

    if opt_out is not False:
        return

    analytics_id = get_config_from_file(config_path, "cli", "analytics_id")
    app_name = fidesctl.__name__

    try:
        client = AnalyticsClient(
            client_id=analytics_id or generate_client_id(FIDESCTL_CLI),
            developer_mode=bool(getenv("FIDESCTL_TEST_MODE") == "True"),
            os=system(),
            product_name=app_name + "-cli",
            production_version=version(app_name),
        )

        event = AnalyticsEvent(
            "cli_command_executed",
            executed_at,
            command="fidesctl init",
            docker=bool(getenv("RUNNING_IN_DOCKER") == "TRUE"),
            resource_counts=None,  # TODO: Figure out if it's possible to capture this
        )

        client.send(event)
    except AnalyticsError:
        pass  # cli analytics should fail silently


def with_analytics(func: Callable) -> Callable:
    """
    Click command decorator which can be added to enable publishing anaytics.
    Sends an `AnalyticsEvent` with details about the executed command,
    as long as the CLI has not been configured to opt out of analytics.

    :param func: function to be wrapped by decorator
    """

    def wrapper_func(ctx: click.Context, *args, **kwargs) -> Any:  # type: ignore
        command = " ".join(filter(None, [ctx.info_name, ctx.invoked_subcommand]))
        error = None
        executed_at = datetime.now(timezone.utc)
        status_code = 0

        try:
            return ctx.invoke(func, ctx, *args, **kwargs)
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
                    ctx.meta["ANALYTICS_CLIENT"].send(event)
                except AnalyticsError:
                    pass  # cli analytics should fail silently

    return update_wrapper(wrapper_func, func)
