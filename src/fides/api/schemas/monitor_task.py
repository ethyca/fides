from datetime import datetime
from typing import List, Optional

from fides.api.schemas.base_class import FidesSchema


class MonitorTaskInProgressResponse(FidesSchema):
    """
    Response schema for in-progress monitor tasks in the Action Center.
    """

    id: str
    monitor_name: str
    task_type: str  # classification or promotion
    last_updated: datetime
    status: str
    staged_resource_urns: Optional[List[str]] = None
    connection_type: Optional[str] = None
    monitor_config_id: str
    message: Optional[str] = None


class MonitorTaskInProgressFilter(FidesSchema):
    """
    Filter parameters for monitor task queries.
    """

    monitor_name: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    size: int = 50
