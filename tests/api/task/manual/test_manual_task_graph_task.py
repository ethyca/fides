from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
    StatusType,
)
from fides.api.schemas.policy import ActionType
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask


@pytest.fixture()
def completed_instance_access(
    db: Session, connection_with_manual_access_task, access_privacy_request
):
    # Create manual task instance
    _, manual_task, manual_config, field = connection_with_manual_access_task
    instance = ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "entity_id": access_privacy_request.id,
            "entity_type": "privacy_request",
            "status": StatusType.pending.value,
        },
    )

    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_id": field.id,
            "instance_id": instance.id,
            "submitted_by": None,  # Use None since submitted_by is nullable
            "data": {
                "field_type": ManualTaskFieldType.text.value,
                "value": "user@example.com",
            },
        },
    )

    # Mark instance as completed
    instance.status = StatusType.completed
    instance.save(db)
    yield instance
    submission.delete(db)
    instance.delete(db)


@pytest.fixture()
def completed_instance_erasure(
    db: Session, connection_with_manual_erasure_task, erasure_privacy_request
):
    _, manual_task, manual_config, field = connection_with_manual_erasure_task
    # Create manual task instance
    instance = ManualTaskInstance.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "entity_id": erasure_privacy_request.id,
            "entity_type": "privacy_request",
            "status": StatusType.pending.value,
        },
    )

    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_id": field.id,
            "instance_id": instance.id,
            "submitted_by": None,  # Use None since submitted_by is nullable
            "data": {
                "field_type": ManualTaskFieldType.checkbox.value,
                "value": True,
            },
        },
    )

    # Mark instance as completed
    instance.status = StatusType.completed
    instance.save(db)
    yield instance
    submission.delete(db)
    instance.delete(db)


class TestManualTaskGraphTaskConditionalDependencies:
    """Test ManualTaskGraphTask functionality with conditional dependencies"""

    @pytest.mark.usefixtures("condition_gt_18")
    def test_extract_conditional_dependency_data_from_inputs_leaf(
        self, db: Session, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test extracting conditional dependency data from inputs for leaf conditions"""
        manual_task, graph_task = build_graph_task
        inputs = [
            [{"user": {"profile": {"age": 25, "name": "John"}}}],
            [{"billing": {"subscription": {"status": "active"}}}],
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_tasks=[manual_task]
        )

        # Verify that the field address value was extracted in nested structure
        assert "user" in conditional_data
        assert "profile" in conditional_data["user"]
        assert "age" in conditional_data["user"]["profile"]
        assert conditional_data["user"]["profile"]["age"] == 25

    @pytest.mark.usefixtures("group_condition")
    def test_extract_conditional_dependency_data_from_inputs_group(
        self, db: Session, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test extracting conditional dependency data from inputs for group conditions"""
        manual_task, graph_task = build_graph_task
        inputs = [
            [{"user": {"profile": {"age": 25, "name": "John"}}}],
            [{"billing": {"subscription": {"status": "active"}}}],
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_tasks=[manual_task]
        )

        # Verify that both field address values were extracted in nested structure
        assert "user" in conditional_data
        assert "profile" in conditional_data["user"]
        assert "age" in conditional_data["user"]["profile"]
        assert conditional_data["user"]["profile"]["age"] == 25

        assert "billing" in conditional_data
        assert "subscription" in conditional_data["billing"]
        assert "status" in conditional_data["billing"]["subscription"]
        assert conditional_data["billing"]["subscription"]["status"] == "active"

    def test_extract_value_from_inputs_nested_path(
        self, db: Session, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test extracting values from nested input paths"""
        _, graph_task = build_graph_task

        # Create mock inputs with nested data
        inputs = [
            [{"user": {"profile": {"age": 30, "location": "NYC"}}}],
            [{"billing": {"subscription": {"status": "active", "plan": "premium"}}}],
        ]

        # Test extracting nested values
        age_value = graph_task._extract_value_from_inputs("user.profile.age", *inputs)
        assert age_value == 30

        status_value = graph_task._extract_value_from_inputs(
            "billing.subscription.status", *inputs
        )
        assert status_value == "active"

        # Test extracting non-existent path
        missing_value = graph_task._extract_value_from_inputs(
            "user.profile.nonexistent", *inputs
        )
        assert missing_value is None

    def test_get_nested_value(
        self, db: Session, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test the _get_nested_value helper method"""
        _, graph_task = build_graph_task

        # Test data with nested structure
        data = {
            "user": {"profile": {"age": 25, "location": "NYC"}},
            "billing": {"subscription": {"status": "active"}},
        }

        # Test successful extraction
        age_value = graph_task._get_nested_value(data, ["user", "profile", "age"])
        assert age_value == 25

        status_value = graph_task._get_nested_value(
            data, ["billing", "subscription", "status"]
        )
        assert status_value == "active"

        # Test extraction of non-existent path
        missing_value = graph_task._get_nested_value(
            data, ["user", "profile", "nonexistent"]
        )
        assert missing_value is None

        # Test extraction with invalid path
        invalid_value = graph_task._get_nested_value(
            data, ["user", "profile", "age", "extra"]
        )
        assert invalid_value is None

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    def test_access_request_with_conditional_dependency_data(
        self,
        db: Session,
        connection_with_manual_access_task,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
    ):
        """Test that access_request includes conditional dependency data in output"""
        # Use existing fixtures:
        # - condition_gt_18 fixture already creates the conditional dependency
        # - manual_task_access_config fixture already creates the config
        connection_config, manual_task, manual_config, field = (
            connection_with_manual_access_task
        )
        _, graph_task = build_graph_task

        # Create manual task instance
        instance = completed_instance_access

        # Create mock inputs with conditional dependency data
        inputs = [
            [{"user": {"profile": {"age": 25, "name": "John"}}}],
        ]

        # Call access_request
        result = graph_task.access_request(*inputs)

        # Verify that the result includes both manual task data and conditional dependency data
        assert len(result) == 1
        result_data = result[0]

        # Should include manual task submission data
        assert "user_email" in result_data
        assert result_data["user_email"] == "user@example.com"

        # Should include conditional dependency data in nested structure
        assert "user" in result_data
        assert "profile" in result_data["user"]
        assert "age" in result_data["user"]["profile"]
        assert result_data["user"]["profile"]["age"] == 25

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_erasure")
    def test_erasure_request_with_conditional_dependency_data(
        self,
        db: Session,
        connection_with_manual_erasure_task,
        build_erasure_graph_task: tuple[ManualTask, ManualTaskGraphTask],
    ):
        """Test that erasure_request includes conditional dependency data in output"""
        # Use existing fixtures:
        # - condition_gt_18 fixture already creates the conditional dependency
        # - completed_instance_erasure fixture already creates the completed instance
        _, graph_task = build_erasure_graph_task

        # Create mock inputs with conditional dependency data
        inputs = [
            [{"user": {"profile": {"age": 25, "name": "John"}}}],
        ]

        # Call erasure_request
        result = graph_task.erasure_request([], inputs=inputs)

        # Verify that the erasure completed successfully
        assert result == 0

    def test_no_conditional_dependencies_handled_gracefully(
        self, db: Session, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test that manual tasks without conditional dependencies work normally"""
        manual_task, graph_task = build_graph_task

        # Create mock inputs
        inputs = [
            [{"user": {"name": "John"}}],
        ]

        # Extract conditional dependency data (should be empty)
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_tasks=[manual_task]
        )

        # Verify that no conditional data was extracted
        assert conditional_data == {}

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    def test_conditional_dependency_data_included_in_submitted_data(
        self,
        db: Session,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        access_privacy_request,
    ):
        """Test that conditional dependency data is included in _get_submitted_data"""
        # Use existing fixtures:
        # - condition_gt_18 fixture already creates the conditional dependency
        # - manual_task_access_config fixture already creates the config
        manual_task, graph_task = build_graph_task

        # Call _get_submitted_data with conditional data
        conditional_data = {
            "user": {"profile": {"age": 25}},
            "billing": {"subscription": {"status": "active"}},
        }
        submitted_data = graph_task._get_submitted_data(
            db,
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
            conditional_data=conditional_data,
        )

        # Verify that the result includes both manual task data and conditional dependency data
        assert submitted_data is not None
        assert "user_email" in submitted_data
        assert submitted_data["user_email"] == "user@example.com"
        assert "user" in submitted_data
        assert "profile" in submitted_data["user"]
        assert "age" in submitted_data["user"]["profile"]
        assert submitted_data["user"]["profile"]["age"] == 25
        assert "billing" in submitted_data
        assert "subscription" in submitted_data["billing"]
        assert "status" in submitted_data["billing"]["subscription"]
        assert submitted_data["billing"]["subscription"]["status"] == "active"

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    def test_conditional_dependency_evaluation_with_regular_task_data(
        self,
        db: Session,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        access_privacy_request,
    ):
        """Test that manual tasks evaluate conditional dependencies using data from regular tasks"""
        manual_task, graph_task = build_graph_task

        # Debug: Check what conditional dependencies are set up
        from fides.api.models.manual_task.conditional_dependency import (
            ManualTaskConditionalDependency,
        )

        conditional_deps = (
            db.query(ManualTaskConditionalDependency)
            .filter(ManualTaskConditionalDependency.manual_task_id == manual_task.id)
            .all()
        )
        print(f"Manual task ID: {manual_task.id}")
        print(
            f"Conditional dependencies: {[(d.field_address, d.operator, d.value) for d in conditional_deps]}"
        )

        # Test with data that satisfies the condition (age >= 18)
        inputs_satisfying_condition = [
            [{"user": {"profile": {"age": 25, "name": "John"}}}],
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_satisfying_condition, manual_tasks=[manual_task]
        )

        # Debug: Print the conditional data
        print(f"Extracted conditional data: {conditional_data}")

        # Evaluate conditional dependencies
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )

        # Debug: Print the evaluation result
        print(f"Should execute: {should_execute}")

        # Debug: Check what the root condition looks like
        from fides.api.models.manual_task.conditional_dependency import (
            ManualTaskConditionalDependency,
        )

        root_condition = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task.id
        )
        print(f"Root condition: {root_condition}")
        if root_condition:
            print(f"Root condition type: {type(root_condition)}")
            if hasattr(root_condition, "field_address"):
                print(f"Root condition field_address: {root_condition.field_address}")
                print(f"Root condition operator: {root_condition.operator}")
                print(f"Root condition value: {root_condition.value}")

        # Should execute because age (25) >= 18
        assert should_execute is True

        # Test with data that doesn't satisfy the condition (age < 18)
        inputs_not_satisfying_condition = [
            [{"user": {"profile": {"age": 15, "name": "John"}}}],
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_not_satisfying_condition, manual_tasks=[manual_task]
        )

        # Evaluate conditional dependencies
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )

        # Should not execute because age (15) < 18
        assert should_execute is False

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    def test_manual_task_execution_with_conditional_dependencies(
        self,
        db: Session,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
    ):
        """Test that manual tasks only execute when conditional dependencies are satisfied"""
        manual_task, graph_task = build_graph_task

        # Test with data that satisfies the condition
        inputs_satisfying_condition = [
            [{"user": {"profile": {"age": 25, "name": "John"}}}],
        ]

        # Call access_request with satisfying data
        result = graph_task.access_request(*inputs_satisfying_condition)

        # Should return data because condition is satisfied
        assert len(result) == 1
        result_data = result[0]
        assert "user_email" in result_data
        assert result_data["user_email"] == "user@example.com"

        # Test with data that doesn't satisfy the condition
        inputs_not_satisfying_condition = [
            [{"user": {"profile": {"age": 15, "name": "John"}}}],
        ]

        # Call access_request with non-satisfying data
        result = graph_task.access_request(*inputs_not_satisfying_condition)

        # Should return empty list because condition is not satisfied
        assert len(result) == 0


class TestManualTaskDataAggregation:
    """Test the data aggregation methods in ManualTaskGraphTask"""

    @pytest.fixture
    def manual_task_instance_with_field(
        self, db, access_privacy_request, connection_with_manual_access_task
    ):
        """Create a manual task instance with proper field setup"""
        _, manual_task, config, field = connection_with_manual_access_task
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
        _, _, config, field = connection_with_manual_access_task

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
        _, _, config, field = connection_with_manual_access_task

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

    @patch("fides.api.task.manual.manual_task_graph_task.format_size")
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

    @patch("fides.api.task.manual.manual_task_graph_task.logger")
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
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Storage error")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            # Should log warning and continue
            mock_logger.warning.assert_called_once()
            assert result is None

    @patch("fides.api.task.manual.manual_task_graph_task.format_size")
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
                multiple_attachments_for_access[0], "retrieve_attachment"
            ) as mock_retrieve1,
            patch.object(
                multiple_attachments_for_access[1], "retrieve_attachment"
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
            attachment_for_access_package, "retrieve_attachment"
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
            attachment_for_access_package, "retrieve_attachment"
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
