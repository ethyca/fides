"""
Pure HTTP utility for executing polling requests.

This module contains low-level HTTP request execution for async DSR polling,
with no business logic or orchestration dependencies.
"""

from typing import Any, Dict, List, Optional, Type, Union

from requests import Response

from fides.api.common_exceptions import ClientUnsuccessfulException, PrivacyRequestError
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.util.saas_util import map_param_values
from fides.connectors.saas.authenticated_client import AuthenticatedClient


def send_and_handle_errors(
    client: AuthenticatedClient,
    prepared_request: SaaSRequestParams,
    ignore_errors: Optional[Union[bool, List[int]]],
    request_label: str,
    exception_cls: Type[Exception] = PrivacyRequestError,
) -> Response:
    """
    Send a request and handle error responses, respecting ignore_errors configuration.

    Delegates ignore_errors to client.send() so that ignored responses are returned
    directly (preserving retry behavior for non-ignored errors). Non-ignored failures
    are wrapped in exception_cls (PrivacyRequestError by default; e.g. FidesopsException
    for strategy callers).
    """
    try:
        return client.send(prepared_request, ignore_errors)
    except ClientUnsuccessfulException as exc:
        response = exc.response
        if response is None:
            raise exception_cls(f"{request_label} failed with no response")
        raise exception_cls(
            f"{request_label} failed with status code {response.status_code}: {response.text}"
        )


class PollingRequestHandler:
    """
    Pure HTTP utility for executing polling requests.

    Handles status checks and result retrieval with no business logic dependencies.
    """

    def __init__(
        self,
        status_request: PollingStatusRequest,
        result_request: Optional[PollingResultRequest] = None,
    ):
        self.status_request = status_request
        self.result_request = result_request

    def get_status_response(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
    ) -> Response:
        """Execute HTTP status request and return raw response."""
        if not self.status_request:
            raise PrivacyRequestError(
                "status_request is not configured in the async polling configuration"
            )

        prepared_status_request = map_param_values(
            action="status",
            context="polling request",
            current_request=self.status_request,
            param_values=param_values,
        )

        return send_and_handle_errors(
            client,
            prepared_status_request,
            self.status_request.ignore_errors,
            "Status request",
        )

    def get_result_response(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
    ) -> Response:
        """Execute HTTP result request and return raw response."""
        if not self.result_request:
            raise PrivacyRequestError(
                "result_request is not configured in the async polling configuration"
            )

        prepared_result_request = map_param_values(
            action="result",
            context="polling request",
            current_request=self.result_request,
            param_values=param_values,
        )

        return send_and_handle_errors(
            client,
            prepared_result_request,
            self.result_request.ignore_errors,
            "Result request",
        )
