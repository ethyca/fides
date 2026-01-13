from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
    ManualTaskParentEntityType,
    ManualTaskSubmission,
    ManualTaskType,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest


@pytest.fixture
def manual_task(
    db: Session, connection_config: ConnectionConfig
) -> Generator[ManualTask, None, None]:
    """Create a test manual task."""
    return ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": f"{connection_config.id}_task",
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )


@pytest.fixture
def manual_task_config(db: Session, manual_task: ManualTask) -> ManualTaskConfig:
    return ManualTaskConfig.create(
        db,
        data={
            "task_id": manual_task.id,
            "config_type": "access_privacy_request",
            "version": 1,
            "is_current": True,
        },
    )


@pytest.fixture
def manual_task_config_field(
    db: Session, manual_task_config: ManualTaskConfig
) -> Generator[ManualTaskConfigField, None, None]:
    return ManualTaskConfigField.create(
        db,
        data={
            "task_id": manual_task_config.task_id,
            "config_id": manual_task_config.id,
            "field_type": "text",
            "field_key": "field_1",
            "field_metadata": {
                "required": True,
            },
        },
    )


@pytest.fixture
def manual_task_instance(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    privacy_request: PrivacyRequest,
) -> Generator[ManualTaskInstance, None, None]:
    """Create a test manual task instance."""
    return ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "entity_id": privacy_request.id,
            "entity_type": "privacy_request",
        },
    )


@pytest.fixture
def manual_task_submission(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_instance: ManualTaskInstance,
    manual_task_config_field: ManualTaskConfigField,
    user: FidesUser,
) -> Generator[ManualTaskSubmission, None, None]:
    """Create a test manual task submission."""
    return ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "field_id": manual_task_config_field.id,
            "instance_id": manual_task_instance.id,
            "submitted_by": user.id,
            "data": {"value": "test"},
        },
    )
