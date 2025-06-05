from typing import Any, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_tasks.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
    ManualTaskReference,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskType,
)


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
    # Create the config first
    config = ManualTaskConfig.create(
        db=db,
        data={
            "task_id": task_id,
            "config_type": config_type,
            **kwargs,
        },
    )

    # Create each field
    for field_data in fields:
        ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": task_id,
                "config_id": config.id,
                "field_key": field_data["dsr_package_label"],
                "field_type": ManualTaskFieldType.form,  # Default to form for DSR fields
                "metadata": {
                    "dsr_package_label": field_data["dsr_package_label"],
                    "label": field_data.get("label", field_data["dsr_package_label"]),
                    "required": field_data.get("required", False),
                    "help_text": field_data.get("help_text"),
                    "types": field_data.get("types", ["string"]),
                },
            },
        )

    return config


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
        entity_type="privacy_request",
    )


def _add_privacy_request_join(query, base_model):
    """Add the privacy request reference join to a query.

    Args:
        query: The query to modify
        base_model: The base model to join from (ManualTask, ManualTaskConfig, or ManualTaskInstance)
    """
    if base_model == ManualTask:
        return query.join(
            ManualTaskReference,
            and_(
                ManualTask.id == ManualTaskReference.task_id,
                ManualTaskReference.reference_type == "privacy_request",
            ),
        )
    elif base_model == ManualTaskConfig:
        return query.join(ManualTask, ManualTaskConfig.task_id == ManualTask.id).join(
            ManualTaskReference,
            and_(
                ManualTask.id == ManualTaskReference.task_id,
                ManualTaskReference.reference_type == "privacy_request",
            ),
        )
    elif base_model == ManualTaskInstance:
        return query.join(
            ManualTask, ManualTaskInstance.task_id == ManualTask.id
        ).filter(ManualTaskInstance.entity_type == "privacy_request")
    return query


def _add_connection_config_filter(query, base_model, connection_config_id):
    """Add connection config filter to a query.

    Args:
        query: The query to modify
        base_model: The base model to filter on
        connection_config_id: The connection config ID to filter by
    """
    if connection_config_id:
        if base_model == ManualTaskInstance:
            return query.filter(ManualTask.parent_entity_id == connection_config_id)
        return query.filter(base_model.parent_entity_id == connection_config_id)
    return query


def _add_enabled_filter(query, base_model, enabled):
    """Add enabled filter to a query.

    Args:
        query: The query to modify
        base_model: The base model to filter on
        enabled: Whether to filter for enabled or disabled tasks
    """
    if enabled is not None:
        if base_model == ManualTaskInstance:
            return query.join(
                ConnectionConfig, ManualTask.parent_entity_id == ConnectionConfig.id
            ).filter(ConnectionConfig.disabled.is_(not enabled))
        return query.join(
            ConnectionConfig, base_model.parent_entity_id == ConnectionConfig.id
        ).filter(ConnectionConfig.disabled.is_(not enabled))
    return query


def _add_privacy_request_filter(query, base_model, privacy_request):
    """Add privacy request filter to a query.

    Args:
        query: The query to modify
        base_model: The base model to filter on
        privacy_request: The privacy request to filter by
    """
    if privacy_request:
        if base_model == ManualTaskInstance:
            return query.filter(ManualTaskInstance.entity_id == privacy_request.id)
        return query.filter(ManualTaskReference.reference_id == privacy_request.id)
    return query


def _add_status_filter(query, base_model, status):
    """Add status filter to a query.

    Args:
        query: The query to modify
        base_model: The base model to filter on
        status: The status to filter by
    """
    if status:
        if base_model == ManualTaskInstance:
            return query.filter(ManualTaskInstance.status == status)
        elif base_model == ManualTaskConfig:
            return query.join(
                ManualTaskInstance,
                and_(
                    ManualTaskConfig.id == ManualTaskInstance.config_id,
                    ManualTaskInstance.entity_type == "privacy_request",
                ),
            ).filter(ManualTaskInstance.status == status)
        return query.join(
            ManualTaskInstance,
            and_(
                ManualTask.id == ManualTaskInstance.task_id,
                ManualTaskInstance.entity_type == "privacy_request",
            ),
        ).filter(ManualTaskInstance.status == status)
    return query


def _add_user_filter(query, base_model, user_id):
    """Add user filter to a query.

    Args:
        query: The query to modify
        base_model: The base model to filter on
        user_id: The user ID to filter by
    """
    if user_id:
        if base_model == ManualTaskInstance:
            return query.join(
                ManualTaskReference,
                and_(
                    ManualTask.id == ManualTaskReference.task_id,
                    ManualTaskReference.reference_type == "assigned_user",
                    ManualTaskReference.reference_id == str(user_id),
                ),
            )
        return query.join(
            ManualTaskReference,
            and_(
                base_model.id == ManualTaskReference.task_id,
                ManualTaskReference.reference_type == "assigned_user",
                ManualTaskReference.reference_id == str(user_id),
            ),
        )
    return query


def get_privacy_request_tasks(
    db: Session,
    privacy_request: Optional[PrivacyRequest] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    connection_config_id: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[ManualTask]:
    """Get tasks for privacy requests with optional filtering by privacy request, status, user ID, connection config, and enabled status.

    Args:
        db: Database session
        privacy_request: Optional privacy request to filter tasks by. If None, returns tasks for all privacy requests.
        status: Optional status to filter tasks by (pending, in_progress, completed, failed)
        user_id: Optional user ID to filter tasks by
        connection_config_id: Optional connection config ID to filter tasks by
        enabled: Optional boolean to filter tasks by enabled status
    """
    query = db.query(ManualTask)
    query = _add_privacy_request_join(query, ManualTask)
    query = _add_connection_config_filter(query, ManualTask, connection_config_id)
    query = _add_enabled_filter(query, ManualTask, enabled)
    query = _add_privacy_request_filter(query, ManualTask, privacy_request)
    query = _add_status_filter(query, ManualTask, status)
    query = _add_user_filter(query, ManualTask, user_id)
    return query.all()


def get_privacy_request_task_configs_filtered(
    db: Session,
    privacy_request: Optional[PrivacyRequest] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    connection_config_id: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[ManualTaskConfig]:
    """Get task configurations for privacy requests with optional filtering.

    Args:
        db: Database session
        privacy_request: Optional privacy request to filter configs by
        status: Optional status to filter configs by (pending, in_progress, completed, failed)
        user_id: Optional user ID to filter configs by
        connection_config_id: Optional connection config ID to filter configs by
        enabled: Optional boolean to filter configs by enabled status
    """
    query = db.query(ManualTaskConfig)
    query = _add_privacy_request_join(query, ManualTaskConfig)
    query = _add_connection_config_filter(query, ManualTaskConfig, connection_config_id)
    query = _add_enabled_filter(query, ManualTaskConfig, enabled)
    query = _add_privacy_request_filter(query, ManualTaskConfig, privacy_request)
    query = _add_status_filter(query, ManualTaskConfig, status)
    query = _add_user_filter(query, ManualTaskConfig, user_id)
    return query.all()


def get_privacy_request_task_instances_filtered(
    db: Session,
    privacy_request: Optional[PrivacyRequest] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    connection_config_id: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[ManualTaskInstance]:
    """Get task instances for privacy requests with optional filtering.

    Args:
        db: Database session
        privacy_request: Optional privacy request to filter instances by
        status: Optional status to filter instances by (pending, in_progress, completed, failed)
        user_id: Optional user ID to filter instances by
        connection_config_id: Optional connection config ID to filter instances by
        enabled: Optional boolean to filter instances by enabled status
    """
    query = db.query(ManualTaskInstance)
    query = _add_privacy_request_join(query, ManualTaskInstance)
    query = _add_connection_config_filter(
        query, ManualTaskInstance, connection_config_id
    )
    query = _add_enabled_filter(query, ManualTaskInstance, enabled)
    query = _add_privacy_request_filter(query, ManualTaskInstance, privacy_request)
    query = _add_status_filter(query, ManualTaskInstance, status)
    query = _add_user_filter(query, ManualTaskInstance, user_id)
    return query.all()
