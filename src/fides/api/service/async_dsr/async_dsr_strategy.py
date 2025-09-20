from abc import abstractmethod
from typing import Any, Dict

from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.schemas.saas.async_polling_configuration import PollingResult
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.strategy import Strategy


class AsyncDSRStrategy(Strategy):
    """Abstract base class for async DSR strategies"""

    type: AsyncTaskType

    @abstractmethod
    def get_status_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> bool:
        """
        Execute status request and return completion status.

        Args:
            client: Authenticated SaaS client
            param_values: Parameter values including correlation_id
            secrets: SaaS connector secrets for authentication

        Returns:
            bool: True if job is complete, False if still processing
        """

    @abstractmethod
    def get_result_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> PollingResult:
        """
        Execute result request and return processed results.

        Args:
            client: Authenticated SaaS client
            param_values: Parameter values including correlation_id
            secrets: SaaS connector secrets for authentication

        Returns:
            PollingResult: Processed results in standardized container format
        """
