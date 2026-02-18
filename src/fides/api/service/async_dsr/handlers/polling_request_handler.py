"""
Pure HTTP utility for executing polling requests.

This module contains low-level HTTP request execution for async DSR polling,
with no business logic or orchestration dependencies.
"""

from typing import Any, Dict, Optional, Type, Union

from loguru import logger
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.saas_util import map_param_values, should_ignore_error


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
    def _send_and_handle_errors(
        client: AuthenticatedClient,
        prepared_request: SaaSRequestParams,
        ignore_errors: Optional[Union[bool, list]],
        request_label: str,
        exception_cls: Type[Exception] = PrivacyRequestError,
    ) -> Response:
        """
        Send a request and handle error responses, respecting ignore_errors configuration.

        When ignore_errors is configured and the response status code matches, the error
        is logged and the response is returned without raising. Otherwise raises
        exception_cls (PrivacyRequestError by default; e.g. FidesopsException for strategy callers).
        """
        response: Response = client.send(prepared_request, ignore_errors)

        if not response.ok and should_ignore_error(response.status_code, ignore_errors):
            logger.info(
                "Ignoring errored response with status code {} for {} as configured.",
                response.status_code,
                request_label,
            )
            return response

        if not response.ok:
            raise exception_cls(
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
