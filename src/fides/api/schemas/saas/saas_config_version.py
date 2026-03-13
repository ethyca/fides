from datetime import datetime
from typing import Optional

from fides.api.schemas.base_class import FidesSchema


class SaaSConfigVersionResponse(FidesSchema):
    """Summary of a stored SaaS integration version, used for list responses."""

    connector_type: str
    version: str
    is_custom: bool
    created_at: datetime


class SaaSConfigVersionDetailResponse(SaaSConfigVersionResponse):
    """Full detail for a single version, including config and dataset as raw dicts."""

    config: dict
    dataset: Optional[dict] = None
