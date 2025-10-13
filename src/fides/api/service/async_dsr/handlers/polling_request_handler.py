"""
Pure HTTP utility for executing polling requests.

This module contains low-level HTTP request execution for async DSR polling,
with no business logic or orchestration dependencies.
"""

from typing import Any, Dict, Optional

from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.saas_util import map_param_values


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

        response: Response = client.send(prepared_status_request)

        if not response.ok:
            raise PrivacyRequestError(
                f"Status request failed with status code {response.status_code}: {response.text}"
            )

        return response

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

        response: Response = client.send(prepared_result_request)

        if not response.ok:
            raise PrivacyRequestError(
                f"Result request failed with status code {response.status_code}: {response.text}"
            )

        return response
