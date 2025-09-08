from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy


class CallbackAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for callback async DSR requests.

    This strategy has no methods since the callback is handled by the callback endpoint
    we still require the strategy to be defined to notify that the request is awaiting async processing
    and follows the AsyncDSRStrategy interface.
    """

    name = "callback"

    def __init__(self) -> None:
        pass
