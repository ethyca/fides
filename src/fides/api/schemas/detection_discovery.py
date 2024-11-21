from datetime import datetime
from typing import List

from pydantic import BaseModel


class StagedResourceResponse(BaseModel):
    """Response schema for a list of staged resources"""

    urn: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    diff_status: str
    child_diff_statuses: List[str]
    hidden: bool
