from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from requests import PreparedRequest, Response
from requests.exceptions import (  # pylint: disable=redefined-builtin
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    SSLError,
    TooManyRedirects,
)

from fides.api.schemas.policy import ActionType
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.service.connectors.saas_connector import SaaSConnector


class LoggerContextKeys(Enum):
    privacy_request_id = "privacy_request_id"
    error_group = "error_group"
    error_details = "error_details"


class ErrorGroup(Enum):
    """A collection of user-friendly error labels to be used in contextualized logs."""

    network_error = "Network/protocol error"
    authentication_error = "Authentication error"
    client_error = "Client-side error"
    server_error = "Server-side error"


def saas_connector_details(
    connector: "SaaSConnector",
    action_type: Optional[ActionType] = None,
) -> Dict[str, Any]:
    """Maps the system and connection info details. Includes the collection and privacy request ID if available."""

    details = {
        "system_key": (
            connector.configuration.system.fides_key
            if connector.configuration.system
            else None
        ),
        "connection_key": connector.configuration.key,
    }
    if action_type:
        details["action_type"] = action_type.value
    if connector.current_collection_name:
        details["collection"] = connector.current_collection_name
    if connector.current_privacy_request:
        details[LoggerContextKeys.privacy_request_id.value] = (
            connector.current_privacy_request.id
        )
    return details


def request_details(
    prepared_request: PreparedRequest,
    response: Optional[Response] = None,
    ignore_error: bool = False,
) -> Dict[str, Any]:
    """Maps the request details and includes response details when "dev mode" is enabled."""

    details: Dict[str, Any] = {
        "method": prepared_request.method,
        "url": prepared_request.url,
    }
    if CONFIG.dev_mode and prepared_request.body is not None:
        details["body"] = prepared_request.body

    if response is not None:
        if CONFIG.dev_mode and response.content:
            details["response"] = response.content.decode("utf-8")

        details["status_code"] = response.status_code

        # assign error group only if error should not be ignored
        if not ignore_error:
            if response.status_code in [401, 403]:
                details[LoggerContextKeys.error_group.value] = (
                    ErrorGroup.authentication_error.value
                )
            elif 400 <= response.status_code < 500:
                details[LoggerContextKeys.error_group.value] = (
                    ErrorGroup.client_error.value
                )
            elif 500 <= response.status_code:
                details[LoggerContextKeys.error_group.value] = (
                    ErrorGroup.server_error.value
                )
    return details


def connection_exception_details(exception: Exception, url: str) -> Dict[str, Any]:
    """Maps select connection exceptions to user-friendly error details."""

    details = {
        LoggerContextKeys.error_group.value: ErrorGroup.network_error.value,
        LoggerContextKeys.error_details.value: f"Unknown exception connecting to {url}.",
    }
    if isinstance(exception, ConnectTimeout):
        details[LoggerContextKeys.error_details.value] = (
            f"Timeout occurred connecting to {url}."
        )
    elif isinstance(exception, ReadTimeout):
        details[LoggerContextKeys.error_details.value] = (
            f"Timeout occurred waiting for a response from {url}."
        )
    elif isinstance(exception, SSLError):
        details[LoggerContextKeys.error_details.value] = (
            f"SSL exception occurred connecting to {url}."
        )
    elif isinstance(exception, TooManyRedirects):
        details[LoggerContextKeys.error_details.value] = (
            f"Too many redirects occurred connecting to {url}."
        )
    elif isinstance(exception, ConnectionError):
        details[LoggerContextKeys.error_details.value] = f"Unable to connect to {url}."
    return details
