"""Contains reusable utils for the CLI commands."""

import json
import pprint
import sys
from datetime import datetime, timezone
from functools import update_wrapper
from importlib.metadata import version
from os import getenv
from platform import system
from typing import Any, Callable, Dict, Optional, Union

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
from fidesctl.api.ctl.routes.util import API_PREFIX
from fidesctl.ctl.connectors.models import AWSConfig, BigQueryConfig, OktaConfig
from fidesctl.ctl.core import api as _api
from fidesctl.ctl.core.config import FidesctlConfig
from fidesctl.ctl.core.config.credentials_settings import (
    get_config_aws_credentials,
    get_config_bigquery_credentials,
    get_config_database_credentials,
    get_config_okta_credentials,
)
from fidesctl.ctl.core.config.utils import get_config_from_file, update_config_file
from fidesctl.ctl.core.utils import check_response, echo_green, echo_red

FIDESCTL_ASCII_ART = """
███████╗██╗██████╗ ███████╗███████╗ ██████╗████████╗██╗     
██╔════╝██║██╔══██╗██╔════╝██╔════╝██╔════╝╚══██╔══╝██║     
█████╗  ██║██║  ██║█████╗  ███████╗██║        ██║   ██║     
██╔══╝  ██║██║  ██║██╔══╝  ╚════██║██║        ██║   ██║     
██║     ██║██████╔╝███████╗███████║╚██████╗   ██║   ███████╗
╚═╝     ╚═╝╚═════╝ ╚══════╝╚══════╝ ╚═════╝   ╚═╝   ╚══════╝                                                      
"""


def check_server(cli_version: str, server_url: str, quiet: bool = False) -> None:
    """Runs a health check and a version check against the server."""

    healthcheck_url = server_url + API_PREFIX + "/health"
    try:
        health_response = check_response(_api.ping(healthcheck_url))
    except requests.exceptions.ConnectionError:
        echo_red(
            f"Connection failed, webserver is unreachable at URL:\n{healthcheck_url}."
        )
        raise SystemExit(1)

    server_version = health_response.json()["version"]
    normalize_version = lambda v: str(v).replace(".dirty", "", 1)
    if normalize_version(server_version) == normalize_version(cli_version):
        if not quiet:
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
    click.secho(pprint.pformat(dict_object, indent=2, width=80, compact=True), fg=color)


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

    is_analytics_opt_out = ctx.obj["CONFIG"].user.analytics_opt_out
    is_analytics_opt_out_config_empty = get_config_from_file(
        config_path,
        "cli",
        "analytics_id",
    ) in ("", None)
    is_analytics_opt_out_env_var_set = getenv("FIDESCTL__CLI__ANALYTICS_ID")
    if (
        not is_analytics_opt_out
        and is_analytics_opt_out_config_empty
        and not is_analytics_opt_out_env_var_set
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


def print_divider(character: str = "-", character_length: int = 10) -> None:
    """
    Returns a consistent divider to print to the console for use within fidesctl

    Defaults to using a hyphen of length 10, however this can optionally be
    overridden as required.
    """
    print(character * character_length)


def handle_database_credentials_options(
    fides_config: FidesctlConfig, connection_string: str, credentials_id: str
) -> str:
    """
    Handles the mutually exclusive database connections options connetion-string and credentials-id.
    Raises errors if neither or both options are provided
    """
    actual_connection_string = connection_string
    if connection_string and credentials_id:
        raise click.UsageError(
            "Illegal usage: connection-string and credentials-id cannot be used together"
        )
    if not connection_string and not credentials_id:
        raise click.UsageError(
            "Illegal usage: connection-string or credentials-id are required"
        )
    if credentials_id:
        database_credentials = get_config_database_credentials(
            credentials_config=fides_config.credentials,
            credentials_id=credentials_id,
        )
        _validate_credentials_id_exists(credentials_id, database_credentials)
        actual_connection_string = database_credentials.connection_string
    return actual_connection_string


def handle_okta_credentials_options(
    fides_config: FidesctlConfig, token: str, org_url: str, credentials_id: str
) -> Optional[OktaConfig]:
    """
    Handles the mutually exclusive okta connections options org-url/token and credentials-id.
    It is allowed to provide neither as there is support for environment variables
    """
    okta_config = dict()
    if token or org_url:
        if not token or not org_url:
            raise click.UsageError(
                "Illegal usage: token and org-url must be used together"
            )
        if credentials_id:
            raise click.UsageError(
                "Illegal usage: token/org-url and credentials-id cannot be used together"
            )
        okta_config = OktaConfig(orgUrl=org_url, token=token)
    if credentials_id:
        okta_config = get_config_okta_credentials(
            credentials_config=fides_config.credentials,
            credentials_id=credentials_id,
        )
        _validate_credentials_id_exists(credentials_id, okta_config)
    return okta_config


def handle_aws_credentials_options(
    fides_config: FidesctlConfig,
    access_key_id: str,
    secret_access_key: str,
    region: str,
    credentials_id: str,
) -> Optional[AWSConfig]:
    """
    Handles the mutually exclusive aws connections options access-key/access-key-id/region
    and credentials-id. It is allowed to provide neither as there is support for environment
    variables.
    """
    aws_config = None
    if access_key_id or secret_access_key or region:
        if not access_key_id or not secret_access_key or not region:
            raise click.UsageError(
                "Illegal usage: access-key-id, secret_access_key and region must be used together"
            )
        if credentials_id:
            raise click.UsageError(
                "Illegal usage: access-key-id/secret_access_key/region and credentials-id cannot be used together"
            )
        aws_config = AWSConfig(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )
    if credentials_id:
        aws_config = get_config_aws_credentials(
            credentials_config=fides_config.credentials,
            credentials_id=credentials_id,
        )
        _validate_credentials_id_exists(credentials_id, aws_config)
    return aws_config


def handle_bigquery_config_options(
    fides_config: FidesctlConfig,
    dataset: str,
    keyfile_path: str,
    credentials_id: str,
) -> Optional[BigQueryConfig]:
    """
    Handles the connections options for passing a keyfile, dictionary, or credentials-id.
    """
    bigquery_config = None

    if keyfile_path and credentials_id:
        raise click.UsageError(
            "Illegal usage: keyfile-path and credentials-id cannot be used together"
        )
    if keyfile_path:
        with open(keyfile_path, "r", encoding="utf-8") as credential_file:
            bigquery_config = BigQueryConfig(
                **{
                    "dataset": dataset,
                    "keyfile_creds": json.load(credential_file),
                }
            )
    elif credentials_id:
        bigquery_config = get_config_bigquery_credentials(
            dataset=dataset,
            credentials_config=fides_config.credentials,
            credentials_id=credentials_id,
        )
        _validate_credentials_id_exists(credentials_id, bigquery_config)
    else:
        raise click.UsageError("Illegal usage: No connection configuration provided")
    return bigquery_config


def _validate_credentials_id_exists(
    credentials_id: str,
    credentials_config: Union[OktaConfig, BigQueryConfig, AWSConfig],
) -> None:
    if not credentials_config:
        raise click.UsageError(
            f"credentials-id {credentials_id} does not exist in fides config"
        )
