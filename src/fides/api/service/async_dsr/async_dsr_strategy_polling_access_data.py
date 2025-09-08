from typing import Any, Dict, List, Optional
import csv
import io

import pydash
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.strategy_configuration import (
    PollingAsyncDSRAccessDataConfiguration,
    SupportedDataType,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling_base import PollingAsyncDSRBaseStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import map_param_values


class PollingAsyncDSRAccessDataStrategy(PollingAsyncDSRBaseStrategy):
    """
    Strategy for polling async access requests with direct data results.
    """

    name = "polling_access_data"
    configuration_model = PollingAsyncDSRAccessDataConfiguration

    def __init__(self, configuration: PollingAsyncDSRAccessDataConfiguration):
        super().__init__(configuration)
        self.result_path = configuration.result_path
        self.data_type = configuration.data_type

    def get_result_request(
        self,
        client: AuthenticatedClient,
        secrets: Dict[str, Any],
        identity_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> List[Row]:
        """Execute result request and return parsed data."""
        param_values = secrets.copy()
        param_values.update(identity_data)

        if request_id:
            param_values["request_id"] = request_id

        prepared_result_request = map_param_values(
            "result", "polling request", self.result_request, param_values
        )

        response: Response = client.send(prepared_result_request)

        if response.ok:
            if self.data_type == SupportedDataType.json:
                return self._process_json_response(response)
            elif self.data_type == SupportedDataType.csv:
                return self._process_csv_response(response)
            else:
                raise PrivacyRequestError(f"Unsupported data type: {self.data_type}")

        raise PrivacyRequestError(
            f"Result request failed with status code {response.status_code}"
        )

    def _process_json_response(self, response: Response) -> List[Row]:
        """Process JSON response data."""
        result = pydash.get(response.json(), self.result_path)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        else:
            raise PrivacyRequestError(
                f"Expected list or dict at path '{self.result_path}', got {type(result)}"
            )

    def _process_csv_response(self, response: Response) -> List[Row]:
        """Process CSV response data."""
        # Get CSV data from result path or direct response
        if self.result_path:
            csv_data = pydash.get(response.json(), self.result_path)
        else:
            csv_data = response.text

        # Parse CSV into list of dictionaries
        reader = csv.DictReader(io.StringIO(csv_data))
        return [dict(row) for row in reader]
