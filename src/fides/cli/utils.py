"""Contains reusable utils for the CLI commands."""

import json
from functools import update_wrapper
from typing import Any, Callable, Optional, Union

import requests
import rich_click as click

from fides.cli.core import api as _api
from fides.common.utils import FIDES_ASCII_ART as FIDES_ASCII_ART
from fides.common.utils import check_response, echo_green, echo_red
from fides.config import FidesConfig
from fides.config.credentials_settings import (
    get_config_aws_credentials,
    get_config_bigquery_credentials,
    get_config_database_credentials,
    get_config_okta_credentials,
)
from fides.config.schemas.credentials import (
    AWSConfig,
    BigQueryConfig,
    DatabaseConfig,
    OktaConfig,
)
from fides.config.utils import get_config_from_file, get_dev_mode


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
    fides_config: FidesConfig,
    org_url: str,
    client_id: str,
    private_key: str,
    credentials_id: str,
) -> Optional[OktaConfig]:
    """
    Handles the mutually exclusive okta connections options org-url/client-id/private-key and credentials-id.
    It is allowed to provide neither as there is support for environment variables
    """
    okta_config: Optional[OktaConfig] = None
    if client_id or private_key or org_url:
        if not client_id or not private_key or not org_url:
            raise click.UsageError(
                "Illegal usage: org-url, client-id, and private-key must be used together"
            )
        if credentials_id:
            raise click.UsageError(
                "Illegal usage: org-url/client-id/private-key and credentials-id cannot be used together"
            )
        okta_config = OktaConfig(
            org_url=org_url, client_id=client_id, private_key=private_key
        )
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
