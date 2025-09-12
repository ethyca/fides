from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.service.strategy import Strategy


class AsyncDSRStrategy(Strategy):
    """Abstract base class for async DSR strategies"""

    type: AsyncTaskType
