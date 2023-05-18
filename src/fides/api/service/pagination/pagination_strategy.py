from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

from requests import Response

from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.strategy import Strategy

if TYPE_CHECKING:
    from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration


class PaginationStrategy(Strategy):
    """Abstract base class for SaaS pagination strategies"""

    @abstractmethod
    def get_next_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        """Build request for next page of data"""

    def validate_request(self, request: Dict[str, Any]) -> None:
        """
        Accepts the raw SaaSRequest data and validates that the request
        has all the necessary information to use this pagination strategy.
        """
