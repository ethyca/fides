from datetime import datetime
from enum import Enum as EnumType
from typing import Any, Optional, List
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.manual_tasks.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskSubmission,
    ManualTaskType,
    ManualTaskConfigurationType,
    ManualTaskInstance,
)


def get_privacy_request_tasks(
    db: Session, task_type: Optional[ManualTaskType] = None
) -> List[ManualTask]:
    """Get all privacy request tasks.

    Args:
        db: Database session
        task_type: Optional task type to filter by
    """
    query = db.query(ManualTask).filter(
        ManualTask.task_type == ManualTaskType.privacy_request
    )

    if task_type:
        query = query.filter(ManualTask.task_type == task_type)

    return query.all()


def get_enabled_privacy_request_tasks(
    db: Session, task_type: Optional[ManualTaskType] = None
) -> List[ManualTask]:
    """Get all enabled privacy request tasks.

    Args:
        db: Database session
        task_type: Optional task type to filter by
    """
    query = db.query(ManualTask).filter(
        ManualTask.task_type == ManualTaskType.privacy_request,
        ManualTask.parent_entity_type == "connection_config",
        ConnectionConfig.disabled.is_(False),
    )

    if task_type:
        query = query.filter(ManualTask.task_type == task_type)

    return query.all()


def get_privacy_request_task_configs(task: ManualTask) -> List[ManualTaskConfig]:
    """Get all privacy request task configurations for a task."""
    return [
        config for config in task.configs
        if config.config_type in [
            ManualTaskConfigurationType.access_privacy_request,
            ManualTaskConfigurationType.erasure_privacy_request,
        ]
    ]


def get_privacy_request_task_fields(config: ManualTaskConfig) -> List[ManualTaskConfigField]:
    """Get all privacy request task fields for a configuration."""
    return [
        field for field in config.fields
        if hasattr(field, "dsr_package_label") and field.dsr_package_label is not None
    ]


def get_privacy_request_task_submissions(task: ManualTask) -> List[ManualTaskSubmission]:
    """Get all privacy request task submissions for a task."""
    return task.submissions


def get_privacy_request_task_instances(task: ManualTask) -> List[ManualTaskInstance]:
    """Get all privacy request task instances for a task."""
    return task.get_entity_instances(entity_type="privacy_request")


def get_privacy_request_task_instance(
    task: ManualTask, privacy_request_id: str
) -> Optional[ManualTaskInstance]:
    """Get the task instance for a specific privacy request.

    Args:
        task: The task to get the instance for
        privacy_request_id: ID of the privacy request
    """
    return task.get_instance_for_entity(
        entity_id=privacy_request_id,
        entity_type="privacy_request"
    )


def get_privacy_request_task_parent_entity(task: ManualTask, db: Session) -> Optional[Any]:
    """Get the parent entity associated with this privacy request task.

    For privacy request tasks, this will be either a ConnectionConfig or a PrivacyRequest.
    """
    if task.parent_entity_type == "connection_config":
        return db.query(ConnectionConfig).filter(
            ConnectionConfig.id == task.parent_entity_id
        ).first()
    elif task.parent_entity_type == "privacy_request":
        return db.query(PrivacyRequest).filter(
            PrivacyRequest.id == task.parent_entity_id
        ).first()
    return None


def get_field_definitions_for_privacy_request(config: ManualTaskConfig) -> dict[str, Any]:
    """Get field definitions based on the privacy request configuration type."""
    field_definitions = {}
    for field in config.fields or []:
        if config.config_type == ManualTaskConfigurationType.access_privacy_request:
            # Include all fields for access, regardless of type
            if "dsr_package_label" in field:
                field_definitions[field["dsr_package_label"]] = (Optional[str], None)
        elif config.config_type == ManualTaskConfigurationType.erasure_privacy_request:
            # Use types if present, otherwise default to ["string"]
            field_types = field.get("types", ["string"])
            # Only include string fields for erasure
            if "dsr_package_label" in field and "string" in field_types:
                field_definitions[field["dsr_package_label"]] = (Optional[bool], None)
    return field_definitions


def create_privacy_request_task(
    db: Session,
    *,
    task_type: ManualTaskType,
    parent_entity_id: str,
    parent_entity_type: str,
    **kwargs: Any,
) -> ManualTask:
    """Create a new privacy request task.

    Args:
        db: Database session
        task_type: Type of privacy request task
        parent_entity_id: ID of the parent entity
        parent_entity_type: Type of the parent entity
        **kwargs: Additional task attributes
    """
    data = {
        "task_type": task_type,
        "parent_entity_id": parent_entity_id,
        "parent_entity_type": parent_entity_type,
        **kwargs,
    }
    return ManualTask.create(db=db, data=data)


def create_privacy_request_task_config(
    db: Session,
    *,
    task_id: str,
    config_type: ManualTaskConfigurationType,
    fields: List[dict[str, Any]],
    **kwargs: Any,
) -> ManualTaskConfig:
    """Create a new privacy request task configuration.

    Args:
        db: Database session
        task_id: ID of the task
        config_type: Type of privacy request task configuration
        fields: List of field definitions
        **kwargs: Additional configuration attributes
    """
    data = {
        "task_id": task_id,
        "config_type": config_type,
        "fields": fields,
        **kwargs,
    }
    return ManualTaskConfig.create(db=db, data=data)


def create_privacy_request_task_instance(
    db: Session,
    *,
    task: ManualTask,
    config_id: str,
    privacy_request_id: str,
) -> ManualTaskInstance:
    """Create a new privacy request task instance.

    Args:
        db: Database session
        task: The task to create an instance for
        config_id: ID of the configuration to use
        privacy_request_id: ID of the privacy request
    """
    return task.create_entity_instance(
        db=db,
        config_id=config_id,
        entity_id=privacy_request_id,
        entity_type="privacy_request"
    )
