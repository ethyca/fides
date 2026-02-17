"""
Pure HTTP utility for executing polling requests.

This module contains low-level HTTP request execution for async DSR polling,
with no business logic or orchestration dependencies.
"""

from typing import Any, Dict, List, Optional, Union

from loguru import logger
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
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

    @staticmethod
    def _should_ignore_error(
        status_code: int,
        ignore_errors: Optional[Union[bool, List[int]]],
    ) -> bool:
        """
        Determine if an error response should be ignored based on the ignore_errors config.

        Mirrors AuthenticatedClient._should_ignore_error:
        - False: do not ignore any errors
        - True: ignore all errors
        - List[int]: ignore only if status_code is in the list
        """
        if ignore_errors is True:
            return True
        if isinstance(ignore_errors, list):
            return status_code in ignore_errors
        return False

    @staticmethod
    def _send_and_handle_errors(
        client: AuthenticatedClient,
        prepared_request: SaaSRequestParams,
        ignore_errors: Optional[Union[bool, List[int]]],
        request_label: str,
    ) -> Response:
        """
        Send a request and handle error responses, respecting ignore_errors configuration.

        Mirrors the sync path convention from SaaSConnector._handle_errored_response:
        when ignore_errors is configured and the response status code matches, the error
        is logged and the response is returned without raising.
        """
        response: Response = client.send(prepared_request, ignore_errors)

        if not response.ok and PollingRequestHandler._should_ignore_error(
            response.status_code, ignore_errors
        ):
            logger.info(
                "Ignoring errored response with status code {} for {} as configured.",
                response.status_code,
                request_label,
            )
            return response

        if not response.ok:
            raise PrivacyRequestError(
                f"{request_label} failed with status code {response.status_code}: {response.text}"
            )

        return response

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

        return self._send_and_handle_errors(
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

        return self._send_and_handle_errors(
            client,
            prepared_result_request,
            self.result_request.ignore_errors,
            "Result request",
        )