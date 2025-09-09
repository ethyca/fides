from typing import Any, Dict, List, Optional, Union
from io import BytesIO

import pydash
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.strategy_configuration import (
    PollingAsyncAccessDownloadConfiguration,
    SupportedDownloadType,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling_base import PollingAsyncDSRBaseStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import map_param_values
from fides.api.models.privacy_request.request_task import RequestTask


class PollingAsyncAccessDownloadStrategy(PollingAsyncDSRBaseStrategy):
    """
    Strategy for polling async access requests with file download results.
    Strategy not fully implemented. Pending full file support.
    """

    name = "polling_access_download"
    configuration_model = PollingAsyncAccessDownloadConfiguration

    def __init__(self, configuration: PollingAsyncAccessDownloadConfiguration):
        super().__init__(configuration)
        self.download_type = configuration.download_type

    def get_result_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],

    ) -> Union[str, bytes, List[Row]]:
        """Execute result request and return download URL or file content."""

        prepared_result_request = map_param_values(
            "result", "polling request", self.result_request, param_values
        )

        response: Response = client.send(prepared_result_request)

        if response.ok:
            if self.download_type == SupportedDownloadType.link:
                return self._process_download_link(response)
            elif self.download_type == SupportedDownloadType.file:
                return self._process_direct_file(response)
            else:
                raise PrivacyRequestError(f"Unsupported download type: {self.download_type}")

        raise PrivacyRequestError(
            f"Result request failed with status code {response.status_code}"
        )

    def _process_download_link(self, response: Response) -> str:
        """Process response containing a download link."""
        if self.result_path:
            download_url = pydash.get(response.json(), self.result_path)
        else:
            # Assume the entire response is the download URL
            download_url = response.text.strip()

        if not download_url:
            raise PrivacyRequestError("No download URL found in response")

        return download_url

    def _process_direct_file(self, response: Response) -> bytes:
        """Process response containing direct file content."""
        # For direct file downloads, return the raw content
        return response.content
