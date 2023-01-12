"""Module that adds interactions with okta"""
import ast
from functools import update_wrapper
from typing import Any, Callable, List, Optional

from fideslang.models import System, SystemMetadata
from okta.client import Client as OktaClient
from okta.exceptions import OktaAPIException
from okta.models import Application as OktaApplication

from fides.connectors.models import (
    ConnectorAuthFailureException,
    ConnectorFailureException,
    OktaConfig,
)


def get_okta_client(okta_config: Optional[OktaConfig]) -> OktaClient:
    """
    Returns an Okta client for the given okta config. Authentication can
    also be handled through environment variables that the okta python sdk support.

    Enabled raiseException config to facilitate exception handling
    """
    config_dict = okta_config.dict() if okta_config else {}
    config_dict["raiseException"] = True
    okta_client = OktaClient(config_dict)
    return okta_client


def handle_common_okta_errors(func: Callable) -> Callable:
    """
    Function decorator which handles common errors for okta calls.
    Classifies exceptions based on error codes returned by the client.
    For a full list of error codes see https://developer.okta.com/docs/reference/error-codes/
    """

    async def wrapper_func(*args, **kwargs) -> Any:  # type: ignore
        try:
            return await func(*args, **kwargs)
        except OktaAPIException as error:
            error_json = ast.literal_eval(str(error))
            # E0000004 - Authentication exception
            # E0000011 - Invalid token exception
            if error_json["errorCode"] in ["E0000004", "E0000011"]:
                raise ConnectorAuthFailureException(error_json["errorSummary"])
            raise ConnectorFailureException(error_json["errorSummary"])

    return update_wrapper(wrapper_func, func)


@handle_common_okta_errors
async def validate_credentials(okta_config: Optional[OktaConfig]) -> None:
    """
    Calls the list_applications api with a page limit of 1 to validate
    okta credentials.
    """
    client = get_okta_client(okta_config=okta_config)
    query_parameters = {"limit": "1"}
    await client.list_applications(query_parameters)


@handle_common_okta_errors
async def list_okta_applications(okta_client: OktaClient) -> List[OktaApplication]:
    """
    Returns a list of Okta applications. Iterates through each page returned by
    the client.
    """
    applications = []
    current_applications, resp, _ = await okta_client.list_applications()
    while True:
        applications.extend(current_applications)
        if resp.has_next():
            current_applications, _ = await resp.next()
        else:
            break
    return applications


def create_okta_systems(
    okta_applications: List[OktaApplication], organization_key: str
) -> List[System]:
    """
    Returns a list of system objects given a list of Okta applications
    """
    systems = [
        System(
            fides_key=application.id,
            name=application.name,
            fidesctl_meta=SystemMetadata(
                resource_id=application.id,
            ),
            description=f"Fides Generated Description for Okta Application: {application.label}",
            system_type="okta_application",
            organization_fides_key=organization_key,
            privacy_declarations=[],
        )
        for application in okta_applications
        if application.status and application.status == "ACTIVE"
    ]
    return systems
