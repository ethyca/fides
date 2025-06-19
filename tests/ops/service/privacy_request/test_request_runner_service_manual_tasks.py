from io import BytesIO
from time import sleep
from typing import Generator
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.policy import Policy
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
)
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.api.schemas.privacy_request import PrivacyRequestCreate, PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.service.privacy_request.request_runner_service import run_privacy_request
from fides.config.config_proxy import ConfigProxy
from fides.service.manual_tasks.manual_task_service import ManualTaskService
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import (
    PrivacyRequestService,
    queue_privacy_request,
)

FIELDS = [
    {
        "field_key": "attachment_field",
        "field_type": "attachment",
        "field_metadata": {
            "required": True,
            "label": "Test Attachment Field",
            "help_text": "This is a test attachment field",
            "file_types": ["text/plain", "application/pdf"],
            "max_file_size": 1000000,
            "max_file_count": 1,
        },
    },
    {
        "field_key": "checkbox_field",
        "field_type": "checkbox",
        "field_metadata": {
            "required": True,
            "label": "Test Checkbox Field",
            "help_text": "This is a test checkbox field",
        },
    },
    {
        "field_key": "text_field",
        "field_type": "text",
        "field_metadata": {
            "required": True,
            "label": "Test Field",
            "help_text": "This is a test field",
            "min_length": 1,
            "max_length": 100,
            "pattern": "^[a-zA-Z0-9]+$",
            "placeholder": "Enter a value",
            "default_value": "default_value",
        },
    },
]


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
def manual_task(
    db: Session, connection_config: ConnectionConfig
) -> Generator[ManualTask, None, None]:
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
def manual_task_config(
    db: Session, manual_task: ManualTask, manual_task_service: ManualTaskService
) -> Generator[ManualTaskConfig, None, None]:
    config = manual_task_service.create_config(
        ManualTaskConfigurationType.access_privacy_request, FIELDS, manual_task.id
    )
    yield config
    config.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_privacy_request_includes_manual_task_submissions(
    db: Session,
    policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_service: ManualTaskService,
    storage_config,
    s3_client,
    monkeypatch,
    user: FidesUser,
    connection_config: ConnectionConfig,
) -> None:
    """Test that manual task submissions are included in the DSR package.

    This test verifies:
    1. Manual tasks are created and in pending state before execution
    2. Different types of manual task data (text, checkbox, attachments) are properly included
    3. Manual task data is correctly formatted in the DSR package after execution
    """

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    # Create privacy request
    privacy_request = privacy_request_service.create_privacy_request(
        PrivacyRequestCreate(
            policy_key=policy.key,
            identity=Identity(email="requester@example.com"),
        ),
        authenticated=True,
    )

    instance = manual_task.instances[0]
    attachment_field = next(
        f
        for f in manual_task_config.field_definitions
        if f.field_key == "attachment_field"
    )
    text_field = next(
        f for f in manual_task_config.field_definitions if f.field_key == "text_field"
    )
    checkbox_field = next(
        f
        for f in manual_task_config.field_definitions
        if f.field_key == "checkbox_field"
    )

    # Create submissions with different types of data
    text_submission = manual_task_service.create_submission(
        instance_id=instance.id,
        field_id=text_field.id,
        data={
            "field_key": "text_field",
            "field_type": "text",
            "value": "Sample text input",
        },
    )

    checkbox_submission = manual_task_service.create_submission(
        instance_id=instance.id,
        field_id=checkbox_field.id,
        data={"field_key": "checkbox_field", "field_type": "checkbox", "value": True},
    )
    attachment_submission = manual_task_service.create_submission(
        instance_id=instance.id,
        field_id=attachment_field.id,
        data={
            "field_key": "attachment_field",
            "field_type": "attachment",
            "value": "test.txt",
        },
    )

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
            "reference_type": AttachmentReferenceType.manual_task_submission,
            "reference_id": attachment_submission.id,
        },
    )

    # Mark instance as complete
    manual_task_service.instance_service.complete_task_instance(
        task_id=manual_task.id,
        config_id=manual_task_config.id,
        instance_id=instance.id,
        user_id=user.id,
    )

    # Resume the privacy request from requires_input state
    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db)
    run_privacy_request.delay(privacy_request.id).get()

    # Refresh the privacy request from the database to get the latest data
    db.refresh(privacy_request)

    # Verify that the manual task submissions are included in the filtered results
    filtered_results = privacy_request.get_filtered_final_upload()

    assert len(filtered_results) > 0
    # Manual task nodes now use connection config keys as dataset names
    manual_task_key = f"{connection_config.key}:post_execution"
    assert manual_task_key in filtered_results["access_request_rule"]
    manual_task_data = filtered_results["access_request_rule"][manual_task_key]
    assert len(manual_task_data) == 1
    assert len(manual_task_data[0]["data"]) == 3
    assert manual_task_data[0]["data"][0]["field_key"] == "text_field"
    assert manual_task_data[0]["data"][1]["field_key"] == "checkbox_field"
    assert manual_task_data[0]["data"][2]["field_key"] == "attachment_field"
    assert len(manual_task_data[0]["attachments"]) == 1

    # Also check the raw access results
    raw_results = privacy_request.get_raw_access_results()
    print(f"Raw access results: {raw_results}")
    print(
        f"Raw access results keys: {list(raw_results.keys()) if isinstance(raw_results, dict) else 'not a dict'}"
    )

    assert len(filtered_results) > 0

    # Cleanup
    attachment_submission.delete(db)
    text_submission.delete(db)
    checkbox_submission.delete(db)
    attachment.delete(db)
    instance.delete(db)
    privacy_request.delete(db)
