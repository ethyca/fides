"""Contains reusable utils for the CLI commands."""

import json
from datetime import datetime, timezone
from functools import update_wrapper
from importlib.metadata import version
from os import getenv
from platform import system
from typing import Any, Callable, Optional, Union

import requests
import rich_click as click
from fideslog.sdk.python.client import AnalyticsClient
from fideslog.sdk.python.event import AnalyticsEvent
from fideslog.sdk.python.exceptions import AnalyticsError
from fideslog.sdk.python.utils import (
    CONFIRMATION_COPY,
    EMAIL_PROMPT,
    FIDESCTL_CLI,
    OPT_OUT_COPY,
    ORGANIZATION_PROMPT,
    generate_client_id,
)
from requests import get, put

import fides
from fides.common.api.v1.urn_registry import REGISTRATION, V1_URL_PREFIX
from fides.common.utils import check_response, echo_green, echo_red
from fides.config import FidesConfig
from fides.config.credentials_settings import (
    get_config_aws_credentials,
    get_config_bigquery_credentials,
    get_config_database_credentials,
    get_config_okta_credentials,
)
from fides.config.helpers import get_config_from_file
from fides.config.utils import get_dev_mode
from fides.connectors.models import (
    AWSConfig,
    BigQueryConfig,
    DatabaseConfig,
    OktaConfig,
)
from fides.core import api as _api

APP = fides.__name__
PACKAGE = "ethyca-fides"
FIDES_ASCII_ART = """

███████╗██╗██████╗ ███████╗███████╗
██╔════╝██║██╔══██╗██╔════╝██╔════╝
█████╗  ██║██║  ██║█████╗  ███████╗
██╔══╝  ██║██║  ██║██╔══╝  ╚════██║
██║     ██║██████╔╝███████╗███████║
╚═╝     ╚═╝╚═════╝ ╚══════╝╚══════╝
"""


def check_server_health(server_url: str, verbose: bool = True) -> requests.Response:
    """Hit the '/health' endpoint and verify the server is available."""

    healthcheck_url = server_url + "/health"
    try:
        health_response = check_response(_api.ping(healthcheck_url))
    except requests.exceptions.ConnectionError:
        echo_red(
            f"Connection failed, webserver is unreachable at URL:\n{healthcheck_url}"
        )
        raise SystemExit(1)
    except Exception as e:
        echo_red(f"Failed to connect to the server at {healthcheck_url}: {e}")
        raise SystemExit(1)

    return health_response


def compare_application_versions(server_version: str, cli_version: str) -> bool:
    """Normalize and compare application versions."""
    normalize_version = lambda v: str(v).replace(".dirty", "", 1)
    return normalize_version(server_version) == normalize_version(cli_version)


def check_server(cli_version: str, server_url: str, quiet: bool = False) -> None:
    """Runs a health check and a version check against the server."""

    health_response = check_server_health(str(server_url) or "")
    if health_response.status_code == 429:
        # The server is ratelimiting us
        echo_red("Server ratelimit reached. Please wait one minute and try again.")
        raise SystemExit(1)
    if health_response.status_code != 200:
        echo_red(
            f"Server response: HTTP {health_response.status_code} - {health_response.text}"
        )
        raise SystemExit(1)

    if not health_response.json().get("version", False):
        echo_red(
            f"Server returned malformed response: {health_response.text}\nPlease check the server and config and try again."
        )
        raise SystemExit(1)

    server_version = health_response.json()["version"]
    if compare_application_versions(server_version, cli_version):
        if not quiet:
            echo_green(
                "Server is reachable and the client/server application versions match."
            )
    else:
        echo_red(
            f"Mismatched versions!\nServer Version: {server_version}\nCLI Version: {cli_version}"
        )


def is_user_registered(config: FidesConfig) -> bool:
    """
    Send a request to the API server, and determine if a registration is already present.
    """

    response = get(f"{config.cli.server_url}{V1_URL_PREFIX}{REGISTRATION}")
    return response.json()["opt_in"]


def register_user(config: FidesConfig, email: str, organization: str) -> None:
    """
    Create a new registration record in the database.
    """

    put(
        f"{config.cli.server_url}{V1_URL_PREFIX}{REGISTRATION}",
        json={
            "analytics_id": config.cli.analytics_id,
            "opt_in": True,
            "user_email": email,
            "user_organization": organization,
        },
    )


def request_analytics_consent(config: FidesConfig, opt_in: bool = False) -> FidesConfig:
    """
    Request the user's consent for analytics collection.

    This function should only be called when specifically wanting to ask
    for the user's consent, otherwise it will ask repeatedly for consent
    unless they've opted in.
    """

    analytics_env_var = getenv("FIDES__USER__ANALYTICS_OPT_OUT")
    if analytics_env_var and analytics_env_var.lower() != "false":
        return config

    if analytics_env_var and analytics_env_var.lower() == "true":
        opt_in = True

    # Otherwise, ask for consent
    print(OPT_OUT_COPY)
    if not opt_in:
        config.user.analytics_opt_out = not click.confirm(
            "Opt-in to anonymous usage analytics?"
        )
    else:
        config.user.analytics_opt_out = opt_in

    # If we've not opted out, attempt to register the user if they are
    # currently connected to a Fides server
    if not config.user.analytics_opt_out:
        server_url = str(config.cli.server_url) or ""
        try:
            check_server_health(server_url, verbose=False)
            should_attempt_registration = not is_user_registered(config)
        except SystemExit:
            should_attempt_registration = False

        if should_attempt_registration:
            email = input(EMAIL_PROMPT)
            organization = input(ORGANIZATION_PROMPT)
            if email and organization:
                register_user(config, email, organization)

        # Either way, thank the user for their opt-in for analytics!
        click.echo(CONFIRMATION_COPY)

    return config


def send_init_analytics(opt_out: bool, config_path: str, executed_at: datetime) -> None:
    """
    Create a new `AnalyticsClient` and send an `AnalyticsEvent` representing
    the execution of `fides init` by a user.
    """

    if opt_out is not False:
        return

    analytics_id = get_config_from_file(config_path, "cli", "analytics_id")

    try:
        client = AnalyticsClient(
            client_id=analytics_id or generate_client_id(FIDESCTL_CLI),
            developer_mode=get_dev_mode(),
            os=system(),
            product_name=APP + "-cli",
            production_version=version(PACKAGE),
        )

        event = AnalyticsEvent(
            "cli_command_executed",
            executed_at,
            command="fides init",
            docker=bool(getenv("RUNNING_IN_DOCKER") == "TRUE"),
            resource_counts=None,  # TODO: Figure out if it's possible to capture this
        )

        client.send(event)
    except AnalyticsError:
        pass  # cli analytics should fail silently


def with_server_health_check(func: Callable) -> Callable:
    """
    Click command decorator which can be added to enable server health check.
    Sends a request to the server's health endpoint to verify the server is available.
    """

    def wrapper_func(ctx: click.Context, *args, **kwargs) -> Any:  # type: ignore
        config = ctx.obj["CONFIG"]
        check_server_health(config.cli.server_url)
        return ctx.invoke(func, ctx, *args, **kwargs)

    return update_wrapper(wrapper_func, func)


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


def handle_database_credentials_options(
    fides_config: FidesConfig, connection_string: str, credentials_id: str
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
        actual_connection_string = (
            database_credentials.connection_string
            if database_credentials is not None
            else actual_connection_string
        )
    return actual_connection_string


def handle_okta_credentials_options(
    fides_config: FidesConfig, token: str, org_url: str, credentials_id: str
) -> Optional[OktaConfig]:
    """
    Handles the mutually exclusive okta connections options org-url/token and credentials-id.
    It is allowed to provide neither as there is support for environment variables
    """
    okta_config: Optional[OktaConfig] = None
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
    fides_config: FidesConfig,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
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
            aws_session_token=session_token,
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
    fides_config: FidesConfig,
    dataset: str,
    keyfile_path: str,
    credentials_id: str,
) -> BigQueryConfig:
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

    if not bigquery_config:
        raise click.UsageError("Illegal usage: No connection configuration provided")

    return bigquery_config


def _validate_credentials_id_exists(
    credentials_id: str,
    credentials_config: Optional[
        Union[AWSConfig, BigQueryConfig, DatabaseConfig, OktaConfig]
    ],
) -> None:
    if not credentials_config:
        raise click.UsageError(
            f"credentials-id {credentials_id} does not exist in fides config"
        )
