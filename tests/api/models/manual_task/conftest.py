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

    # Clean up submissions first if they exist and field still exists
    try:
        if db.query(ManualTaskConfigField).filter_by(id=field.id).first():
            from fides.api.models.manual_task import ManualTaskSubmission

            for submission in field.submissions:
                if db.query(ManualTaskSubmission).filter_by(id=submission.id).first():
                    submission.delete(db)
            db.commit()

            # Now delete the field if it still exists
            if db.query(ManualTaskConfigField).filter_by(id=field.id).first():
                db.delete(field)
                db.commit()
    except Exception:
        # Field may have been cascade deleted, which is fine
        pass


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
    # Only try to delete if instance still exists (may have been cascade deleted)
    try:
        if db.query(ManualTaskInstance).filter_by(id=instance.id).first():
            instance.delete(db)
            db.commit()
    except Exception:
        # Instance may have been cascade deleted, which is fine
        pass


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
