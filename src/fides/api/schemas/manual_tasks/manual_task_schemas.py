from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import ConfigDict, Field

from fides.api.schemas.base_class import FidesSchema


class ManualTaskExecutionTiming(str, Enum):
    """Enum for when a manual task should be executed in the privacy request DAG."""

    pre_execution = "pre_execution"  # Execute before the main DAG
    post_execution = "post_execution"  # Execute after the main DAG
    parallel = "parallel"  # Execute in parallel with the main DAG


# Constants for manual task collection names
MANUAL_TASK_COLLECTIONS = {
    ManualTaskExecutionTiming.pre_execution: "pre_execution",
    ManualTaskExecutionTiming.post_execution: "post_execution",
}


class ManualTaskType(str, Enum):
    """Enum for manual task types."""

    privacy_request = "privacy_request"
    # Add more task types as needed


class ManualTaskParentEntityType(str, Enum):
    """Enum for manual task parent entity types."""

    connection_config = (
        "connection_config"  # used for access and erasure privacy requests
    )
    # Add more parent entity types as needed


class ManualTaskEntityType(str, Enum):
    """Enum for manual task entity types."""

    privacy_request = "privacy_request"
    # Add more entity types as needed


class ManualTaskReferenceType(str, Enum):
    """Enum for manual task reference types."""

    privacy_request = "privacy_request"
    connection_config = "connection_config"
    manual_task_config = "manual_task_config"
    assigned_user = "assigned_user"  # Reference to the user assigned to the task
    # Add more reference types as needed


class ManualTaskLogStatus(str, Enum):
    """Enum for manual task log status."""

    created = "created"
    updated = "updated"
    in_progress = "in_progress"
    complete = "complete"
    error = "error"
    retrying = "retrying"
    paused = "paused"
    awaiting_input = "awaiting_input"


class ManualTaskLogCreate(FidesSchema):
    """Schema for creating a manual task log entry."""

    model_config = ConfigDict(extra="forbid")

    task_id: Annotated[str, Field(..., description="ID of the task")]
    status: Annotated[ManualTaskLogStatus, Field(..., description="Log status")]
    message: Annotated[Optional[str], Field(None, description="Log message")]
    details: Annotated[
        Optional[dict[str, Any]], Field(None, description="Additional details")
    ]
    config_id: Annotated[Optional[str], Field(None, description="Configuration ID")]
    instance_id: Annotated[Optional[str], Field(None, description="Instance ID")]


class ManualTaskLogResponse(FidesSchema):
    """Schema for manual task log response."""

    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(..., description="Log ID")]
    task_id: Annotated[str, Field(..., description="Task ID")]
    status: Annotated[ManualTaskLogStatus, Field(..., description="Log status")]
    message: Annotated[Optional[str], Field(None, description="Log message")]
    details: Annotated[
        Optional[dict[str, Any]], Field(None, description="Additional details")
    ]
    config_id: Annotated[Optional[str], Field(None, description="Configuration ID")]
    instance_id: Annotated[Optional[str], Field(None, description="Instance ID")]
    created_at: Annotated[datetime, Field(..., description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(..., description="Last update timestamp")]


class ManualTaskBase(FidesSchema):
    """Base schema for manual task models."""

    name: str = Field(..., description="The name of the manual task")
    description: Optional[str] = Field(
        None, description="The description of the manual task"
    )
    task_type: ManualTaskType = Field(..., description="The type of manual task")
    parent_entity_id: str = Field(..., description="The ID of the parent entity")
    parent_entity_type: ManualTaskParentEntityType = Field(
        ..., description="The type of parent entity"
    )


class ManualTaskCreate(ManualTaskBase):
    """Schema for creating a manual task."""

    pass  # pylint: disable=unnecessary-pass


class ManualTaskUpdate(FidesSchema):
    """Schema for updating a manual task."""

    name: Optional[str] = Field(None, description="The name of the manual task")
    description: Optional[str] = Field(
        None, description="The description of the manual task"
    )
    task_type: Optional[ManualTaskType] = Field(
        None, description="The type of manual task"
    )


class ManualTaskResponse(ManualTaskBase):
    """Schema for manual task responses."""

    id: str = Field(..., description="The ID of the manual task")
    created_at: str = Field(..., description="When the manual task was created")
    updated_at: str = Field(..., description="When the manual task was last updated")


class ManualTaskReference(FidesSchema):
    """Schema for manual task references."""

    id: str = Field(..., description="The ID of the manual task")
    name: str = Field(..., description="The name of the manual task")
    reference_type: ManualTaskReferenceType = Field(
        ..., description="The type of reference"
    )


class ManualTaskListResponse(FidesSchema):
    """Schema for manual task list responses."""

    items: list[ManualTaskResponse] = Field(..., description="The list of manual tasks")
    total: int = Field(..., description="The total number of manual tasks")
    page: int = Field(..., description="The current page number")
    size: int = Field(..., description="The page size")
    pages: int = Field(..., description="The total number of pages")
