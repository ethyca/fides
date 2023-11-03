"""Contains reusable utils for the CLI commands."""

import json
from typing import Optional, Union

import requests
import rich_click as click

import fides
from fides.common.utils import check_response, echo_green, echo_red
from fides.config import FidesConfig
from fides.config.credentials_settings import (
    get_config_aws_credentials,
    get_config_bigquery_credentials,
    get_config_database_credentials,
    get_config_okta_credentials,
)
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
        if verbose:
            echo_red(
                f"Connection failed, webserver is unreachable at URL:\n{healthcheck_url}"
            )
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
