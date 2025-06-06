from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import ConfigDict, Field

from fides.api.schemas.base_class import FidesSchema


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
    in_processing = "in_processing"
    complete = "complete"
    error = "error"
    retrying = "retrying"
    paused = "paused"
    awaiting_input = "awaiting_input"


class ManualTaskLogCreate(FidesSchema):
    """Schema for creating a manual task log entry."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="ID of the task")
    status: ManualTaskLogStatus = Field(..., description="Log status")
    message: Optional[str] = Field(None, description="Log message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional details")
    config_id: Optional[str] = Field(None, description="Configuration ID")
    instance_id: Optional[str] = Field(None, description="Instance ID")


class ManualTaskLogResponse(FidesSchema):
    """Schema for manual task log response."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Log ID")
    task_id: str = Field(..., description="Task ID")
    status: ManualTaskLogStatus = Field(..., description="Log status")
    message: Optional[str] = Field(None, description="Log message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional details")
    config_id: Optional[str] = Field(None, description="Configuration ID")
    instance_id: Optional[str] = Field(None, description="Instance ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
