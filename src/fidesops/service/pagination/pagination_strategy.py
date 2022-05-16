from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from requests import Response

from fidesops.schemas.saas.shared_schemas import SaaSRequestParams
from fidesops.schemas.saas.strategy_configuration import StrategyConfiguration


class PaginationStrategy(ABC):
    """Abstract base class for SaaS pagination strategies"""

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Returns strategy name"""

    @abstractmethod
    def get_next_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: str,
    ) -> Optional[SaaSRequestParams]:
        """Build request for next page of data"""

    @staticmethod
    @abstractmethod
    def get_configuration_model() -> StrategyConfiguration:
        """Used to get the configuration model to configure the strategy"""

    def validate_request(self, request: Dict[str, Any]) -> None:
        """
        Accepts the raw SaaSRequest data and validates that the request
        has all the necessary information to use this pagination strategy.
        """
