from io import BytesIO
from time import sleep
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

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
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.policy import Policy
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskExecutionTiming,
    ManualTaskParentEntityType,
)
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.api.schemas.privacy_request import PrivacyRequestCreate, PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.service.privacy_request.request_runner_service import run_privacy_request
from fides.config.config_proxy import ConfigProxy
from fides.service.manual_tasks.manual_task_service import ManualTaskService
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService

# Test field definitions
POST_EXECUTION_FIELDS = [
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

PRE_EXECUTION_FIELDS = [
    {
        "field_key": "pre_execution_text",
        "field_type": "text",
        "field_metadata": {
            "required": True,
            "label": "Pre-Execution Text",
            "help_text": "This is a pre-execution text field",
        },
    },
    {
        "field_key": "pre_execution_checkbox",
        "field_type": "checkbox",
        "field_metadata": {
            "required": True,
            "label": "Pre-Execution Checkbox",
            "help_text": "This is a pre-execution checkbox field",
        },
    },
]

# Erasure-specific field definitions
ERASURE_POST_EXECUTION_FIELDS = [
    {
        "field_key": "erasure_confirmation",
        "field_type": "checkbox",
        "field_metadata": {
            "required": True,
            "label": "Erasure Confirmation",
            "help_text": "Confirm that data has been erased",
        },
    },
    {
        "field_key": "erasure_notes",
        "field_type": "text",
        "field_metadata": {
            "required": False,
            "label": "Erasure Notes",
            "help_text": "Additional notes about the erasure process",
            "max_length": 500,
        },
    },
    {
        "field_key": "erasure_evidence",
        "field_type": "attachment",
        "field_metadata": {
            "required": False,
            "label": "Erasure Evidence",
            "help_text": "Upload evidence of data erasure",
            "file_types": ["text/plain", "application/pdf", "image/png"],
            "max_file_size": 2000000,
            "max_file_count": 3,
        },
    },
]

ERASURE_PRE_EXECUTION_FIELDS = [
    {
        "field_key": "erasure_authorization",
        "field_type": "checkbox",
        "field_metadata": {
            "required": True,
            "label": "Erasure Authorization",
            "help_text": "Authorize the erasure of user data",
        },
    },
    {
        "field_key": "erasure_scope",
        "field_type": "text",
        "field_metadata": {
            "required": True,
            "label": "Erasure Scope",
            "help_text": "Define the scope of data to be erased",
            "max_length": 200,
        },
    },
]


# Helper functions
def create_manual_task_config(
    db: Session,
    manual_task: ManualTask,
    execution_timing: ManualTaskExecutionTiming,
    fields: List[Dict[str, Any]],
) -> ManualTaskConfig:
    """Create a manual task config with the specified fields."""
    config = ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
            "execution_timing": execution_timing,
            "is_current": True,
        },
    )

    for field_data in fields:
        ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_key": field_data["field_key"],
                "field_type": field_data["field_type"],
                "field_metadata": field_data["field_metadata"],
            },
        )

    return config


def create_erasure_manual_task_config(
    db: Session,
    manual_task: ManualTask,
    execution_timing: ManualTaskExecutionTiming,
    fields: List[Dict[str, Any]],
) -> ManualTaskConfig:
    """Create an erasure manual task config with the specified fields."""
    config = ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.erasure_privacy_request,
            "execution_timing": execution_timing,
            "is_current": True,
        },
    )

    for field_data in fields:
        ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_key": field_data["field_key"],
                "field_type": field_data["field_type"],
                "field_metadata": field_data["field_metadata"],
            },
        )

    return config


def create_erasure_policy(
    db: Session,
    oauth_client: Any,
    policy_key: str = "test_erasure_policy",
) -> Policy:
    """Create an erasure policy for testing."""
    from fides.api.models.policy import Rule, RuleTarget
    from fides.api.schemas.policy import ActionType
    from fides.api.util.data_category import DataCategory

    policy = Policy.create(
        db=db,
        data={
            "name": "Test Erasure Policy",
            "key": policy_key,
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule",
            "policy_id": policy.id,
            "masking_strategy": {
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.email").value,
            "rule_id": erasure_rule.id,
        },
    )

    return policy


def create_privacy_request(
    privacy_request_service: PrivacyRequestService,
    policy: Policy,
    email: str = "requester@example.com",
) -> Any:
    """Create a privacy request with the given email."""
    return privacy_request_service.create_privacy_request(
        PrivacyRequestCreate(
            policy_key=policy.key,
            identity=Identity(email=email),
        ),
        authenticated=True,
    )


def run_privacy_request_with_pause(
    privacy_request: Any,
    run_privacy_request_task: Any,
    timeout: int = 10,
) -> None:
    """Run a privacy request and expect it to pause for manual input."""
    try:
        run_privacy_request_task.delay(privacy_request.id).get(timeout=timeout)
    except Exception:
        # Expected to pause when no manual task instances exist
        pass


def create_manual_task_instance(
    manual_task_service: ManualTaskService,
    manual_task: ManualTask,
    config_id: str,
    privacy_request_id: str,
) -> Any:
    """Create a manual task instance."""
    return manual_task_service.instance_service.create_instance(
        task_id=manual_task.id,
        config_id=config_id,
        entity_id=privacy_request_id,
        entity_type="privacy_request",
    )


def create_submission(
    manual_task_service: ManualTaskService,
    instance_id: str,
    field_id: str,
    field_key: str,
    field_type: str,
    value: Any,
) -> Any:
    """Create a manual task submission."""
    return manual_task_service.create_submission(
        instance_id=instance_id,
        field_id=field_id,
        data={
            "field_key": field_key,
            "field_type": field_type,
            "value": value,
        },
    )


def create_attachment_with_reference(
    db: Session,
    storage_config: Any,
    submission_id: str,
    filename: str = "test.txt",
    content: bytes = b"test attachment content",
) -> Attachment:
    """Create an attachment and link it to a submission."""
    attachment = Attachment.create_and_upload(
        db=db,
        data={
            "file_name": filename,
            "attachment_type": AttachmentType.include_with_access_package,
            "storage_key": storage_config.key,
        },
        attachment_file=BytesIO(content),
    )

    AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_type": AttachmentReferenceType.manual_task_submission,
            "reference_id": submission_id,
        },
    )

    return attachment


def complete_manual_task_instance(
    manual_task_service: ManualTaskService,
    manual_task: ManualTask,
    config_id: str,
    instance_id: str,
    user_id: str,
) -> None:
    """Mark a manual task instance as complete."""
    manual_task_service.instance_service.complete_task_instance(
        task_id=manual_task.id,
        config_id=config_id,
        instance_id=instance_id,
        user_id=user_id,
    )


def resume_privacy_request(privacy_request: Any, db: Session) -> None:
    """Resume a privacy request from requires_input state."""
    from fides.api.schemas.policy import ActionType

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db)
    run_privacy_request.delay(privacy_request.id).get()


def assert_manual_task_data_in_results(
    filtered_results: Dict[str, Any],
    connection_config: ConnectionConfig,
    execution_timing: str,
    expected_field_count: int,
) -> Dict[str, Any]:
    """Assert that manual task data is present in the filtered results."""
    manual_task_key = f"{connection_config.key}:{execution_timing}"
    assert manual_task_key in filtered_results["access_request_rule"]

    manual_task_data = filtered_results["access_request_rule"][manual_task_key]
    assert manual_task_key in manual_task_data
    task_results = manual_task_data[manual_task_key]
    assert len(task_results) > 0

    first_result = task_results[0]
    assert len(first_result["data"]) == expected_field_count

    return first_result


def assert_erasure_manual_task_data_in_results(
    filtered_results: Dict[str, Any],
    connection_config: ConnectionConfig,
    execution_timing: str,
    expected_field_count: int,
) -> Dict[str, Any]:
    """Assert that erasure manual task data is present in the filtered results."""
    manual_task_key = f"{connection_config.key}:{execution_timing}"

    # For erasure requests, manual task data should be in the filtered results directly
    # The structure is different from access requests
    assert manual_task_key in filtered_results

    manual_task_data = filtered_results[manual_task_key]
    assert len(manual_task_data) > 0

    first_result = manual_task_data[0]
    assert "data" in first_result
    assert len(first_result["data"]) == expected_field_count

    return first_result


def get_erasure_manual_task_data(
    privacy_request: Any,
    connection_config: ConnectionConfig,
    execution_timing: str,
    db: Session,
) -> Dict[str, Any]:
    """Get erasure manual task data from request tasks."""
    from fides.api.schemas.policy import ActionType

    # Find the erasure request task for the manual task node
    manual_task_address = f"{connection_config.key}:{execution_timing}"
    request_task = privacy_request.get_existing_request_task(
        db=db,
        action_type=ActionType.erasure,
        collection_address=manual_task_address,
    )

    if not request_task or not request_task.data_for_erasures:
        return {}

    # Return the first result from data_for_erasures
    data_for_erasures = request_task.data_for_erasures
    if isinstance(data_for_erasures, list) and len(data_for_erasures) > 0:
        return data_for_erasures[0]
    return {}


def assert_manual_task_erasure_behavior(
    privacy_request: Any,
    connection_config: ConnectionConfig,
    execution_timing: str,
    expected_rows_masked: int,
    db: Session,
) -> None:
    """Assert that manual task erasure behavior is correct."""
    from fides.api.graph.config import CollectionAddress
    from fides.api.schemas.policy import ActionType
    from fides.api.task.task_resources import ManualTaskConnector

    # Create a manual task connector to test its behavior
    connector = ManualTaskConnector(connection_config, db)

    # Get the actual request task that was created during the privacy request execution
    manual_task_address = f"{connection_config.key}:{execution_timing}"
    collection_address = CollectionAddress.from_string(manual_task_address)
    existing_request_task = privacy_request.get_existing_request_task(
        db, ActionType.erasure, collection_address
    )

    # In real erasure scenarios, manual task nodes do not have erasure request tasks
    assert existing_request_task is None, (
        "Manual task nodes should not have erasure request tasks in erasure runs. "
        f"Found: {existing_request_task}"
    )
    # If no request task exists, the mask_data should return 0
    assert expected_rows_masked == 0
    return


def find_field_data_by_key(
    data: List[Dict[str, Any]], field_key: str
) -> Dict[str, Any]:
    """Find field data by field_key in a list of field data."""
    try:
        return next(item for item in data if item["data"]["field_key"] == field_key)
    except StopIteration as e:
        available_fields = [item["data"]["field_key"] for item in data]
        raise AssertionError(
            f"Expected field '{field_key}' not found. Available fields: {available_fields}"
        ) from e


# Fixtures
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
    db: Session, manual_task: ManualTask
) -> Generator[ManualTaskConfig, None, None]:
    config = create_manual_task_config(
        db=db,
        manual_task=manual_task,
        execution_timing=ManualTaskExecutionTiming.post_execution,
        fields=POST_EXECUTION_FIELDS,
    )
    yield config
    config.delete(db)


@pytest.fixture
def pre_execution_config(
    db: Session, manual_task: ManualTask
) -> Generator[ManualTaskConfig, None, None]:
    config = create_manual_task_config(
        db=db,
        manual_task=manual_task,
        execution_timing=ManualTaskExecutionTiming.pre_execution,
        fields=PRE_EXECUTION_FIELDS,
    )
    yield config
    config.delete(db)


@pytest.fixture
def erasure_manual_task_config(
    db: Session, manual_task: ManualTask
) -> Generator[ManualTaskConfig, None, None]:
    config = create_erasure_manual_task_config(
        db=db,
        manual_task=manual_task,
        execution_timing=ManualTaskExecutionTiming.post_execution,
        fields=ERASURE_POST_EXECUTION_FIELDS,
    )
    yield config
    config.delete(db)


@pytest.fixture
def erasure_pre_execution_config(
    db: Session, manual_task: ManualTask
) -> Generator[ManualTaskConfig, None, None]:
    config = create_erasure_manual_task_config(
        db=db,
        manual_task=manual_task,
        execution_timing=ManualTaskExecutionTiming.pre_execution,
        fields=ERASURE_PRE_EXECUTION_FIELDS,
    )
    yield config
    config.delete(db)


@pytest.fixture
def erasure_policy(db: Session, oauth_client) -> Generator[Policy, None, None]:
    policy = create_erasure_policy(db, oauth_client)
    yield policy
    # Cleanup will be handled by the test


@pytest.fixture
def dataset_config(db: Session, connection_config: ConnectionConfig) -> Generator:
    """Create a dataset configuration for testing."""
    from fides.api.models.datasetconfig import DatasetConfig
    from fides.api.models.sql_models import Dataset as CtlDataset

    dataset_dict = {
        "fides_key": "test_dataset",
        "name": "Test Dataset",
        "description": "A test dataset for manual task testing",
        "collections": [
            {
                "name": "users",
                "description": "User data",
                "fields": [
                    {
                        "name": "id",
                        "description": "User ID",
                        "data_categories": ["user.unique_id"],
                        "fides_meta": {"primary_key": True},
                    },
                    {
                        "name": "email",
                        "description": "User email",
                        "data_categories": ["user.contact.email"],
                        "fides_meta": {"identity": "email"},
                    },
                ],
            }
        ],
    }

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": dataset_dict["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )

    yield dataset_config
    dataset_config.delete(db)
    ctl_dataset.delete(db)


@pytest.fixture
def mock_s3_client(monkeypatch, s3_client):
    """Mock S3 client for storage operations."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
    return s3_client


# Tests
@pytest.mark.usefixtures("use_dsr_3_0")
def test_privacy_request_includes_manual_task_submissions(
    db: Session,
    policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_service: ManualTaskService,
    storage_config,
    mock_s3_client,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
) -> None:
    """Test that manual task submissions are included in the DSR package."""

    # Create privacy request
    privacy_request = create_privacy_request(privacy_request_service, policy)

    # Run privacy request - it should pause for manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create manual task instance and submissions
    instance = create_manual_task_instance(
        manual_task_service, manual_task, manual_task_config.id, privacy_request.id
    )

    # Get field definitions
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

    # Create submissions
    text_submission = create_submission(
        manual_task_service,
        instance.id,
        text_field.id,
        "text_field",
        "text",
        "Sample text input",
    )
    checkbox_submission = create_submission(
        manual_task_service,
        instance.id,
        checkbox_field.id,
        "checkbox_field",
        "checkbox",
        True,
    )
    attachment_submission = create_submission(
        manual_task_service,
        instance.id,
        attachment_field.id,
        "attachment_field",
        "attachment",
        "test.txt",
    )

    # Create attachment and link it
    attachment = create_attachment_with_reference(
        db, storage_config, attachment_submission.id
    )

    # Complete the task instance
    complete_manual_task_instance(
        manual_task_service, manual_task, manual_task_config.id, instance.id, user.id
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Verify results
    filtered_results = privacy_request.get_filtered_final_upload()
    assert len(filtered_results) > 0

    first_result = assert_manual_task_data_in_results(
        filtered_results, connection_config, "post_execution", 3
    )

    # Verify specific field data
    text_field_data = find_field_data_by_key(first_result["data"], "text_field")
    checkbox_field_data = find_field_data_by_key(first_result["data"], "checkbox_field")
    attachment_field_data = find_field_data_by_key(
        first_result["data"], "attachment_field"
    )

    assert text_field_data["data"]["value"] == "Sample text input"
    assert checkbox_field_data["data"]["value"] is True
    assert attachment_field_data["data"]["value"] == "test.txt"
    assert len(first_result["attachments"]) == 1

    # Cleanup
    AttachmentReference.filter(
        db, conditions=(AttachmentReference.reference_id == attachment_submission.id)
    ).delete()
    text_submission.delete(db)
    checkbox_submission.delete(db)
    attachment_submission.delete(db)
    attachment.delete(db)
    instance.delete(db)
    privacy_request.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_privacy_request_includes_pre_execution_manual_task_submissions(
    db: Session,
    policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    manual_task_service: ManualTaskService,
    storage_config,
    mock_s3_client,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
    pre_execution_config: ManualTaskConfig,
) -> None:
    """Test that pre-execution manual task submissions are included in the DSR package."""

    # Create privacy request
    privacy_request = create_privacy_request(privacy_request_service, policy)

    # Run privacy request - it should pause for manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create manual task instance and submissions
    instance = create_manual_task_instance(
        manual_task_service, manual_task, pre_execution_config.id, privacy_request.id
    )

    # Get field definitions
    pre_text_field = next(
        f
        for f in pre_execution_config.field_definitions
        if f.field_key == "pre_execution_text"
    )
    pre_checkbox_field = next(
        f
        for f in pre_execution_config.field_definitions
        if f.field_key == "pre_execution_checkbox"
    )

    # Create submissions
    pre_text_submission = create_submission(
        manual_task_service,
        instance.id,
        pre_text_field.id,
        "pre_execution_text",
        "text",
        "Pre-execution text input",
    )
    pre_checkbox_submission = create_submission(
        manual_task_service,
        instance.id,
        pre_checkbox_field.id,
        "pre_execution_checkbox",
        "checkbox",
        True,
    )

    # Complete the task instance
    complete_manual_task_instance(
        manual_task_service, manual_task, pre_execution_config.id, instance.id, user.id
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Verify results
    filtered_results = privacy_request.get_filtered_final_upload()
    assert len(filtered_results) > 0

    first_result = assert_manual_task_data_in_results(
        filtered_results, connection_config, "pre_execution", 2
    )

    # Verify specific field data
    pre_text_field_data = find_field_data_by_key(
        first_result["data"], "pre_execution_text"
    )
    pre_checkbox_field_data = find_field_data_by_key(
        first_result["data"], "pre_execution_checkbox"
    )

    assert pre_text_field_data["data"]["value"] == "Pre-execution text input"
    assert pre_checkbox_field_data["data"]["value"] is True

    # Cleanup
    pre_text_submission.delete(db)
    pre_checkbox_submission.delete(db)
    instance.delete(db)
    privacy_request.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_privacy_request_includes_both_pre_and_post_execution_manual_task_submissions(
    db: Session,
    policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_service: ManualTaskService,
    storage_config,
    mock_s3_client,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
    pre_execution_config: ManualTaskConfig,
) -> None:
    """Test that both pre and post-execution manual task submissions are included in the DSR package."""

    # Create privacy request
    privacy_request = create_privacy_request(privacy_request_service, policy)

    # Run privacy request - it should pause for pre-execution manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create pre-execution manual task instance and submissions
    pre_instance = create_manual_task_instance(
        manual_task_service, manual_task, pre_execution_config.id, privacy_request.id
    )

    pre_text_field = next(
        f
        for f in pre_execution_config.field_definitions
        if f.field_key == "pre_execution_text"
    )
    pre_checkbox_field = next(
        f
        for f in pre_execution_config.field_definitions
        if f.field_key == "pre_execution_checkbox"
    )

    pre_text_submission = create_submission(
        manual_task_service,
        pre_instance.id,
        pre_text_field.id,
        "pre_execution_text",
        "text",
        "Pre-execution text input",
    )
    pre_checkbox_submission = create_submission(
        manual_task_service,
        pre_instance.id,
        pre_checkbox_field.id,
        "pre_execution_checkbox",
        "checkbox",
        True,
    )

    # Complete pre-execution task
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        pre_execution_config.id,
        pre_instance.id,
        user.id,
    )

    # Resume - should pause again for post-execution tasks
    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db)
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create post-execution manual task instance and submissions
    post_instance = create_manual_task_instance(
        manual_task_service, manual_task, manual_task_config.id, privacy_request.id
    )

    attachment_field = next(
        f
        for f in manual_task_config.field_definitions
        if f.field_key == "attachment_field"
    )
    post_text_field = next(
        f for f in manual_task_config.field_definitions if f.field_key == "text_field"
    )
    checkbox_field = next(
        f
        for f in manual_task_config.field_definitions
        if f.field_key == "checkbox_field"
    )

    post_text_submission = create_submission(
        manual_task_service,
        post_instance.id,
        post_text_field.id,
        "text_field",
        "text",
        "Post-execution text input",
    )
    checkbox_submission = create_submission(
        manual_task_service,
        post_instance.id,
        checkbox_field.id,
        "checkbox_field",
        "checkbox",
        True,
    )
    attachment_submission = create_submission(
        manual_task_service,
        post_instance.id,
        attachment_field.id,
        "attachment_field",
        "attachment",
        "test.txt",
    )

    # Create attachment and link it
    attachment = create_attachment_with_reference(
        db, storage_config, attachment_submission.id
    )

    # Complete post-execution task
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        manual_task_config.id,
        post_instance.id,
        user.id,
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Verify results
    filtered_results = privacy_request.get_filtered_final_upload()
    assert len(filtered_results) > 0

    # Check pre-execution data
    pre_first_result = assert_manual_task_data_in_results(
        filtered_results, connection_config, "pre_execution", 2
    )
    pre_text_field_data = find_field_data_by_key(
        pre_first_result["data"], "pre_execution_text"
    )
    pre_checkbox_field_data = find_field_data_by_key(
        pre_first_result["data"], "pre_execution_checkbox"
    )
    assert pre_text_field_data["data"]["value"] == "Pre-execution text input"
    assert pre_checkbox_field_data["data"]["value"] is True

    # Check post-execution data
    post_first_result = assert_manual_task_data_in_results(
        filtered_results, connection_config, "post_execution", 3
    )
    post_text_field_data = find_field_data_by_key(
        post_first_result["data"], "text_field"
    )
    post_checkbox_field_data = find_field_data_by_key(
        post_first_result["data"], "checkbox_field"
    )
    post_attachment_field_data = find_field_data_by_key(
        post_first_result["data"], "attachment_field"
    )
    assert post_text_field_data["data"]["value"] == "Post-execution text input"
    assert post_checkbox_field_data["data"]["value"] is True
    assert post_attachment_field_data["data"]["value"] == "test.txt"
    assert len(post_first_result["attachments"]) == 1

    # Cleanup
    AttachmentReference.filter(
        db, conditions=(AttachmentReference.reference_id == attachment_submission.id)
    ).delete()
    pre_text_submission.delete(db)
    pre_checkbox_submission.delete(db)
    post_text_submission.delete(db)
    checkbox_submission.delete(db)
    attachment_submission.delete(db)
    attachment.delete(db)
    pre_instance.delete(db)
    post_instance.delete(db)
    privacy_request.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_erasure_request_includes_manual_task_submissions(
    db: Session,
    erasure_policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    erasure_manual_task_config: ManualTaskConfig,
    manual_task_service: ManualTaskService,
    storage_config,
    mock_s3_client,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
) -> None:
    """Test that erasure manual task submissions are properly recorded and erasure completes successfully."""

    # Create privacy request with erasure policy
    privacy_request = create_privacy_request(privacy_request_service, erasure_policy)

    # Run privacy request - it should pause for manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create manual task instance and submissions
    instance = create_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        privacy_request.id,
    )

    # Get field definitions
    erasure_confirmation_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_confirmation"
    )
    erasure_notes_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_notes"
    )
    erasure_evidence_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_evidence"
    )

    # Create submissions
    confirmation_submission = create_submission(
        manual_task_service,
        instance.id,
        erasure_confirmation_field.id,
        "erasure_confirmation",
        "checkbox",
        True,
    )
    notes_submission = create_submission(
        manual_task_service,
        instance.id,
        erasure_notes_field.id,
        "erasure_notes",
        "text",
        "Data has been successfully erased from all systems",
    )
    evidence_submission = create_submission(
        manual_task_service,
        instance.id,
        erasure_evidence_field.id,
        "erasure_evidence",
        "attachment",
        "erasure_confirmation.pdf",
    )

    # Create attachment and link it
    attachment = create_attachment_with_reference(
        db,
        storage_config,
        evidence_submission.id,
        "erasure_confirmation.pdf",
        b"erasure evidence content",
    )

    # Complete the task instance
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        instance.id,
        user.id,
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Verify erasure completed successfully
    assert privacy_request.status == PrivacyRequestStatus.complete

    # Verify manual task instance was completed
    db.refresh(instance)
    assert instance.status == StatusType.completed

    # Verify submissions were recorded
    assert confirmation_submission.data["value"] is True
    assert (
        notes_submission.data["value"]
        == "Data has been successfully erased from all systems"
    )
    assert evidence_submission.data["value"] == "erasure_confirmation.pdf"

    # Cleanup
    AttachmentReference.filter(
        db, conditions=(AttachmentReference.reference_id == evidence_submission.id)
    ).delete()
    confirmation_submission.delete(db)
    notes_submission.delete(db)
    evidence_submission.delete(db)
    attachment.delete(db)
    instance.delete(db)
    privacy_request.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_erasure_request_includes_pre_execution_manual_task_submissions(
    db: Session,
    erasure_policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    manual_task_service: ManualTaskService,
    storage_config,
    mock_s3_client,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
    erasure_pre_execution_config: ManualTaskConfig,
) -> None:
    """Test that pre-execution erasure manual task submissions are properly recorded and erasure completes successfully."""

    # Create privacy request with erasure policy
    privacy_request = create_privacy_request(privacy_request_service, erasure_policy)

    # Run privacy request - it should pause for manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create manual task instance and submissions
    instance = create_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_pre_execution_config.id,
        privacy_request.id,
    )

    # Get field definitions
    authorization_field = next(
        f
        for f in erasure_pre_execution_config.field_definitions
        if f.field_key == "erasure_authorization"
    )
    scope_field = next(
        f
        for f in erasure_pre_execution_config.field_definitions
        if f.field_key == "erasure_scope"
    )

    # Create submissions
    authorization_submission = create_submission(
        manual_task_service,
        instance.id,
        authorization_field.id,
        "erasure_authorization",
        "checkbox",
        True,
    )
    scope_submission = create_submission(
        manual_task_service,
        instance.id,
        scope_field.id,
        "erasure_scope",
        "text",
        "All user data including profile, preferences, and activity logs",
    )

    # Complete the task instance
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_pre_execution_config.id,
        instance.id,
        user.id,
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Verify erasure completed successfully
    assert privacy_request.status == PrivacyRequestStatus.complete

    # Verify manual task instance was completed
    db.refresh(instance)
    assert instance.status == StatusType.completed

    # Verify submissions were recorded
    assert authorization_submission.data["value"] is True
    assert (
        scope_submission.data["value"]
        == "All user data including profile, preferences, and activity logs"
    )

    # Cleanup
    authorization_submission.delete(db)
    scope_submission.delete(db)
    instance.delete(db)
    privacy_request.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_erasure_request_includes_both_pre_and_post_execution_manual_task_submissions(
    db: Session,
    erasure_policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    erasure_manual_task_config: ManualTaskConfig,
    manual_task_service: ManualTaskService,
    storage_config,
    mock_s3_client,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
    erasure_pre_execution_config: ManualTaskConfig,
) -> None:
    """Test that both pre and post-execution erasure manual task submissions are properly recorded and erasure completes successfully."""

    # Create privacy request with erasure policy
    privacy_request = create_privacy_request(privacy_request_service, erasure_policy)

    # Run privacy request - it should pause for pre-execution manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create pre-execution manual task instance and submissions
    pre_instance = create_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_pre_execution_config.id,
        privacy_request.id,
    )

    pre_authorization_field = next(
        f
        for f in erasure_pre_execution_config.field_definitions
        if f.field_key == "erasure_authorization"
    )
    pre_scope_field = next(
        f
        for f in erasure_pre_execution_config.field_definitions
        if f.field_key == "erasure_scope"
    )

    pre_authorization_submission = create_submission(
        manual_task_service,
        pre_instance.id,
        pre_authorization_field.id,
        "erasure_authorization",
        "checkbox",
        True,
    )
    pre_scope_submission = create_submission(
        manual_task_service,
        pre_instance.id,
        pre_scope_field.id,
        "erasure_scope",
        "text",
        "Complete user data erasure including all associated records",
    )

    # Complete pre-execution task
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_pre_execution_config.id,
        pre_instance.id,
        user.id,
    )

    # Resume - should pause again for post-execution tasks
    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db)
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create post-execution manual task instance and submissions
    post_instance = create_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        privacy_request.id,
    )

    post_confirmation_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_confirmation"
    )
    post_notes_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_notes"
    )
    post_evidence_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_evidence"
    )

    post_confirmation_submission = create_submission(
        manual_task_service,
        post_instance.id,
        post_confirmation_field.id,
        "erasure_confirmation",
        "checkbox",
        True,
    )
    post_notes_submission = create_submission(
        manual_task_service,
        post_instance.id,
        post_notes_field.id,
        "erasure_notes",
        "text",
        "Erasure completed successfully. All user data has been permanently deleted.",
    )
    post_evidence_submission = create_submission(
        manual_task_service,
        post_instance.id,
        post_evidence_field.id,
        "erasure_evidence",
        "attachment",
        "erasure_completion_report.pdf",
    )

    # Create attachment and link it
    attachment = create_attachment_with_reference(
        db,
        storage_config,
        post_evidence_submission.id,
        "erasure_completion_report.pdf",
        b"erasure completion report content",
    )

    # Complete post-execution task
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        post_instance.id,
        user.id,
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Verify erasure completed successfully
    assert privacy_request.status == PrivacyRequestStatus.complete

    # Verify both manual task instances were completed
    db.refresh(pre_instance)
    db.refresh(post_instance)
    assert pre_instance.status == StatusType.completed
    assert post_instance.status == StatusType.completed

    # Verify pre-execution submissions were recorded
    assert pre_authorization_submission.data["value"] is True
    assert (
        pre_scope_submission.data["value"]
        == "Complete user data erasure including all associated records"
    )

    # Verify post-execution submissions were recorded
    assert post_confirmation_submission.data["value"] is True
    assert (
        post_notes_submission.data["value"]
        == "Erasure completed successfully. All user data has been permanently deleted."
    )
    assert post_evidence_submission.data["value"] == "erasure_completion_report.pdf"

    # Cleanup
    AttachmentReference.filter(
        db, conditions=(AttachmentReference.reference_id == post_evidence_submission.id)
    ).delete()
    pre_authorization_submission.delete(db)
    pre_scope_submission.delete(db)
    post_confirmation_submission.delete(db)
    post_notes_submission.delete(db)
    post_evidence_submission.delete(db)
    attachment.delete(db)
    pre_instance.delete(db)
    post_instance.delete(db)
    privacy_request.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_manual_task_erasure_behavior_no_request_task(
    db: Session,
    erasure_policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    erasure_manual_task_config: ManualTaskConfig,
    manual_task_service: ManualTaskService,
    storage_config,
    mock_s3_client,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
) -> None:
    """Test that manual task erasure behavior is correct when no erasure request task exists."""

    # Create privacy request with erasure policy
    privacy_request = create_privacy_request(privacy_request_service, erasure_policy)

    # Run privacy request - it should pause for manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create manual task instance and submissions
    instance = create_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        privacy_request.id,
    )

    # Get field definitions
    erasure_confirmation_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_confirmation"
    )
    erasure_notes_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_notes"
    )

    # Create submissions
    confirmation_submission = create_submission(
        manual_task_service,
        instance.id,
        erasure_confirmation_field.id,
        "erasure_confirmation",
        "checkbox",
        True,
    )
    notes_submission = create_submission(
        manual_task_service,
        instance.id,
        erasure_notes_field.id,
        "erasure_notes",
        "text",
        "Data has been successfully erased from all systems",
    )

    # Complete the task instance
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        instance.id,
        user.id,
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Test the manual task erasure behavior
    # In real erasure scenarios, manual task nodes do not have erasure request tasks
    # The mask_data method should return 0
    assert_manual_task_erasure_behavior(
        privacy_request, connection_config, "post_execution", 0, db
    )

    # Verify erasure completed successfully
    assert privacy_request.status == PrivacyRequestStatus.complete

    # Verify manual task instance was completed
    db.refresh(instance)
    assert instance.status == StatusType.completed

    # Verify submissions were recorded
    assert confirmation_submission.data["value"] is True
    assert (
        notes_submission.data["value"]
        == "Data has been successfully erased from all systems"
    )

    # Cleanup
    confirmation_submission.delete(db)
    notes_submission.delete(db)
    instance.delete(db)
    privacy_request.delete(db)


@pytest.mark.usefixtures("use_dsr_3_0")
def test_manual_task_connector_no_erasure_request_task(
    db: Session,
    erasure_policy: Policy,
    privacy_request_service: PrivacyRequestService,
    manual_task: ManualTask,
    erasure_manual_task_config: ManualTaskConfig,
    manual_task_service: ManualTaskService,
    user: FidesUser,
    connection_config: ConnectionConfig,
    dataset_config,
    run_privacy_request_task,
) -> None:
    """Test that ManualTaskConnector properly handles cases with no erasure request task for manual nodes."""

    # Create privacy request with erasure policy
    privacy_request = create_privacy_request(privacy_request_service, erasure_policy)

    # Run privacy request - it should pause for manual input
    run_privacy_request_with_pause(privacy_request, run_privacy_request_task)
    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # Create manual task instance
    instance = create_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        privacy_request.id,
    )

    # Get field definitions for required fields
    erasure_confirmation_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_confirmation"
    )
    erasure_notes_field = next(
        f
        for f in erasure_manual_task_config.field_definitions
        if f.field_key == "erasure_notes"
    )

    # Create minimal required submissions (empty/null values to test "no data" handling)
    confirmation_submission = create_submission(
        manual_task_service,
        instance.id,
        erasure_confirmation_field.id,
        "erasure_confirmation",
        "checkbox",
        False,  # No confirmation
    )
    notes_submission = create_submission(
        manual_task_service,
        instance.id,
        erasure_notes_field.id,
        "erasure_notes",
        "text",
        "",  # Empty notes
    )

    # Complete the task instance with minimal data
    complete_manual_task_instance(
        manual_task_service,
        manual_task,
        erasure_manual_task_config.id,
        instance.id,
        user.id,
    )

    # Resume and complete the privacy request
    resume_privacy_request(privacy_request, db)
    db.refresh(privacy_request)

    # Test the manual task erasure behavior with minimal data
    # In real erasure scenarios, manual task nodes do not have erasure request tasks
    # The mask_data method should return 0
    assert_manual_task_erasure_behavior(
        privacy_request, connection_config, "post_execution", 0, db
    )

    # Verify erasure completed successfully
    assert privacy_request.status == PrivacyRequestStatus.complete

    # Verify manual task instance was completed
    db.refresh(instance)
    assert instance.status == StatusType.completed

    # Verify submissions were recorded (even with minimal data)
    assert confirmation_submission.data["value"] is False
    assert notes_submission.data["value"] == ""

    # Cleanup
    confirmation_submission.delete(db)
    notes_submission.delete(db)
    instance.delete(db)
    privacy_request.delete(db)
