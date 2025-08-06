from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy

class PollingAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for polling async DSR requests.
    """
    def start_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        pass

    def get_status_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        pass

    def get_result_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        pass
