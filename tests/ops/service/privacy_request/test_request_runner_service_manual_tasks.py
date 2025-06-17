from io import BytesIO
from typing import Generator
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.orm import Session


from fides.api.models.attachment import Attachment, AttachmentType, AttachmentReference, AttachmentReferenceType
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_instance import  ManualTaskInstance, ManualTaskSubmission
from fides.api.models.policy import Policy
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskParentEntityType
from fides.api.schemas.manual_tasks.manual_task_config import ManualTaskConfigurationType, ManualTaskFieldType
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.api.schemas.messaging.messaging import MessagingActionType, MessagingServiceType
from fides.api.schemas.privacy_request import (
    PrivacyRequestCreate,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.config.config_proxy import ConfigProxy
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService
from fides.service.messaging.messaging_service import MessagingService
from fides.service.manual_tasks.manual_task_service import ManualTaskService



@pytest.fixture
def mock_messaging_service() -> MessagingService:
    mock_service = create_autospec(MessagingService)
    mock_service.dispatch_message = MagicMock()
    return mock_service

@pytest.fixture
def privacy_request_service(
    db: Session, mock_messaging_service
) -> PrivacyRequestService:
    return PrivacyRequestService(db, ConfigProxy(db), mock_messaging_service)

@pytest.fixture
def manual_task_service(db: Session) -> ManualTaskService:
    return ManualTaskService(db)

@pytest.fixture
def manual_task(self, db: Session, connection_config: ConnectionConfig) -> Generator[ManualTask, None, None]:
    manual_task = ManualTask.create(
        db=db,
        data={
            "task_type": "privacy_request",
            "parent_entity_id": connection_config.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )
    yield manual_task
    manual_task.delete(db)

@pytest.fixture
def manual_task_config(db: Session, manual_task: ManualTask, manual_task_service: ManualTaskService) -> Generator[ManualTaskConfig, None, None]:
    fields = [
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
    ]
    config = manual_task_service.create_config(ManualTaskConfigurationType.access_privacy_request, fields, manual_task.id)
    yield config
    config.delete(db)

def test_privacy_request_includes_manual_task_submissions(
    db: Session,
    policy: Policy,
    connection_config: ConnectionConfig,
    run_privacy_request_task,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    storage_config,
) -> None:
    """Test that manual task submissions are included in the DSR package.

    This test verifies:
    1. Manual tasks are created and in pending state before execution
    2. Different types of manual task data (text, checkbox, attachments) are properly included
    3. Manual task data is correctly formatted in the DSR package after execution
    """
    # Create privacy request
    privacy_request = privacy_request_service.create_privacy_request(
        PrivacyRequestCreate(
            policy_key=policy.key,
            identity=Identity(email="requester@example.com"),
        ),
        authenticated=True,
    )
    # Create a manual task instance
    instance = ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "entity_id": pr.id,
            "entity_type": "privacy_request",
            "status": StatusType.pending,
        },
    )

    # Verify instance is in pending state before execution
    db.refresh(instance)
    assert instance.status == StatusType.pending

    # Create an attachment
    attachment = Attachment.create_and_upload(
        db=db,
        data={
            "file_name": "test.txt",
            "attachment_type": AttachmentType.include_with_access_package,
            "storage_key": storage_config.key,
        },
        attachment_file=BytesIO(b"test attachment content"),
    )

    # Link attachment to manual task instance
    AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_type": AttachmentReferenceType.manual_task_instance,
            "reference_id": instance.id,
        },
    )

    # Create submissions with different types of data
    text_submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "instance_id": instance.id,
            "field_id": "text_field",
            "data": {"value": "Sample text input"},
        },
    )

    checkbox_submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "instance_id": instance.id,
            "field_id": "checkbox_field",
            "data": {"value": True},
        },
    )

    # Mark instance as complete
    instance.status = StatusType.complete
    instance.save(db)

    # Verify that the manual task submissions are included in the filtered results
    filtered_results = pr.get_filtered_final_upload()
    assert "manual_tasks" in filtered_results
    assert len(filtered_results["manual_tasks"]) == 1
    task_data = filtered_results["manual_tasks"][0]

    # Verify task metadata
    assert task_data["task_id"] == manual_task.id
    assert task_data["config_id"] == manual_task_config.id
    assert task_data["status"] == StatusType.complete

    # Verify submissions data
    assert len(task_data["submissions"]) == 2
    submissions_by_field = {s["field_id"]: s for s in task_data["submissions"]}

    assert "text_field" in submissions_by_field
    assert submissions_by_field["text_field"]["data"]["value"] == "Sample text input"

    assert "checkbox_field" in submissions_by_field
    assert submissions_by_field["checkbox_field"]["data"]["value"] is True

    # Verify attachments
    assert "attachments" in task_data
    assert len(task_data["attachments"]) == 1
    attachment_data = task_data["attachments"][0]
    assert attachment_data["file_name"] == "test.txt"

    # Cleanup
    text_submission.delete(db)
    checkbox_submission.delete(db)
    attachment.delete(db)
    instance.delete(db)
    manual_task_config.delete(db)
    manual_task.delete(db)
    pr.delete(db)
