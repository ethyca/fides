"""Tests for manual task execution functionality."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestNotFound, PrivacyRequestPaused
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
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
    _is_manual_task_node,
    _process_manual_task_instances,
    _save_task_data,
    run_manual_task_node,
)
from fides.api.task.filter_results import (
    _is_manual_task_node as filter_is_manual_task_node,
)
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
    fields = [
        {
            "field_key": "text_field",
            "field_type": "text",
            "field_metadata": {
                "required": True,
                "label": "Test Field",
                "help_text": "This is a test field",
            },
        }
    ]

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
    for field in fields:
        config.add_field_definition(db, field)

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
        self, db: Session, request_task: RequestTask
    ):
        """Test privacy request retrieval when not found."""
        request_task.privacy_request_id = "non-existent-id"
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
        submission = instance.add_submission(
            db=db,
            field_id=manual_task_config.field_definitions[0].id,
            data={"field_key": "text_field", "value": "test value"},
        )

        task_data = _build_task_data(instance)
        assert "data" in task_data
        assert len(task_data["data"]) == 1
        assert task_data["data"][0]["field_id"] == submission.field_id
        assert task_data["data"][0]["data"]["value"] == "test value"

    def test_build_task_data_with_attachments(
        self, db: Session, manual_task_config: ManualTaskConfig
    ):
        """Test building task data with attachments."""
        # Create an instance with submissions and attachments
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
        submission = instance.add_submission(
            db=db,
            field_id=manual_task_config.field_definitions[0].id,
            data={"field_key": "text_field", "value": "test value"},
        )

        # Mock attachment
        submission.attachments = [
            MagicMock(file_name="test.txt", storage_key="test-key")
        ]

        task_data = _build_task_data(instance)
        assert "attachments" in task_data
        assert len(task_data["attachments"]) == 1
        assert task_data["attachments"][0]["file_name"] == "test.txt"

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
        request_task.status = "complete"
        result = run_manual_task_node(db, request_task)
        assert result is True

    def test_run_manual_task_node_no_connection_config(
        self, db: Session, request_task: RequestTask
    ):
        """Test running a manual task node with no connection config."""
        request_task.dataset_name = "non-existent-key"
        result = run_manual_task_node(db, request_task)
        assert result is True
        assert request_task.status == "complete"

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
            },
        )
        request_task.dataset_name = other_config.key

        result = run_manual_task_node(db, request_task)
        assert result is True

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
        privacy_request: PrivacyRequest,
    ):
        """Test running a manual task node with incomplete instances."""
        # Create an incomplete instance
        ManualTaskInstance.create(
            db=db,
            data={
                "entity_id": request_task.privacy_request_id,
                "entity_type": "privacy_request",
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "status": StatusType.pending,
            },
        )

        with pytest.raises(PrivacyRequestPaused):
            run_manual_task_node(db, request_task)

        # Check that privacy request status was updated
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

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
        instance.add_submission(
            db=db,
            field_id=manual_task_config.field_definitions[0].id,
            data={"field_key": "text_field", "value": "test value"},
        )

        result = run_manual_task_node(db, request_task)
        assert result is True
        assert request_task.status == "complete"


class TestTaskResourcesManualTaskDetection:
    """Test manual task detection in task resources."""

    def test_has_manual_task_true(
        self, db: Session, connection_config: ConnectionConfig, manual_task: ManualTask
    ):
        """Test that has_manual_task returns True when manual task exists."""
        assert Connections._has_manual_task(db, connection_config) is True

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

        assert Connections._has_manual_task(db, connection_config) is False

    def test_add_manual_task_configs(
        self, db: Session, connection_config: ConnectionConfig, manual_task: ManualTask
    ):
        """Test adding manual task configs to connection configs list."""
        from fides.api.models.policy import Policy
        from fides.api.models.privacy_request import PrivacyRequest, RequestTask
        from fides.api.task.task_resources import TaskResources

        # Create required objects
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": "test-policy",
            },
        )

        policy = Policy.create(
            db=db,
            data={
                "key": "test-policy",
                "name": "Test Policy",
            },
        )

        request_task = RequestTask.create(
            db=db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "test:collection",
                "dataset_name": "test",
                "collection_name": "collection",
                "action_type": ActionType.access,
                "status": "pending",
            },
        )

        # Test adding manual task configs
        connection_configs = [connection_config]
        task_resources = TaskResources(
            privacy_request, policy, connection_configs, request_task, db
        )

        # The manual task config should be included
        assert connection_config.key in task_resources.connection_configs
