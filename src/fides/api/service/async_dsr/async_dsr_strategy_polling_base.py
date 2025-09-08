from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import pydash
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.strategy_configuration import (
    PollingAsyncDSRBaseConfiguration,
    IdSource,
)
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import map_param_values


class PollingAsyncDSRBaseStrategy(AsyncDSRStrategy, ABC):
    """
    Base strategy for polling async DSR requests.
    """

    def __init__(self, configuration: PollingAsyncDSRBaseConfiguration):
        self.status_request = configuration.status_request
        self.status_path = configuration.status_path
        self.status_completed_value = configuration.status_completed_value
        self.result_request = configuration.result_request
        self.result_path = configuration.result_path
        self.request_id_config = configuration.request_id_config

    def extract_request_id(
        self,
        response: Response,
        param_values: Dict[str, Any]
    ) -> Optional[str]:
        """Extract request ID from response based on configuration."""
        if not self.request_id_config:
            return None

        config = self.request_id_config

        if config.id_source == IdSource.path:
            return pydash.get(response.json(), config.id_path)
        elif config.id_source == IdSource.generated:
            # For generated IDs, we should have stored it in param_values
            return param_values.get("request_id")
        raise PrivacyRequestError(
            f"Request ID source {config.id_source} not supported"
        )

    def get_status_request(
        self,
        client: AuthenticatedClient,
        secrets: Dict[str, Any],
        identity_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> bool:
        """Execute status request and return completion status."""
        param_values = secrets.copy()
        param_values.update(identity_data)

        if request_id:
            param_values["request_id"] = request_id

        prepared_status_request = map_param_values(
            "status", "polling request", self.status_request, param_values
        )

        response: Response = client.send(prepared_status_request)

        if response.ok:
            status_path_value = pydash.get(response.json(), self.status_path)
            return self._evaluate_status_value(status_path_value)

        raise PrivacyRequestError(
            f"Status request failed with status code {response.status_code}"
        )

    def _evaluate_status_value(self, status_path_value: Any) -> bool:
        """Evaluate if status indicates completion."""
        # Boolean direct check
        if isinstance(status_path_value, bool):
            return status_path_value

        # String comparison with completed value
        if isinstance(status_path_value, str):
            if self.status_completed_value:
                return status_path_value == self.status_completed_value
            # If no completed value specified, any non-empty string is considered complete
            return bool(status_path_value)

        # List check (first element)
        if isinstance(status_path_value, list) and status_path_value:
            first_element = status_path_value[0]
            if self.status_completed_value:
                return first_element == self.status_completed_value
            return bool(first_element)

        # Unexpected type
        raise PrivacyRequestError(
            f"Status request returned an unexpected value: {status_path_value}"
        )


    def get_result_request(
        self,
        client: AuthenticatedClient,
        secrets: Dict[str, Any],
        identity_data: Dict[str, Any],
    ) -> List[Row]:
        """Build request to get the result of the async DSR process"""
        param_values = secrets.copy()
        param_values.update(identity_data)
        prepared_result_request = map_param_values(
            "result",
            "polling request",
            self.result_request,
            param_values,  # type: ignore
        )
        response: Response = client.send(prepared_result_request)
        if response.ok:
            result = pydash.get(response.json(), self.result_path)
            return result

        raise PrivacyRequestError(
            f"Result request failed with status code {response.status_code}"
        )
