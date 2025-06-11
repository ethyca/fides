import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.oauth.roles import EXTERNAL_RESPONDENT, RESPONDENT
from fides.api.schemas.manual_tasks.manual_task_config import ManualTaskFieldType
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)
from fides.service.manual_tasks.manual_task_config_service import (
    ManualTaskConfigService,
)
from fides.service.manual_tasks.manual_task_service import ManualTaskService

# Shared test data
CONFIG_TYPE = "access_privacy_request"
FIELDS = [
    {
        "field_key": "field1",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Field 1",
            "required": True,
            "help_text": "This is field 1",
            "placeholder": "Enter text here",
        },
    },
    {
        "field_key": "field2",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "Field 2",
            "required": False,
            "help_text": "This is field 2",
        },
    },
]


@pytest.fixture
def manual_task(db: Session):
    task = ManualTask.create(
        db=db,
        data={
            "parent_entity_id": "test-parent-id",
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
            "task_type": ManualTaskType.privacy_request,
        },
    )

    ManualTaskReference.create(
        db=db,
        data={
            "task_id": task.id,
            "reference_id": task.parent_entity_id,
            "reference_type": ManualTaskReferenceType.connection_config,
        },
    )

    yield task
    task.delete(db)


@pytest.fixture
def respondent_user(db: Session):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_respondent_user",
            "email_address": "fides.user@ethyca.com",
        },
    )
    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [RESPONDENT]})
    yield user
    user.delete(db)


@pytest.fixture
def external_user(db: Session):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_external_user",
            "email_address": "user@not_ethyca.com",
        },
    )
    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "roles": [EXTERNAL_RESPONDENT]}
    )
    yield user
    user.delete(db)


@pytest.fixture
def manual_task_config_service(db: Session):
    return ManualTaskConfigService(db)


@pytest.fixture
def manual_task_config(
    db: Session,
    manual_task: ManualTask,
    manual_task_config_service: ManualTaskConfigService,
):
    manual_task_config_service.create_new_version(
        task=manual_task,
        config_type=CONFIG_TYPE,
        field_updates=FIELDS,
    )


@pytest.fixture
def manual_task_service(db: Session):
    return ManualTaskService(db)
