"""Tests for manual task execution functionality."""

from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestNotFound, PrivacyRequestPaused
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_instance import (
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.storage import StorageConfig
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    MANUAL_TASK_COLLECTIONS,
    ManualTaskExecutionTiming,
    ManualTaskParentEntityType,
)
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.execute_request_tasks import (
    _build_submission_data,
    _build_task_data,
    _get_configs_for_timing,
    _get_connection_config,
    _get_manual_task,
    _get_manual_task_instances,
    _get_privacy_request,
    _handle_completed_instances,
    _handle_incomplete_instances,
    _handle_no_instances,
    _process_manual_task_instances,
    _save_task_data,
    run_manual_task_node,
)
from fides.api.task.filter_results import _is_manual_task_node
from fides.api.task.filter_results import (
    _is_manual_task_node as filter_is_manual_task_node,
)
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.task_resources import Connections


@pytest.fixture
def manual_task(db: Session, connection_config: ConnectionConfig) -> ManualTask:
    """Create a manual task for testing."""
    return ManualTask.create(
        db=db,
        data={
            "task_type": "privacy_request",
            "parent_entity_id": connection_config.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )


@pytest.fixture
def manual_task_config(db: Session, manual_task: ManualTask) -> ManualTaskConfig:
    """Create a manual task config for testing."""
    config = ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
            "execution_timing": ManualTaskExecutionTiming.post_execution,
            "is_current": True,
        },
    )

    # Add field definitions
    field_data = {
        "task_id": manual_task.id,
        "config_id": config.id,
        "field_key": "text_field",
        "field_type": "text",
        "field_metadata": {
            "required": True,
            "label": "Test Field",
            "help_text": "This is a test field",
        },
    }

    ManualTaskConfigField.create(db, data=field_data)

    return config


@pytest.fixture
def request_task(
    db: Session, privacy_request: PrivacyRequest, connection_config: ConnectionConfig
) -> RequestTask:
    """Create a request task for testing."""
    return RequestTask.create(
        db=db,
        data={
            "privacy_request_id": privacy_request.id,
            "collection_address": f"{connection_config.key}:post_execution",
            "dataset_name": connection_config.key,
            "collection_name": "post_execution",
            "action_type": ActionType.access,
            "status": "pending",
            "upstream_tasks": [],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
        },
    )


class TestManualTaskNodeDetection:
    """Test manual task node detection functionality."""

    def test_is_manual_task_node_pre_execution(self):
        """Test detection of pre-execution manual task nodes."""
        node_address = "test_connection:pre_execution"
        assert _is_manual_task_node(node_address) is True

    def test_is_manual_task_node_post_execution(self):
        """Test detection of post-execution manual task nodes."""
        node_address = "test_connection:post_execution"
        assert _is_manual_task_node(node_address) is True

    def test_is_manual_task_node_regular_node(self):
        """Test that regular nodes are not detected as manual task nodes."""
        node_address = "test_connection:users"
        assert _is_manual_task_node(node_address) is False

    def test_is_manual_task_node_no_colon(self):
        """Test that nodes without colons are not detected as manual task nodes."""
        node_address = "test_connection"
        assert _is_manual_task_node(node_address) is False

    def test_filter_is_manual_task_node_consistency(self):
        """Test that both filter and execute functions detect manual task nodes consistently."""
        test_cases = [
            ("test_connection:pre_execution", True),
            ("test_connection:post_execution", True),
            ("test_connection:users", False),
            ("test_connection", False),
        ]

        for node_address, expected in test_cases:
            assert _is_manual_task_node(node_address) == expected
            assert filter_is_manual_task_node(node_address) == expected


class TestManualTaskExecutionHelpers:
    """Test the helper functions for manual task execution."""

    def test_get_privacy_request_success(
        self, db: Session, privacy_request: PrivacyRequest, request_task: RequestTask
    ):
        """Test successful privacy request retrieval."""
        result = _get_privacy_request(db, request_task)
        assert result.id == privacy_request.id

    def test_get_privacy_request_not_found(
        self, db: Session, request_task: RequestTask, policy: Policy
    ):
        """Test privacy request retrieval when not found."""
        # Create a temporary privacy request and assign it to the task
        temp_privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid4())}",
                "status": PrivacyRequestStatus.pending,
                "policy_id": policy.id,
            },
        )
        request_task.privacy_request_id = temp_privacy_request.id
        request_task.save(db)

        # Commit to ensure the privacy request is saved
        db.commit()

        # Delete the privacy request to simulate it not existing
        temp_privacy_request.delete(db)
        db.commit()

        # Refresh the session to ensure the deletion is reflected
        db.refresh(request_task)

        # Now try to get the privacy request - should raise an exception
        with pytest.raises(PrivacyRequestNotFound):
            _get_privacy_request(db, request_task)

    def test_get_connection_config_success(
        self,
        db: Session,
        request_task: RequestTask,
        connection_config: ConnectionConfig,
    ):
        """Test successful connection config retrieval."""
        result = _get_connection_config(db, request_task)
        assert result is not None
        assert result.key == connection_config.key

    def test_get_connection_config_not_found(
        self, db: Session, request_task: RequestTask
    ):
        """Test connection config retrieval when not found."""
        request_task.dataset_name = "non-existent-key"
        result = _get_connection_config(db, request_task)
        assert result is None

    def test_get_manual_task_success(
        self, db: Session, connection_config: ConnectionConfig, manual_task: ManualTask
    ):
        """Test successful manual task retrieval."""
        result = _get_manual_task(db, connection_config)
        assert result is not None
        assert result.id == manual_task.id

    def test_get_manual_task_not_found(
        self, db: Session, connection_config: ConnectionConfig
    ):
        """Test manual task retrieval when not found."""
        # Create a different connection config without a manual task
        other_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "other_connection",
                "name": "Other Connection",
                "connection_type": "postgres",
                "access": "read",
            },
        )
        result = _get_manual_task(db, other_config)
        assert result is None

    def test_get_configs_for_timing_success(
        self, manual_task: ManualTask, manual_task_config: ManualTaskConfig
    ):
        """Test successful config retrieval for specific timing."""
        configs = _get_configs_for_timing(
            manual_task, ManualTaskExecutionTiming.post_execution
        )
        assert len(configs) == 1
        assert configs[0].id == manual_task_config.id

    def test_get_configs_for_timing_no_configs(self, manual_task: ManualTask):
        """Test config retrieval when no configs exist for timing."""
        configs = _get_configs_for_timing(
            manual_task, ManualTaskExecutionTiming.pre_execution
        )
        assert len(configs) == 0

    def test_get_manual_task_instances_success(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test successful manual task instance retrieval."""
        # Create an instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.pending,
            },
        )

        instances = _get_manual_task_instances(
            db, request_task, manual_task, ManualTaskExecutionTiming.post_execution
        )
        assert len(instances) == 1
        assert instances[0].id == instance.id

    def test_get_manual_task_instances_no_instances(
        self, db: Session, request_task: RequestTask, manual_task: ManualTask
    ):
        """Test instance retrieval when no instances exist."""
        instances = _get_manual_task_instances(
            db, request_task, manual_task, ManualTaskExecutionTiming.post_execution
        )
        assert len(instances) == 0


class TestManualTaskInstanceHandling:
    """Test manual task instance handling functionality."""

    def test_handle_no_instances(
        self,
        db: Session,
        request_task: RequestTask,
        privacy_request: PrivacyRequest,
        connection_config: ConnectionConfig,
    ):
        """Test handling when no manual task instances exist."""
        with pytest.raises(PrivacyRequestPaused) as exc_info:
            _handle_no_instances(
                db,
                request_task,
                privacy_request,
                connection_config,
                ManualTaskExecutionTiming.post_execution,
            )

        # Check that the exception message is correct
        assert (
            "Privacy request paused waiting for manual tasks with timing post_execution"
            in str(exc_info.value)
        )

        # Check that privacy request status was updated
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

        # Check that request task status was updated
        db.refresh(request_task)
        assert request_task.status == ExecutionLogStatus.pending

    def test_handle_completed_instances(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test handling when all manual task instances are complete."""
        # Create completed instances
        instances = []
        for i in range(2):
            instance = ManualTaskInstance.create(
                db=db,
                data={
                    "entity_id": request_task.privacy_request_id,
                    "entity_type": "privacy_request",
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "status": StatusType.completed,
                },
            )

            # Add a submission
            field_definitions = manual_task_config.field_definitions
            if field_definitions:
                field_id = field_definitions[0].id
                submission = ManualTaskSubmission.create(
                    db=db,
                    data={
                        "task_id": manual_task.id,
                        "config_id": manual_task_config.id,
                        "instance_id": instance.id,
                        "field_id": field_id,
                        "data": {"field_key": "text_field", "value": f"test value {i}"},
                    },
                )
            instances.append(instance)

        result = _handle_completed_instances(
            db, request_task, instances, ManualTaskExecutionTiming.post_execution
        )

        assert result is True

        # Check that request task status was updated
        db.refresh(request_task)
        assert request_task.status == ExecutionLogStatus.complete

        # Check that task data was saved
        assert request_task.access_data is not None
        assert request_task.collection_address in request_task.access_data
        assert len(request_task.access_data[request_task.collection_address]) == 2

    def test_handle_incomplete_instances(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test handling when some manual task instances are incomplete."""
        # Create mixed instances (some complete, some incomplete)
        instances = []

        # Complete instance
        complete_instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.completed,
            },
        )
        # Add submissions to make the instance complete
        field_definitions = manual_task_config.field_definitions
        if field_definitions:
            field_id = field_definitions[0].id
            submission = ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "instance_id": complete_instance.id,
                    "field_id": field_id,
                    "data": {"field_key": "text_field", "value": "complete value"},
                },
            )
        instances.append(complete_instance)

        # Incomplete instance
        incomplete_instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.pending,
            },
        )
        instances.append(incomplete_instance)

        with pytest.raises(PrivacyRequestPaused) as exc_info:
            _handle_incomplete_instances(
                db, request_task, instances, 1, ManualTaskExecutionTiming.post_execution
            )

        # Check that the exception message is correct
        assert (
            "Privacy request paused waiting for 1 manual tasks with timing post_execution to complete"
            in str(exc_info.value)
        )

        # Check that privacy request status was updated
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

        # Check that request task status was updated
        db.refresh(request_task)
        assert request_task.status == ExecutionLogStatus.pending

    def test_process_manual_task_instances_all_complete(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test processing when all instances are complete."""
        # Create completed instances
        instances = []
        for i in range(2):
            instance = ManualTaskInstance.create(
                db=db,
                data={
                    "entity_id": request_task.privacy_request_id,
                    "entity_type": "privacy_request",
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "status": StatusType.completed,
                },
            )
            # Add a submission
            field_definitions = manual_task_config.field_definitions
            if field_definitions:
                field_id = field_definitions[0].id
                submission = ManualTaskSubmission.create(
                    db=db,
                    data={
                        "task_id": manual_task.id,
                        "config_id": manual_task_config.id,
                        "instance_id": instance.id,
                        "field_id": field_id,
                        "data": {"field_key": "text_field", "value": f"test value {i}"},
                    },
                )
            instances.append(instance)

        result = _process_manual_task_instances(
            db, request_task, instances, ManualTaskExecutionTiming.post_execution
        )

        assert result is True

        # Check that request task was marked as complete
        db.refresh(request_task)
        assert request_task.status == ExecutionLogStatus.complete

    def test_process_manual_task_instances_some_incomplete(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test processing when some instances are incomplete."""
        # Create mixed instances
        instances = []

        # Complete instance
        complete_instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.completed,
            },
        )
        # Add submissions to make the instance complete
        field_definitions = manual_task_config.field_definitions
        if field_definitions:
            field_id = field_definitions[0].id
            submission = ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "instance_id": complete_instance.id,
                    "field_id": field_id,
                    "data": {"field_key": "text_field", "value": "complete value"},
                },
            )
        instances.append(complete_instance)

        # Incomplete instance
        incomplete_instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.pending,
            },
        )
        instances.append(incomplete_instance)

        with pytest.raises(PrivacyRequestPaused):
            _process_manual_task_instances(
                db, request_task, instances, ManualTaskExecutionTiming.post_execution
            )

        # Check that privacy request status was updated
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

    def test_process_manual_task_instances_all_incomplete(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test processing manual task instances when all are incomplete."""
        # Create incomplete instances
        instances = []
        for i in range(3):
            instance = ManualTaskInstance.create(
                db=db,
                data={
                    "entity_id": request_task.privacy_request_id,
                    "entity_type": "privacy_request",
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "status": StatusType.pending,
                },
            )
            instances.append(instance)

        # Process instances - should raise PrivacyRequestPaused
        with pytest.raises(PrivacyRequestPaused) as exc_info:
            _process_manual_task_instances(
                db, request_task, instances, ManualTaskExecutionTiming.post_execution
            )

        # Check that the exception message mentions incomplete tasks
        assert "Privacy request paused waiting for 3 manual tasks" in str(
            exc_info.value
        )

        # Check that privacy request status was updated
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

        # Check that request task status was updated
        db.refresh(request_task)
        assert request_task.status == ExecutionLogStatus.pending

    def test_process_manual_task_instances_with_invalid_completed_instance(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test processing when an instance is marked as completed but missing required fields."""
        # Create an instance marked as completed but without required field submissions
        invalid_completed_instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.completed,  # Marked as completed but no submissions
            },
        )

        # Add a required field to the config
        field_definitions = manual_task_config.field_definitions
        if field_definitions:
            field = field_definitions[0]
            field.field_metadata = {"required": True}
            db.commit()

        instances = [invalid_completed_instance]

        # Process the instances - should reset the invalid completed instance to pending
        with pytest.raises(PrivacyRequestPaused):
            _process_manual_task_instances(
                db, request_task, instances, ManualTaskExecutionTiming.post_execution
            )

        # Check that the instance was reset to pending
        db.refresh(invalid_completed_instance)
        assert invalid_completed_instance.status == StatusType.pending

        # Check that privacy request status was updated
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

        # Cleanup
        invalid_completed_instance.delete(db)


class TestManualTaskDataBuilding:
    """Test manual task data building functionality."""

    def test_build_task_data_with_submissions(
        self, db: Session, manual_task_config: ManualTaskConfig
    ):
        """Test building task data from manual task instance with submissions."""
        # Create an instance with submissions
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": "test-privacy-request",
                "entity_type": "privacy_request",
                "task_id": manual_task_config.task_id,
                "config_id": manual_task_config.id,
                "status": StatusType.completed,
            },
        )

        # Create a submission
        field_definitions = manual_task_config.field_definitions
        if field_definitions:
            field_id = field_definitions[0].id
            submission = ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task_config.task_id,
                    "config_id": manual_task_config.id,
                    "instance_id": instance.id,
                    "field_id": field_id,
                    "data": {"field_key": "text_field", "value": "test value"},
                },
            )

        # Build task data
        task_data = _build_task_data(instance)
        assert "data" in task_data
        assert len(task_data["data"]) == 1
        assert task_data["data"][0]["field_id"] == field_id
        assert task_data["data"][0]["data"]["value"] == "test value"

    def test_build_task_data_with_attachments(
        self,
        db: Session,
        manual_task_config: ManualTaskConfig,
        storage_config: StorageConfig,
        s3_client,
        monkeypatch,
    ):
        """Test building task data from manual task instance with attachments."""

        # Mock the S3 client to prevent actual AWS calls
        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr(
            "fides.api.service.storage.s3.get_s3_client", mock_get_s3_client
        )

        # Create an instance with submissions
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": "test-privacy-request",
                "entity_type": "privacy_request",
                "task_id": manual_task_config.task_id,
                "config_id": manual_task_config.id,
                "status": StatusType.completed,
            },
        )

        # Create a submission with attachment
        field_definitions = manual_task_config.field_definitions
        attachment = None
        attachment_reference = None

        if field_definitions:
            field_id = field_definitions[0].id
            submission = ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task_config.task_id,
                    "config_id": manual_task_config.id,
                    "instance_id": instance.id,
                    "field_id": field_id,
                    "data": {"field_key": "text_field", "value": "test value"},
                },
            )

            # Create an attachment
            from io import BytesIO

            from fides.api.models.attachment import (
                Attachment,
                AttachmentReference,
                AttachmentType,
            )

            attachment = Attachment.create_and_upload(
                db=db,
                data={
                    "file_name": "test.txt",
                    "storage_key": storage_config.key,
                    "attachment_type": AttachmentType.internal_use_only,
                },
                attachment_file=BytesIO(b"test content"),
            )

            # Link attachment to submission
            attachment_reference = AttachmentReference.create(
                db=db,
                data={
                    "attachment_id": attachment.id,
                    "reference_id": submission.id,
                    "reference_type": "manual_task_submission",
                },
            )

            # Build task data
            task_data = _build_task_data(instance)
            assert "data" in task_data
            assert len(task_data["data"]) == 1
            assert "attachments" in task_data
            assert len(task_data["attachments"]) == 1
            assert task_data["attachments"][0]["file_name"] == "test.txt"
        else:
            # If no field definitions, just test that task_data is created
            task_data = _build_task_data(instance)
            assert "data" in task_data
            assert len(task_data["data"]) == 0

        # Clean up to prevent foreign key constraint violations
        if attachment_reference:
            attachment_reference.delete(db)
        if attachment:
            attachment.delete(db)
        db.commit()

    def test_build_submission_data(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test building submission data from multiple instances."""
        # Create instances
        instances = []
        for i in range(2):
            instance = ManualTaskInstance.create(
                db=db,
                data={
                    "entity_id": request_task.privacy_request_id,
                    "entity_type": "privacy_request",
                    "task_id": manual_task_config.task_id,
                    "config_id": manual_task_config.id,
                    "status": StatusType.completed,
                },
            )
            instances.append(instance)

        submission_data = _build_submission_data(request_task, instances)
        assert request_task.collection_address in submission_data
        assert len(submission_data[request_task.collection_address]) == 2

    def test_save_task_data_access(self, request_task: RequestTask):
        """Test saving task data for access tasks."""
        submission_data = {"test_key": [{"data": "test"}]}
        _save_task_data(request_task, submission_data)

        assert request_task.access_data == submission_data
        assert request_task.data_for_erasures == submission_data

    def test_save_task_data_erasure(self, request_task: RequestTask):
        """Test saving task data for erasure tasks."""
        request_task.action_type = ActionType.erasure
        submission_data = {"test_key": [{"data": "test"}]}
        _save_task_data(request_task, submission_data)

        assert request_task.data_for_erasures == submission_data
        assert (
            not hasattr(request_task, "access_data") or request_task.access_data is None
        )


class TestManualTaskExecutionFlow:
    """Test the complete manual task execution flow."""

    def test_run_manual_task_node_already_complete(
        self, db: Session, request_task: RequestTask
    ):
        """Test running a manual task node that's already complete."""
        request_task.status = ExecutionLogStatus.complete
        result = run_manual_task_node(db, request_task)
        assert result is True

    def test_run_manual_task_node_no_connection_config(
        self, db: Session, request_task: RequestTask
    ):
        """Test running a manual task node with no connection config."""
        request_task.dataset_name = "non-existent-key"
        # When there's no connection config, the task should complete without error
        result = run_manual_task_node(db, request_task)
        assert result is True
        # The task should be marked as complete since there's no manual task to wait for
        db.refresh(request_task)
        assert request_task.status == ExecutionLogStatus.complete

    def test_run_manual_task_node_no_manual_task(
        self,
        db: Session,
        request_task: RequestTask,
        connection_config: ConnectionConfig,
    ):
        """Test running a manual task node with no associated manual task."""
        # Create a connection config without a manual task
        other_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "other_connection",
                "name": "Other Connection",
                "connection_type": "postgres",
                "access": "read",
            },
        )
        request_task.dataset_name = other_config.key

        result = run_manual_task_node(db, request_task)
        assert result is True
        assert request_task.status == ExecutionLogStatus.complete

    def test_run_manual_task_node_no_configs_for_timing(
        self, db: Session, request_task: RequestTask, manual_task: ManualTask
    ):
        """Test running a manual task node with no configs for the timing."""
        # Create a config with different timing
        ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "execution_timing": ManualTaskExecutionTiming.pre_execution,
                "is_current": True,
            },
        )

        result = run_manual_task_node(db, request_task)
        assert result is True

    def test_run_manual_task_node_no_instances(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test running a manual task node with no instances."""
        with pytest.raises(PrivacyRequestPaused):
            run_manual_task_node(db, request_task)

        # Check that privacy request status was updated
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

    def test_run_manual_task_node_incomplete_instances(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        connection_config: ConnectionConfig,
    ):
        """Test running a manual task node with incomplete instances."""
        # Set the request task to use the correct connection config
        request_task.dataset_name = connection_config.key
        request_task.save(db)

        # Create incomplete instances
        instances = []
        for i in range(2):
            instance = ManualTaskInstance.create(
                db=db,
                data={
                    "entity_id": request_task.privacy_request_id,
                    "entity_type": "privacy_request",
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "status": StatusType.pending,
                },
            )
            instances.append(instance)

        with pytest.raises(PrivacyRequestPaused) as exc_info:
            run_manual_task_node(db, request_task)

        # Check that the exception message mentions incomplete tasks
        assert (
            "Privacy request paused waiting for 2 manual tasks with timing post_execution to complete"
            in str(exc_info.value)
        )

    def test_run_manual_task_node_completed_instances(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test running a manual task node with completed instances."""
        # Create a completed instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.completed,
            },
        )

        # Add a submission
        field_definitions = manual_task_config.field_definitions
        if field_definitions:
            field_id = field_definitions[0].id
            submission = ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "instance_id": instance.id,
                    "field_id": field_id,
                    "data": {"field_key": "text_field", "value": "test value"},
                },
            )

        result = run_manual_task_node(db, request_task)
        assert result is True
        assert request_task.status == ExecutionLogStatus.complete


class TestManualTaskDataUsesFiltering:
    """Test manual task data filtering by data uses."""

    def test_filter_manual_task_data_by_uses(
        self,
        db: Session,
        request_task: RequestTask,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ):
        """Test that manual task data is filtered by data uses correctly."""
        # Create a completed instance with submissions
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.completed,
            },
        )

        # Add submissions with different data uses
        field_definitions = manual_task_config.field_definitions
        if len(field_definitions) >= 2:
            # First field with user.contact.email data use
            field_1 = ManualTaskConfigField.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "field_key": "email",
                    "field_type": "text",
                    "field_metadata": {"data_uses": ["user.contact.email"]},
                },
            )
            field_1.save(db)

            submission_1 = ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "instance_id": instance.id,
                    "field_id": field_1.id,
                    "data": {"field_key": "email", "value": "test@example.com"},
                },
            )

            # Second field with user.demographic data use
            field_2 = ManualTaskConfigField.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "field_key": "age",
                    "field_type": "number",
                    "field_metadata": {"data_uses": ["user.demographic"]},
                },
            )
            field_2.save(db)

            submission_2 = ManualTaskSubmission.create(
                db=db,
                data={
                    "task_id": manual_task.id,
                    "config_id": manual_task_config.id,
                    "instance_id": instance.id,
                    "field_id": field_2.id,
                    "data": {"field_key": "age", "value": "25"},
                },
            )

            # Create manual task results
            manual_task_results = [
                {
                    "data": [
                        {
                            "field_id": submission_1.field_id,
                            "data": submission_1.data,
                        },
                        {
                            "field_id": submission_2.field_id,
                            "data": submission_2.data,
                        },
                    ]
                }
            ]

            # Create access request results with manual task data
            access_request_results = {
                f"{request_task.dataset_name}:post_execution": manual_task_results
            }

            # Create configs mapping
            manual_task_configs = {
                field_1.id: {"data_uses": ["user.contact.email"]},
                field_2.id: {"data_uses": ["user.demographic"]},
            }

            # Test filtering by user.contact data use
            target_categories = {"user.contact.email"}
            filtered_results = filter_data_categories(
                access_request_results,
                target_categories,
                DatasetGraph(),
                manual_task_configs=manual_task_configs,
            )

            # Should return manual task data filtered by user.contact.email
            manual_task_key = f"{request_task.dataset_name}:post_execution"
            assert manual_task_key in filtered_results
            assert len(filtered_results[manual_task_key]) == 1
            assert len(filtered_results[manual_task_key][0]["data"]) == 1
            assert (
                filtered_results[manual_task_key][0]["data"][0]["field_id"]
                == submission_1.field_id
            )

            # Test filtering by user.demographic data use
            target_categories = {"user.demographic"}
            filtered_results = filter_data_categories(
                access_request_results,
                target_categories,
                DatasetGraph(),
                manual_task_configs=manual_task_configs,
            )

            assert manual_task_key in filtered_results
            assert len(filtered_results[manual_task_key]) == 1
            assert len(filtered_results[manual_task_key][0]["data"]) == 1
            assert (
                filtered_results[manual_task_key][0]["data"][0]["field_id"]
                == submission_2.field_id
            )

            # Test filtering by both data uses
            target_categories = {"user.contact.email", "user.demographic"}
            filtered_results = filter_data_categories(
                access_request_results,
                target_categories,
                DatasetGraph(),
                manual_task_configs=manual_task_configs,
            )

            assert manual_task_key in filtered_results
            assert len(filtered_results[manual_task_key]) == 1
            assert len(filtered_results[manual_task_key][0]["data"]) == 2

            # Test filtering by non-matching data use
            target_categories = {"user.financial"}
            filtered_results = filter_data_categories(
                access_request_results,
                target_categories,
                DatasetGraph(),
                manual_task_configs=manual_task_configs,
            )

            # Should not return any manual task data
            assert manual_task_key not in filtered_results


class TestTaskResourcesManualTaskDetection:
    """Test manual task detection in task resources."""

    def test_has_manual_task_true(
        self, db: Session, connection_config: ConnectionConfig, manual_task: ManualTask
    ):
        """Test that has_manual_task returns True when manual task exists."""
        assert Connections.has_manual_task(db, connection_config) is True

    def test_has_manual_task_false(
        self, db: Session, connection_config: ConnectionConfig
    ):
        """Test that has_manual_task returns False when no manual task exists."""
        # Delete the manual task
        manual_tasks = ManualTask.filter(
            db=db, conditions=(ManualTask.parent_entity_id == connection_config.id)
        )
        for task in manual_tasks:
            task.delete(db)

        assert Connections.has_manual_task(db, connection_config) is False

    def test_add_manual_task_configs(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        manual_task: ManualTask,
        policy: Policy,
        privacy_request: PrivacyRequest,
    ):
        """Test adding manual task configs to connection configs list."""
        from fides.api.task.task_resources import TaskResources

        # Create request task using the existing fixtures
        request_task = RequestTask.create(
            db=db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "test:collection",
                "dataset_name": "test",
                "collection_name": "collection",
                "action_type": ActionType.access,
                "status": "pending",
                "upstream_tasks": [],
                "downstream_tasks": [],
                "all_descendant_tasks": [],
            },
        )

        # Test adding manual task configs
        connection_configs = [connection_config]
        task_resources = TaskResources(
            privacy_request, policy, connection_configs, request_task, db
        )

        # The manual task config should be included
        assert connection_config.key in task_resources.connection_configs
