from pydantic import BaseModel, Field
from typing import List


class Task(BaseModel):
    """Pydantic Model for a Task."""

    __tablename__ = "tasks"

    privacy_request_id: str = Field(
        description="The PrivacyRequest that this task belongs to."
    )
    downstream: List[str] = Field(
        default=[], description="The task(s) that rely on this task's completion"
    )
    upstream: List[str] = Field(
        default=[], description="The task(s) that this task relies on."
    )
    result_data: str = Field(
        default="", description="The data retrieved from the target_field."
    )
    target_field: str = Field(description="The field that is targeted by this task.")
    connection_config: str = Field(
        description="The key of the ConnectionConfig used to access this target_field."
    )
    labels: List[str] = Field(default=[], description="Additional metadata.")
