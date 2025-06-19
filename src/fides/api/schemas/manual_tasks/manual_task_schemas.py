from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import ConfigDict, Field

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.manual_tasks.manual_task_status import StatusType


class ManualTaskExecutionTiming(str, Enum):
    """Enum for when a manual task should be executed in the privacy request DAG."""

    pre_execution = "pre_execution"  # Execute before the main DAG
    post_execution = "post_execution"  # Execute after the main DAG
    parallel = "parallel"  # Execute in parallel with the main DAG


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


class ManualTaskResponse(FidesSchema):
    """Schema for manual task response."""

    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(..., description="Task ID")]
    parent_entity_id: Annotated[str, Field(..., description="Parent entity ID")]
    parent_entity_type: Annotated[
        ManualTaskParentEntityType, Field(..., description="Parent entity type")
    ]
    status: Annotated[StatusType, Field(..., description="Task status")]
    created_at: Annotated[datetime, Field(..., description="Creation timestamp")]
    updated_at: Annotated[datetime, Field(..., description="Last update timestamp")]


class ManualTaskCreate(FidesSchema):
    """Schema for creating a manual task."""

    model_config = ConfigDict(extra="forbid")

    parent_entity_id: Annotated[str, Field(..., description="Parent entity ID")]
    parent_entity_type: Annotated[
        ManualTaskParentEntityType, Field(..., description="Parent entity type")
    ]


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
