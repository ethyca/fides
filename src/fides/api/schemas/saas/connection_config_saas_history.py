from datetime import datetime
from typing import Any, Dict, List, Optional

from fides.api.schemas.base_class import FidesSchema


class ConnectionConfigSaaSHistoryResponse(FidesSchema):
    """Summary of a per-connection SaaS config snapshot, used for list responses."""

    id: str
    version: str
    created_at: datetime


class ConnectionConfigSaaSHistoryDetailResponse(ConnectionConfigSaaSHistoryResponse):
    """Full detail for a single snapshot, including config and dataset."""

    config: Dict[str, Any]
    dataset: Optional[List[Dict[str, Any]]] = None
