from datetime import datetime
from typing import List, Optional

from fides.api.schemas.base_class import FidesSchema


class MonitorTaskInProgressResponse(FidesSchema):
    """
    Response schema for in-progress monitor tasks in the Action Center.
    """

    id: str
    created_at: datetime
    updated_at: datetime
    monitor_config_id: Optional[str]
    monitor_name: Optional[str]
    action_type: str  # MonitorTaskType
    status: str
    message: Optional[str]
    staged_resource_urns: Optional[List[str]]
    connection_type: Optional[str]
    connection_name: Optional[str]


class MonitorTaskInProgressFilter(FidesSchema):
    """
    Filter parameters for monitor task queries.
    """

    monitor_name: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    size: int = 50
