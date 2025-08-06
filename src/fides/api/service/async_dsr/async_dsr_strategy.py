from requests import Response

from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.strategy import Strategy

if TYPE_CHECKING:
    from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration

class AsyncDSRStrategy(Strategy):
    """Abstract base class for async DSR strategies"""

    @abstractmethod
    def start_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        """Build request to start the async DSR process"""

    def get_status_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        """Build request to get the status of the async DSR process"""

    def get_result_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        """Build request to get the result of the async DSR process"""
