from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig, ManualTaskConfigField
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance, ManualTaskSubmission
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
    ManualTaskType,
)


@pytest.fixture
def manual_task(
    db: Session, connection_config: ConnectionConfig
) -> Generator[ManualTask, None, None]:
    """Create a test manual task."""
    task = ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": f"{connection_config.id}_task",
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )
    yield task
    try:
        task.delete(db)
    except Exception as e:
        pass


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

def manual_task_config_field_1(db: Session, manual_task_config: ManualTaskConfig) -> ManualTaskConfigField:
    return ManualTaskConfigField.create(
        db,
        data={
            "config_id": manual_task_config.id,
            "field_type": "text",
            "field_key": "field_1",
            "required": True,
        },
    )

def manual_task_config_field_2(db: Session, manual_task_config: ManualTaskConfig) -> ManualTaskConfigField:
    return ManualTaskConfigField.create(
        db,
        data={
            "config_id": manual_task_config.id,
            "field_type": "text",
            "field_key": "field_2",
            "required": False,
        },
    )

@pytest.fixture
def manual_task_instance(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    privacy_request: PrivacyRequest
) -> ManualTaskInstance:
    """Create a test manual task instance."""
    instance = ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "entity_id": privacy_request.id,
            "entity_type": "privacy_request",
        },
    )
    return instance


@pytest.fixture
def manual_task_submission(db: Session, manual_task_instance: ManualTaskInstance) -> ManualTaskSubmission:
    """Create a test manual task submission."""
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": manual_task_config_field_1.id,
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"value": "test"},
        },
    )
    return submission
