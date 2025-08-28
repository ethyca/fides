from typing import Any, Dict, List

import pydash
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.strategy_configuration import PollingAsyncDSRConfiguration
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import map_param_values


class PollingAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for polling async DSR requests.
    """

    name = "polling"
    configuration_model = PollingAsyncDSRConfiguration

    def __init__(self, configuration: PollingAsyncDSRConfiguration):
        self.status_request = configuration.status_request
        self.status_path = configuration.status_path
        self.status_completed_value = configuration.status_completed_value
        self.result_request = configuration.result_request
        self.result_path = configuration.result_path

    def get_status_request(
        self,
        client: AuthenticatedClient,
        secrets: Dict[str, Any],
        identity_data: Dict[str, Any],
    ) -> bool:
        """Executes the status requests, and move forward if its true"""
        param_values = secrets.copy()
        param_values.update(identity_data)
        prepared_status_request = map_param_values(
            "status", "polling request", self.status_request, param_values
        )

        response: Response = client.send(prepared_status_request)

        if response.ok:
            status_path_value = pydash.get(response.json(), self.status_path)
            # If the status path value is a boolean, return it
            if isinstance(status_path_value, bool):
                return status_path_value

            # if the status path is a string, check if its the expected string value
            if isinstance(status_path_value, str):
                if status_path_value == self.status_completed_value:
                    return True

                return False

            # if the status path is a list, check if the first element is the expected string value
            if isinstance(status_path_value, list):
                if status_path_value[0] == self.status_completed_value:
                    return True

                return False
            # And if we cant recognize the type, raise an error
            raise PrivacyRequestError(
                f"Status request returned an unexpected value: {status_path_value}"
            )

        raise PrivacyRequestError(
            f"Status request failed with status code {response.status_code}"
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
