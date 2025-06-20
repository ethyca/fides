from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_instance import (
    ManualTaskInstance,
    ManualTaskSubmission,
)
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


@pytest.fixture
def manual_task_config_field_1(
    db: Session, manual_task_config: ManualTaskConfig
) -> Generator[ManualTaskConfigField, None, None]:
    field = ManualTaskConfigField.create(
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
    yield field
    field.delete(db)


@pytest.fixture
def manual_task_config_field_2(
    db: Session, manual_task_config: ManualTaskConfig
) -> Generator[ManualTaskConfigField, None, None]:
    field = ManualTaskConfigField.create(
        db,
        data={
            "task_id": manual_task_config.task_id,
            "config_id": manual_task_config.id,
            "field_type": "text",
            "field_key": "field_2",
            "field_metadata": {
                "required": False,
            },
        },
    )
    yield field
    field.delete(db)


@pytest.fixture
def manual_task_instance(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    privacy_request: PrivacyRequest,
) -> Generator[ManualTaskInstance, None, None]:
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
    yield instance
    instance.delete(db)


@pytest.fixture
def manual_task_submission(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_instance: ManualTaskInstance,
    manual_task_config_field_1: ManualTaskConfigField,
    user: FidesUser,
) -> Generator[ManualTaskSubmission, None, None]:
    """Create a test manual task submission."""
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "field_id": manual_task_config_field_1.id,
            "instance_id": manual_task_instance.id,
            "submitted_by": user.id,
            "data": {"value": "test"},
        },
    )
    yield submission
    submission.delete(db)
