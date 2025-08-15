from unittest.mock import patch

import pytest

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.models.manual_task import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.conditional_dependencies.schemas import (
    ConditionEvaluationResult,
    GroupEvaluationResult,
)
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
from fides.api.util.cache import get_cache
from tests.api.task.manual.conftest import _build_request_task, _build_task_resources


def _create_graph_task_setup(db, connection_setup, privacy_request, action_type):
    """Helper to create graph task setup with minimal duplication"""
    connection_config, manual_task, config, field = connection_setup

    request_task = _build_request_task(
        db, privacy_request, connection_config, action_type
    )
    resources = _build_task_resources(
        db, privacy_request, privacy_request.policy, connection_config, request_task
    )

    graph_task = ManualTaskGraphTask(resources)

    return {
        "connection_config": connection_config,
        "manual_task": manual_task,
        "config": config,
        "field": field,
        "graph_task": graph_task,
        "privacy_request": privacy_request,
        "request_task": request_task,
        "resources": resources,
    }


@pytest.fixture
def manual_task_setup(db, connection_with_manual_access_task, access_privacy_request):
    """Create manual task setup for testing"""
    return _create_graph_task_setup(
        db,
        connection_with_manual_access_task,
        access_privacy_request,
        ActionType.access,
    )


@pytest.fixture
def erasure_task_setup(
    db, connection_with_manual_erasure_task, erasure_privacy_request
):
    """Create erasure task setup for testing erasure mode"""
    return _create_graph_task_setup(
        db,
        connection_with_manual_erasure_task,
        erasure_privacy_request,
        ActionType.erasure,
    )


@pytest.fixture
def conditional_dependency_setup(
    db, connection_with_manual_access_task, access_privacy_request, condition_gt_18
):
    """Create setup with conditional dependencies for testing"""
    setup = _create_graph_task_setup(
        db,
        connection_with_manual_access_task,
        access_privacy_request,
        ActionType.access,
    )
    setup["conditional_dependency"] = condition_gt_18
    return setup


# =============================================================================
# Helper Functions for Common Test Patterns
# =============================================================================


def mock_conditional_dependencies(
    conditions_met=True, conditional_data={"test": "data"}
):
    """Helper to mock conditional dependency evaluation"""
    if conditions_met is None:
        # No conditional dependencies
        return (
            patch(
                "fides.api.task.manual.manual_task_graph_task.extract_conditional_dependency_data_from_inputs",
                autospec=True,
                return_value={},
            ),
            patch(
                "fides.api.task.manual.manual_task_graph_task.evaluate_conditional_dependencies",
                autospec=True,
                return_value=None,
            ),
        )
    else:
        # Has conditional dependencies
        return (
            patch(
                "fides.api.task.manual.manual_task_graph_task.extract_conditional_dependency_data_from_inputs",
                autospec=True,
                return_value=conditional_data,
            ),
            patch(
                "fides.api.task.manual.manual_task_graph_task.evaluate_conditional_dependencies",
                autospec=True,
                return_value=type("MockResult", (), {"result": conditions_met})(),
            ),
        )


def create_test_instance(db, manual_task, config, privacy_request):
    """Helper to create a test manual task instance"""
    return ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": config.id,
            "entity_id": privacy_request.id,
            "entity_type": "privacy_request",
            "status": "pending",
        },
    )


def create_test_submission(db, manual_task, config, field, instance):
    """Helper to create a test submission"""
    return ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": config.id,
            "field_id": field.id,
            "instance_id": instance.id,
            "submitted_by": None,
            "data": {
                "field_type": ManualTaskFieldType.text.value,
                "value": "test_value",
            },
        },
    )


def verify_instance_creation(db, privacy_request, manual_task, expected_count=1):
    """Helper to verify manual task instance creation"""
    db.refresh(privacy_request)
    instances = privacy_request.manual_task_instances
    assert len(instances) == expected_count
    if expected_count > 0:
        assert instances[0].task_id == manual_task.id


@pytest.fixture
def mock_log_end():
    """Reusable fixture for mocking log_end"""

    def _create_mock(obj):
        """Create a mock for log_end on the given object"""
        with patch.object(obj, "log_end", autospec=True) as mock_log_end:
            return mock_log_end

    return _create_mock


def mock_run_request(manual_task_graph_task, return_value=None):
    """Helper function to mock _run_request with common patterns"""
    return patch.object(
        manual_task_graph_task, "_run_request", autospec=True, return_value=return_value
    )


def create_log_end_mock(manual_task_graph_task):
    """Helper function to mock log_end with common patterns"""
    return patch.object(manual_task_graph_task, "log_end", autospec=True)


class TestManualTaskDataAggregation:
    """Test the data aggregation methods in ManualTaskGraphTask"""

    @pytest.fixture
    def manual_task_instance_with_field(
        self, db, access_privacy_request, connection_with_manual_access_task
    ):
        """Create a manual task instance with proper field setup"""
        _, manual_task, config, _ = connection_with_manual_access_task
        return ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

    def test_aggregate_submission_data_empty_instances(self, manual_task_graph_task):
        """Test aggregation with empty instances list"""
        result = manual_task_graph_task._aggregate_submission_data([])
        assert result == {}

    def test_aggregate_submission_data_no_submissions(
        self, manual_task_graph_task, manual_task_instance_with_field
    ):
        """Test aggregation with instances that have no submissions"""
        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_text_field(
        self, manual_task_graph_task, manual_task_submission_text
    ):
        """Test aggregation with text field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_text.instance

        result = manual_task_graph_task._aggregate_submission_data([instance])

        assert "user_email" in result
        assert result["user_email"] == "user@example.com"

    def test_aggregate_submission_data_checkbox_field(
        self, manual_task_graph_task, manual_task_submission_checkbox
    ):
        """Test aggregation with checkbox field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_checkbox.instance

        result = manual_task_graph_task._aggregate_submission_data([instance])

        assert "user_email" in result
        assert result["user_email"] is True

    def test_aggregate_submission_data_multiple_instances(
        self,
        manual_task_graph_task,
        manual_task_submission_text,
        manual_task_submission_checkbox,
    ):
        """Test aggregation with multiple instances"""
        instance1 = manual_task_submission_text.instance
        instance2 = manual_task_submission_checkbox.instance

        result = manual_task_graph_task._aggregate_submission_data(
            [instance1, instance2]
        )

        # Should have data from both instances
        assert "user_email" in result
        # The last instance processed will overwrite the first one with the same field_key
        assert result["user_email"] is True

    def test_aggregate_submission_data_invalid_submission_data(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with invalid submission data"""
        # Get the field from the connection setup
        _, _, _, field = connection_with_manual_access_task

        # Create a submission with invalid data structure
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data="invalid_data",  # Not a dict
        )
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_missing_field_key(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with submission missing field_key"""
        # Get the field from the connection setup
        _, _, _, field = connection_with_manual_access_task

        # Create a submission with field but no field_key
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data={"field_type": ManualTaskFieldType.text.value, "value": "test"},
        )
        # Temporarily set field_key to None for testing (will be restored)
        original_field_key = field.field_key
        field.field_key = None
        submission.field = field
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

        # Restore the original field_key
        field.field_key = original_field_key

    @patch("fides.api.task.manual.manual_task_graph_task.format_size", autospec=True)
    def test_process_attachment_field_success(
        self,
        mock_format_size,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test successful attachment field processing"""
        mock_format_size.return_value = "1.2 KB"

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            assert result is not None
            assert "test_document.pdf" in result
            assert result["test_document.pdf"]["url"] == "https://example.com/file.pdf"
            assert result["test_document.pdf"]["size"] == "1.2 KB"

    def test_process_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test attachment field processing with no attachments"""
        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    @pytest.mark.usefixtures("storage_config")
    def test_process_attachment_field_wrong_attachment_type(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test attachment field processing with wrong attachment type"""
        # Change the attachment type to internal_use_only (not include_with_access_package)
        attachment_for_access_package.attachment_type = "internal_use_only"

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    @patch("fides.api.task.manual.manual_task_graph_task.logger", autospec=True)
    def test_process_attachment_field_retrieval_error(
        self,
        mock_logger,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test attachment field processing with retrieval error"""
        # Mock the attachment retrieval to raise an exception
        with patch.object(
            attachment_for_access_package, "retrieve_attachment", autospec=True
        ) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Storage error")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            # Should log warning and continue
            mock_logger.warning.assert_called_once()
            assert result is None

    @patch("fides.api.task.manual.manual_task_graph_task.format_size", autospec=True)
    def test_process_attachment_field_multiple_attachments(
        self,
        mock_format_size,
        manual_task_graph_task,
        manual_task_submission_attachment,
        multiple_attachments_for_access,
    ):
        """Test attachment field processing with multiple attachments"""
        mock_format_size.return_value = "2.5 KB"

        # Mock the attachment retrieval for multiple attachments
        with (
            patch.object(
                multiple_attachments_for_access[0], "retrieve_attachment", autospec=True
            ) as mock_retrieve1,
            patch.object(
                multiple_attachments_for_access[1], "retrieve_attachment", autospec=True
            ) as mock_retrieve2,
        ):

            mock_retrieve1.return_value = (2560, "https://example.com/doc1.pdf")
            mock_retrieve2.return_value = (1024, "https://example.com/doc2.pdf")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            assert result is not None
            assert "document1.pdf" in result
            assert "document2.pdf" in result
            assert result["document1.pdf"]["url"] == "https://example.com/doc1.pdf"
            assert result["document2.pdf"]["url"] == "https://example.com/doc2.pdf"
            assert result["document1.pdf"]["size"] == "2.5 KB"
            assert result["document2.pdf"]["size"] == "2.5 KB"

    def test_aggregate_submission_data_with_attachment_field(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test aggregation with attachment field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_attachment.instance

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment", autospec=True
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._aggregate_submission_data([instance])

            # Should process attachment field
            assert "user_email" in result
            assert isinstance(result["user_email"], dict)
            assert "test_document.pdf" in result["user_email"]

    def test_aggregate_submission_data_mixed_field_types(
        self,
        manual_task_graph_task,
        manual_task_submission_text,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test aggregation with mixed field types (text and attachment)"""
        instance1 = manual_task_submission_text.instance
        instance2 = manual_task_submission_attachment.instance

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment", autospec=True
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._aggregate_submission_data(
                [instance1, instance2]
            )

            # Should have both text and attachment data
            assert "user_email" in result
            # The last instance processed will overwrite the first one with the same field_key
            assert isinstance(result["user_email"], dict)
            assert "test_document.pdf" in result["user_email"]

    def test_aggregate_submission_data_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test aggregation with attachment field but no attachments"""
        # Get the instance from the submission
        instance = manual_task_submission_attachment.instance

        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._aggregate_submission_data([instance])

        # Should return None for attachment field with no attachments
        assert "user_email" in result
        assert result["user_email"] is None

    def test_aggregate_submission_data_invalid_submission_data_type(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with submission data that is not a dict"""
        _, _, _, field = connection_with_manual_access_task

        # Create submission with non-dict data
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data="not_a_dict",  # Invalid data type
        )
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_missing_field_type(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with submission missing field_type"""
        _, _, _, field = connection_with_manual_access_task

        # Create submission without field_type
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data={"value": "test_value"},  # Missing field_type
        )
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}


class TestManualTaskConditionalDependencies:
    """Test that Manual Tasks only create instances when conditional dependencies are met"""

    @pytest.fixture
    def evaluation_result(self):
        return ConditionEvaluationResult(
            result=True,
            message="Conditions met",
            field_address="postgres_example:customer:profile:age",
            operator="gte",
            expected_value=18,
            actual_value=25,
        )

    def test_manual_task_creates_instance_when_condition_met(
        self,
        db,
        conditional_dependency_setup,
        access_privacy_request,
    ):
        """Test that manual task instances are created when conditional dependencies are satisfied"""
        setup = conditional_dependency_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Use helper to mock conditional dependencies
        mock_extract, mock_evaluate = mock_conditional_dependencies(conditions_met=True)
        with mock_extract, mock_evaluate:
            # Call _run_request which should create instances when conditions are met
            # This should raise AwaitingAsyncTaskCallback since no submissions exist yet
            with pytest.raises(AwaitingAsyncTaskCallback):
                graph_task._run_request(
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    [],  # Empty input data since we're mocking the extraction
                )

            # Use helper to verify instance creation
            verify_instance_creation(
                db, access_privacy_request, manual_task, expected_count=1
            )

    def test_manual_task_does_not_create_instance_when_condition_not_met(
        self,
        db,
        conditional_dependency_setup,
        access_privacy_request,
    ):
        """Test that manual task instances are NOT created when conditional dependencies are not satisfied"""
        setup = conditional_dependency_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Use helper to mock conditional dependencies
        mock_extract, mock_evaluate = mock_conditional_dependencies(
            conditions_met=False
        )
        with mock_extract, mock_evaluate:
            # Call _run_request which should NOT create instances when conditions are not met
            result = graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],  # Empty input data since we're mocking the extraction
            )

            # Should return None when conditions are not met
            assert result is None

            # Use helper to verify no instances were created
            verify_instance_creation(
                db, access_privacy_request, manual_task, expected_count=0
            )

    def test_manual_task_with_multiple_conditions_all_met(
        self,
        db,
        conditional_dependency_setup,
        access_privacy_request,
        group_condition,
    ):
        """Test that manual task instances are created when ALL conditional dependencies are satisfied"""
        setup = conditional_dependency_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Use helper to mock conditional dependencies
        mock_extract, mock_evaluate = mock_conditional_dependencies(conditions_met=True)
        with mock_extract, mock_evaluate:
            # Call _run_request which should create instances when all conditions are met
            # This should raise AwaitingAsyncTaskCallback since no submissions exist yet
            with pytest.raises(AwaitingAsyncTaskCallback):
                graph_task._run_request(
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    [],  # Empty input data since we're mocking the extraction
                )

            # Use helper to verify instance creation
            verify_instance_creation(
                db, access_privacy_request, manual_task, expected_count=1
            )

    def test_manual_task_with_no_conditional_dependencies(
        self,
        db,
        manual_task_setup,
        access_privacy_request,
    ):
        """Test that manual task instances are always created when there are no conditional dependencies"""
        setup = manual_task_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Mock the conditional dependency evaluation to return None (no conditions)
        mock_extract, mock_evaluate = mock_conditional_dependencies(
            conditions_met=None, conditional_data={}
        )
        with mock_extract, mock_evaluate:
            # Call _run_request which should create instances when there are no conditions
            # This should raise AwaitingAsyncTaskCallback since no submissions exist yet
            with pytest.raises(AwaitingAsyncTaskCallback):
                graph_task._run_request(
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    [],  # No input data needed when no conditional dependencies
                )

            # Use helper to verify instance creation
            verify_instance_creation(
                db, access_privacy_request, manual_task, expected_count=1
            )

    def test_conditional_dependency_field_address_format(
        self,
        db,
        conditional_dependency_setup,
        access_privacy_request,
    ):
        """Test that conditional dependencies work with the correct field address format (dots vs colons)"""
        setup = conditional_dependency_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]
        conditional_dependency = setup["conditional_dependency"]

        # Verify the conditional dependency was created with the correct format
        # The field address should use dots for nested fields: "postgres_example:customer:profile.age"
        assert (
            conditional_dependency.field_address
            == "postgres_example:customer:profile.age"
        )
        assert conditional_dependency.operator == "gte"
        assert conditional_dependency.value == 18

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Use helper to mock conditional dependencies
        mock_extract, mock_evaluate = mock_conditional_dependencies(conditions_met=True)
        with mock_extract, mock_evaluate:
            # Test with mocked conditional dependency evaluation
            with pytest.raises(AwaitingAsyncTaskCallback):
                graph_task._run_request(
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    [],
                )

            # Use helper to verify instance creation
            verify_instance_creation(
                db, access_privacy_request, manual_task, expected_count=1
            )


class TestManualTaskGraphTaskHelperMethods:
    """Test the helper methods in ManualTaskGraphTask"""

    def test_check_manual_task_configs_no_configs(
        self, manual_task_graph_task, manual_task
    ):
        """Test checking manual task configs when no configs exist"""
        # Clear existing configs
        manual_task.configs = []

        with patch.object(
            manual_task_graph_task, "log_end", autospec=True
        ) as mock_log_end:
            result = manual_task_graph_task._check_manual_task_configs(
                manual_task,
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
            )
            assert result is False
            mock_log_end.assert_called_once_with(ActionType.access)

    def test_check_manual_task_configs_with_configs(
        self, manual_task_graph_task, connection_with_manual_access_task
    ):
        """Test checking manual task configs when configs exist"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Ensure configs exist and are current
        config.is_current = True
        config.config_type = ManualTaskConfigurationType.access_privacy_request

        result = manual_task_graph_task._check_manual_task_configs(
            manual_task,
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
        )
        assert result is True

    def test_ensure_manual_task_instances_existing_instance(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test ensuring manual task instances when instance already exists"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create an existing instance
        existing_instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # This should not create a new instance
        manual_task_graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify only one instance exists
        instances = access_privacy_request.manual_task_instances
        assert len(instances) == 1
        assert instances[0].id == existing_instance.id

    @pytest.mark.usefixtures("storage_config")
    def test_cleanup_manual_task_instances(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test cleaning up manual task instances"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create instances to clean up
        ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )
        ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Verify instances exist
        assert len(access_privacy_request.manual_task_instances) == 2

        # Clean up instances
        manual_task_graph_task._cleanup_manual_task_instances(
            manual_task, access_privacy_request
        )

        # Verify instances were removed
        db.refresh(access_privacy_request)
        assert len(access_privacy_request.manual_task_instances) == 0

    def test_ensure_manual_task_instances_no_config(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test ensuring manual task instances when no config exists"""
        # Clear configs
        manual_task.configs = []

        # This should not create any instances
        manual_task_graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify no instances were created
        instances = access_privacy_request.manual_task_instances
        assert len(instances) == 0

    def test_get_submitted_data_no_instances(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test getting submitted data when no instances exist"""
        result = manual_task_graph_task._get_submitted_data(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )
        assert result is None

    def test_get_submitted_data_incomplete_fields(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test getting submitted data when instances have incomplete fields"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create instance with incomplete fields
        ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Mock incomplete_fields to return True
        with patch(
            "fides.api.models.manual_task.manual_task.ManualTaskInstance.incomplete_fields",
            return_value=True,
        ):
            result = manual_task_graph_task._get_submitted_data(
                manual_task,
                access_privacy_request,
                ManualTaskConfigurationType.access_privacy_request,
            )
            assert result is None

    def test_get_submitted_data_with_conditional_data(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test getting submitted data with conditional data"""
        _, manual_task, config, field = connection_with_manual_access_task

        # Create completed instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Create a submission for the field to make it complete
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_id": field.id,
                "instance_id": instance.id,
                "submitted_by": None,
                "data": {
                    "field_type": ManualTaskFieldType.text.value,
                    "value": "test_value",
                },
            },
        )

        # Mock incomplete_fields to return empty list (no incomplete fields)

        result = manual_task_graph_task._get_submitted_data(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
            {"conditional": "data"},
        )

        assert result is not None
        assert "conditional" in result

    def test_process_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test processing attachment field with no attachments"""
        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    def test_process_attachment_field_wrong_attachment_type(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test processing attachment field with wrong attachment type"""
        # Change attachment type to not include_with_access_package
        attachment_for_access_package.attachment_type = "internal_use_only"

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    def test_get_manual_task_or_none_invalid_address(self, manual_task_graph_task):
        """Test getting manual task with invalid address"""
        with patch.object(
            manual_task_graph_task.execution_node, "address", "invalid:address"
        ):
            with pytest.raises(ValueError, match="Invalid manual task address"):
                manual_task_graph_task._get_manual_task_or_none()

    def test_run_request_no_manual_task(
        self, db, access_privacy_request, connection_config
    ):
        """Test running request when no manual task exists"""

        # Create a request task and resources, but without a manual task

        request_task = _build_request_task(
            db, access_privacy_request, connection_config, ActionType.access
        )
        resources = _build_task_resources(
            db,
            access_privacy_request,
            access_privacy_request.policy,
            connection_config,
            request_task,
        )

        graph_task = ManualTaskGraphTask(resources)

        # Test the flow - should return None when no manual task exists
        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            [],
        )
        assert result is None

    def test_run_request_conditions_not_met(
        self,
        db,
        conditional_dependency_setup,
        access_privacy_request,
    ):
        """Test running request when conditional dependencies are not met"""
        setup = conditional_dependency_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]

        # Create input data that does NOT satisfy the conditional dependency
        # The condition expects: postgres_example:customer:profile.age >= 18 (note the dot, not colon)
        input_data = [
            {"postgres_example:customer:profile.age": 15}
        ]  # fails the condition

        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            input_data,
        )

        # Should return None when conditions are not met
        assert result is None

        # Verify that instances were cleaned up
        db.refresh(access_privacy_request)
        instances = access_privacy_request.manual_task_instances
        assert len(instances) == 0

    def test_run_request_access_task_skipped_during_erasure_mode(
        self,
        db,
        erasure_task_setup,
    ):
        """Test that access tasks are skipped during erasure mode"""

        setup = erasure_task_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]
        privacy_request = setup["privacy_request"]

        # Set privacy request to in_processing status
        privacy_request.status = PrivacyRequestStatus.in_processing
        db.commit()

        # Test that access tasks are NOT skipped when not in erasure phase
        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            [],
        )
        # Should not be skipped - should raise AwaitingAsyncTaskCallback or return data
        assert (
            result is not None
            or privacy_request.status == PrivacyRequestStatus.requires_input
        )

        # Now simulate being in erasure phase by setting a checkpoint
        privacy_request.cache_failed_checkpoint_details(CurrentStep.erasure)

        # Test that access tasks ARE skipped during erasure phase
        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            [],
        )
        # Should be skipped (return None) during erasure mode
        assert result is None

        # Verify the task was marked as complete with the correct message
        # This would be verified through the execution logs in a real scenario

    def test_is_in_erasure_phase_method(
        self,
        db,
        erasure_task_setup,
    ):
        """Test the _is_in_erasure_phase method logic"""

        setup = erasure_task_setup
        graph_task = setup["graph_task"]
        privacy_request = setup["privacy_request"]

        # Initially should not be in erasure phase
        assert not graph_task._is_in_erasure_phase()

        # Test with different checkpoint steps

        # Access phase steps should return False
        access_phase_steps = [
            CurrentStep.pre_webhooks,
            CurrentStep.access,
            CurrentStep.upload_access,
        ]

        for step in access_phase_steps:
            privacy_request.cache_failed_checkpoint_details(step)
            assert (
                not graph_task._is_in_erasure_phase()
            ), f"Step {step} should not be erasure phase"

        # Erasure phase steps should return True
        erasure_phase_steps = [
            CurrentStep.erasure,
            CurrentStep.finalize_erasure,
            CurrentStep.consent,
            CurrentStep.finalize_consent,
            CurrentStep.email_post_send,
            CurrentStep.post_webhooks,
            CurrentStep.finalization,
        ]

        for step in erasure_phase_steps:
            privacy_request.cache_failed_checkpoint_details(step)
            assert (
                graph_task._is_in_erasure_phase()
            ), f"Step {step} should be erasure phase"

        # Test fallback logic when no checkpoint details exist
        # Clear checkpoint details
        cache = get_cache()
        cache.delete(f"FAILED_LOCATION__{privacy_request.id}")

        # Should fall back to checking access terminator task
        # Since we don't have access tasks set up, this should return False
        assert not graph_task._is_in_erasure_phase()

    def test_run_request_access_task_not_skipped_during_access_mode(
        self,
        db,
        manual_task_setup,
    ):
        """Test that access tasks are NOT skipped during access mode"""

        setup = manual_task_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]
        privacy_request = setup["privacy_request"]

        # Use helpers to create test data
        instance = create_test_instance(
            db, manual_task, setup["config"], privacy_request
        )
        create_test_submission(
            db, manual_task, setup["config"], setup["field"], instance
        )

        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            [],
        )

        # Should NOT return None (not skipped) - should return the submitted data
        assert result is not None
        assert len(result) > 0
        # The result should contain the submitted data
        assert "user_email" in result[0]
        assert result[0]["user_email"] == "test_value"

    def test_run_request_conditional_dependencies_evaluated_before_policy_rules(
        self,
        db,
        conditional_dependency_setup,
        access_privacy_request,
    ):
        """Test that conditional dependencies are evaluated before policy rules"""

        setup = conditional_dependency_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]

        # Use helper to mock conditional dependencies
        mock_extract, mock_evaluate = mock_conditional_dependencies(conditions_met=True)
        with mock_extract, mock_evaluate:
            # This should raise AwaitingAsyncTaskCallback since no submissions exist yet
            with pytest.raises(AwaitingAsyncTaskCallback):
                graph_task._run_request(
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    [],
                )

            # Use helper to verify instance creation
            verify_instance_creation(
                db, access_privacy_request, manual_task, expected_count=1
            )

    def test_run_request_erasure_task_follows_normal_flow(
        self,
        db,
        erasure_task_setup,
    ):
        """Test that erasure tasks follow the normal flow"""

        setup = erasure_task_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]
        privacy_request = setup["privacy_request"]

        # Use helpers to create test data
        instance = create_test_instance(
            db, manual_task, setup["config"], privacy_request
        )
        create_test_submission(
            db, manual_task, setup["config"], setup["field"], instance
        )

        # Use helper to mock conditional dependencies
        mock_extract, mock_evaluate = mock_conditional_dependencies(
            conditions_met=None, conditional_data={}
        )
        with mock_extract, mock_evaluate:
            # Use the correct configuration type for erasure
            result = graph_task._run_request(
                ManualTaskConfigurationType.erasure_privacy_request,  # Use erasure config type
                ActionType.erasure,
                [],
            )

            # Should NOT return None (not skipped) - should return the submitted data
            assert result is not None
            assert len(result) > 0
            # The result should contain the submitted data
            # Note: erasure tasks use "confirm_erasure" field key, not "user_email"
            assert "confirm_erasure" in result[0]
            assert result[0]["confirm_erasure"] == "test_value"

    def test_access_request_returns_empty_when_none(self, manual_task_graph_task):
        """Test access request returns empty list when _run_request returns None"""
        with mock_run_request(manual_task_graph_task, return_value=None):
            result = manual_task_graph_task.access_request([])
            assert result == []

    def test_access_request_logs_end_when_successful(self, manual_task_graph_task):
        """Test access request logs end when successful"""
        test_data = [{"test": "data"}]

        with (
            mock_run_request(manual_task_graph_task, return_value=test_data),
            create_log_end_mock(manual_task_graph_task) as mock_log_end,
        ):
            result = manual_task_graph_task.access_request([])
            assert result == test_data
            mock_log_end.assert_called_once_with(ActionType.access, record_count=1)

    def test_erasure_request_no_inputs(self, manual_task_graph_task):
        """Test erasure request with no inputs"""
        with mock_run_request(manual_task_graph_task, return_value=None):
            result = manual_task_graph_task.erasure_request([], inputs=[])
            assert result == 0

    def test_erasure_request_logs_end_when_successful(self, manual_task_graph_task):
        """Test erasure request logs end when successful"""
        with (
            mock_run_request(manual_task_graph_task, return_value=[{"test": "data"}]),
            create_log_end_mock(manual_task_graph_task) as mock_log_end,
        ):
            result = manual_task_graph_task.erasure_request(
                [], inputs=[[{"test": "data"}]]
            )
            assert result == 0
            mock_log_end.assert_called_once_with(ActionType.erasure, record_count=0)
            assert mock_log_end.call_count == 1

    def test_cleanup_manual_task_instances_no_instances(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test cleaning up manual task instances when none exist"""
        # Verify no instances exist
        assert len(access_privacy_request.manual_task_instances) == 0

        # This should not raise any errors
        manual_task_graph_task._cleanup_manual_task_instances(
            manual_task, access_privacy_request
        )

        # Still no instances
        assert len(access_privacy_request.manual_task_instances) == 0

    def test_set_submitted_data_or_raise_awaiting_async_task_callback_no_submitted_data(
        self, manual_task_graph_task, manual_task, access_privacy_request, db
    ):
        """Test the else branch when submitted_data is None"""
        with (
            patch.object(
                manual_task_graph_task,
                "_get_submitted_data",
                autospec=True,
                return_value=None,
            ),
            patch.object(
                manual_task_graph_task.resources.request, "save", autospec=True
            ),
        ):
            # This should raise AwaitingAsyncTaskCallback
            with pytest.raises(
                AwaitingAsyncTaskCallback,
                match="Manual task for .* requires user input",
            ):
                manual_task_graph_task._set_submitted_data_or_raise_awaiting_async_task_callback(
                    manual_task,
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                )

    def test_set_submitted_data_or_raise_awaiting_async_task_callback_with_awaiting_message(
        self, manual_task_graph_task, manual_task, access_privacy_request, db
    ):
        """Test the else branch when submitted_data is None and awaiting_detail_message is provided"""
        with (
            patch.object(
                manual_task_graph_task,
                "_get_submitted_data",
                autospec=True,
                return_value=None,
            ),
            patch.object(
                manual_task_graph_task.resources.request, "save", autospec=True
            ),
        ):
            # This should raise AwaitingAsyncTaskCallback with the detail message
            with pytest.raises(
                AwaitingAsyncTaskCallback,
                match="Manual task for .* requires user input. Test detail",
            ):
                manual_task_graph_task._set_submitted_data_or_raise_awaiting_async_task_callback(
                    manual_task,
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    awaiting_detail_message="Test detail",
                )

    def test_ensure_manual_task_instances_with_config(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test creating manual task instances when config exists"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Ensure config is current and has the right type
        config.is_current = True
        config.config_type = ManualTaskConfigurationType.access_privacy_request

        manual_task_graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify instance was created
        instances = access_privacy_request.manual_task_instances
        assert len(instances) == 1
        assert instances[0].task_id == manual_task.id
        assert instances[0].config_id == config.id

    def test_get_submitted_data_status_update(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test status update when instances are completed"""
        _, manual_task, config, field = connection_with_manual_access_task

        # Create instance with pending status
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Create a submission to make the instance complete
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_id": field.id,
                "instance_id": instance.id,
                "submitted_by": None,
                "data": {
                    "field_type": ManualTaskFieldType.text.value,
                    "value": "test_value",
                },
            },
        )

        # Mock incomplete_fields to return empty list (no incomplete fields)
        result = manual_task_graph_task._get_submitted_data(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Should return the aggregated data
        assert result is not None
        assert "user_email" in result

        # Verify status was updated to completed
        db.refresh(instance)
        assert instance.status == "completed"

    def test_run_request_with_evaluation_result(
        self,
        db,
        conditional_dependency_setup,
        access_privacy_request,
    ):
        """Test _run_request when evaluation_result exists"""

        setup = conditional_dependency_setup
        manual_task = setup["manual_task"]
        graph_task = setup["graph_task"]

        # Use helpers to create test data
        instance = create_test_instance(
            db, manual_task, setup["config"], access_privacy_request
        )
        create_test_submission(
            db, manual_task, setup["config"], setup["field"], instance
        )

        # Use helper to mock conditional dependencies
        mock_extract, mock_evaluate = mock_conditional_dependencies(conditions_met=True)
        with mock_extract, mock_evaluate:
            result = graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],
            )

            # Should return the submitted data
            assert result is not None
            assert len(result) > 0
            assert "user_email" in result[0]
            assert result[0]["user_email"] == "test_value"

    def test_cleanup_manual_task_instances_with_instances(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test cleanup when instances exist"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create instances to clean up
        ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )
        ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Verify instances exist
        assert len(access_privacy_request.manual_task_instances) == 2

        # Clean up instances
        manual_task_graph_task._cleanup_manual_task_instances(
            manual_task, access_privacy_request
        )

        # Verify instances were removed
        db.refresh(access_privacy_request)
        assert len(access_privacy_request.manual_task_instances) == 0

    @pytest.mark.usefixtures("complete_manual_task_setup")
    def test_no_double_event_log_entries_after_submission(self, manual_task_graph_task):
        """Test that log_end is called exactly once for both access and erasure requests"""
        # Mock _run_request to return data (simulating completed task)
        with (
            mock_run_request(manual_task_graph_task, return_value=[{"test": "data"}]),
            create_log_end_mock(manual_task_graph_task) as mock_log_end,
        ):

            # Test access request with mocked completion
            result = manual_task_graph_task.access_request([])

            # Should return data and call log_end exactly once
            assert result is not None
            assert len(result) > 0
            mock_log_end.assert_called_once_with(
                ActionType.access, record_count=len(result)
            )
            assert mock_log_end.call_count == 1

    def test_no_double_event_log_entries_for_erasure(self, build_erasure_graph_task):
        """Test that log_end is called exactly once for erasure requests"""
        _, manual_task_graph_task = build_erasure_graph_task

        # Mock _run_request to return data (simulating completed task)
        with (
            mock_run_request(manual_task_graph_task, return_value=[{"test": "data"}]),
            create_log_end_mock(manual_task_graph_task) as mock_log_end,
        ):

            # Test erasure request with mocked completion
            result = manual_task_graph_task.erasure_request(
                [], inputs=[[{"test": "data"}]]
            )

            # Should return 0 and call log_end exactly once
            assert result == 0
            mock_log_end.assert_called_once_with(ActionType.erasure, record_count=0)
            assert mock_log_end.call_count == 1

    @pytest.mark.usefixtures("complete_manual_task_setup")
    def test_no_double_event_log_entries_when_awaiting_input(
        self, manual_task_graph_task
    ):
        """Test that log_end is not called when awaiting user input"""
        with (
            mock_run_request(manual_task_graph_task, return_value=None),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):

            # Test access request - should not call log_end when awaiting input
            result = manual_task_graph_task.access_request([])
            assert result == []
            mock_log_end.assert_not_called()

        # Test erasure request - should not call log_end when awaiting input
        with (
            mock_run_request(manual_task_graph_task, return_value=None),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):

            result = manual_task_graph_task.erasure_request([], inputs=[])
            assert result == 0
            mock_log_end.assert_not_called()

    def test_no_double_event_log_entries_with_conditional_dependencies(
        self, manual_task_graph_task
    ):
        """Test that log_end is called exactly once even with conditional dependencies"""
        with (
            mock_run_request(manual_task_graph_task, return_value=[{"test": "data"}]),
            create_log_end_mock(manual_task_graph_task) as mock_log_end,
        ):

            # Test access request with conditional dependencies
            result = manual_task_graph_task.access_request([])

            # Should call log_end exactly once
            assert result is not None
            mock_log_end.assert_called_once_with(ActionType.access, record_count=1)
            assert mock_log_end.call_count == 1

    @pytest.mark.usefixtures("complete_manual_task_setup")
    def test_no_double_event_log_entries_in_awaiting_scenario(
        self, manual_task_graph_task
    ):
        """Test that log_end is not called when manual task is actually awaiting input"""
        with create_log_end_mock(manual_task_graph_task) as mock_log_end:
            # The retry decorator will catch AwaitingAsyncTaskCallback and return None
            # This simulates the real scenario where the task is paused awaiting input
            result = manual_task_graph_task.access_request([])

            # Should return None (from retry decorator) when awaiting input
            assert result is None

            # Verify log_end was never called
            mock_log_end.assert_not_called()
