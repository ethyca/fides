from typing import Any, Dict

import pydash
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.schemas.saas.async_polling_configuration import (
    PollingAsyncDSRConfiguration,
    PollingResult,
)
from fides.api.service.async_dsr.handlers.polling_result_handler import (
    PollingResponseProcessor,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)
from fides.api.util.saas_util import map_param_values


class PollingAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Unified strategy for polling async DSR requests.
    Works for both access and erasure operations.
    """

    type = AsyncTaskType.polling
    configuration_model = PollingAsyncDSRConfiguration

    def __init__(self, configuration: PollingAsyncDSRConfiguration):
        self.status_request = configuration.status_request
        self.result_request = configuration.result_request

    def get_status_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> bool:
        """Execute status request with override support and return completion status."""

        # Check for request override first
        if self.status_request.request_override:
            # Get and execute override function
            override_function = SaaSRequestOverrideFactory.get_override(
                self.status_request.request_override, SaaSRequestType.POLLING_STATUS
            )

            return override_function(
                client=client,
                param_values=param_values,
                request_config=self.status_request,
                secrets=secrets,
            )

        # Standard status checking logic
        prepared_status_request = map_param_values(
            "status", "polling request", self.status_request, param_values
        )

        response: Response = client.send(prepared_status_request)

        if response.ok:
            status_path_value = pydash.get(
                response.json(), self.status_request.status_path
            )
            return self._evaluate_status_value(status_path_value)

        raise PrivacyRequestError(
            f"Status request failed with status code {response.status_code}: {response.text}"
        )

    def get_result_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> PollingResult:
        """Execute result request with override support and return smart-parsed results."""

        # Check for request override first
        if self.result_request.request_override:
            # Get and execute override function
            override_function = SaaSRequestOverrideFactory.get_override(
                self.result_request.request_override, SaaSRequestType.POLLING_RESULT
            )

            return override_function(
                client=client,
                param_values=param_values,
                request_config=self.result_request,
                secrets=secrets,
            )

        # Standard result processing logic
        prepared_result_request = map_param_values(
            "result", "polling request", self.result_request, param_values
        )

        response: Response = client.send(prepared_result_request)

        if not response.ok:
            raise PrivacyRequestError(
                f"Result request failed with status code {response.status_code}: {response.text}"
            )

        # Process response with smart data type inference
        return PollingResponseProcessor.process_response(
            response,
            prepared_result_request.path or "",
            self.result_request.result_path,
        )

    def _evaluate_status_value(self, status_path_value: Any) -> bool:
        """Evaluate if status indicates completion."""

        # Boolean direct check
        if isinstance(status_path_value, bool):
            return status_path_value

        # Direct comparison with completed value
        if status_path_value == self.status_request.status_completed_value:
            return True

        # String comparison
        if isinstance(status_path_value, str):
            # If no completed value specified, any non-empty string is considered complete
            if self.status_request.status_completed_value is None:
                return bool(status_path_value)
            return status_path_value == str(self.status_request.status_completed_value)

        # List check (first element)
        if isinstance(status_path_value, list) and status_path_value:
            first_element = status_path_value[0]
            if self.status_request.status_completed_value is None:
                return bool(first_element)
            return first_element == self.status_request.status_completed_value

        # Numeric comparison
        if isinstance(status_path_value, (int, float)):
            if isinstance(self.status_request.status_completed_value, (int, float)):
                return status_path_value == self.status_request.status_completed_value
            return bool(status_path_value)

        # Default to False for unexpected types
        return False
