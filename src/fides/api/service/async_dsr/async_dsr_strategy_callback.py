from typing import Any, Dict

from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.schemas.saas.async_polling_configuration import PollingResult
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient


class CallbackAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for callback async DSR requests.

    This strategy implements the abstract methods but they are not actively used
    since callback handling is done through webhook endpoints, not polling.
    """

    type = AsyncTaskType.callback

    def get_status_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> bool:
        """
        Callback strategies don't use status polling.
        Status updates come through webhook callbacks.
        """
        raise NotImplementedError(
            "Callback strategies don't use status polling - status comes via webhook"
        )

    def get_result_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> PollingResult:
        """
        Callback strategies don't use result polling.
        Results come through webhook callbacks.
        """
        raise NotImplementedError(
            "Callback strategies don't use result polling - results come via webhook"
        )
