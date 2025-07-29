from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
    StatusType,
)
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependencyType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
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
        self, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test extracting conditional dependency data from inputs for leaf conditions"""
        manual_task, graph_task = build_graph_task
        # Update inputs to match the expected input_keys format
        # The parent's pre_process_input_data expects inputs to correspond to input_keys
        inputs = [
            [{"profile": {"age": 25, "name": "John"}}],  # postgres_example:customer
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_task=manual_task
        )

        # Verify that the field address value was extracted in nested structure
        assert "profile" in conditional_data
        assert "age" in conditional_data["profile"]
        assert conditional_data["profile"]["age"] == 25

    @pytest.mark.usefixtures("group_condition")
    def test_extract_conditional_dependency_data_from_inputs_group(
        self, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test extracting conditional dependency data from inputs for group conditions"""
        manual_task, graph_task = build_graph_task
        # Update inputs to match the expected input_keys format
        inputs = [
            [{"profile": {"age": 25, "name": "John"}}],  # postgres_example:customer
            [{"subscription": {"status": "active"}}],  # postgres_example:payment_card
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_task=manual_task
        )

        # Verify that both field address values were extracted in nested structure
        assert "profile" in conditional_data
        assert "age" in conditional_data["profile"]
        assert conditional_data["profile"]["age"] == 25

        assert "subscription" in conditional_data
        assert "status" in conditional_data["subscription"]
        assert conditional_data["subscription"]["status"] == "active"

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    def test_access_request_with_conditional_dependency_data(
        self,
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
            [{"profile": {"age": 25, "name": "John"}}],
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
        assert "profile" in result_data
        assert "age" in result_data["profile"]
        assert result_data["profile"]["age"] == 25

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_erasure")
    def test_erasure_request_with_conditional_dependency_data(
        self,
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
            [{"profile": {"age": 25, "name": "John"}}],
        ]

        # Call erasure_request
        result = graph_task.erasure_request([], inputs=inputs)

        # Verify that the erasure completed successfully
        assert result == 0

    def test_no_conditional_dependencies_handled_gracefully(
        self, build_graph_task: tuple[ManualTask, ManualTaskGraphTask]
    ):
        """Test that manual tasks without conditional dependencies work normally"""
        manual_task, graph_task = build_graph_task

        # When there are no conditional dependencies, there are no input keys
        # So we should pass empty input data
        inputs = []

        # Extract conditional dependency data (should be empty)
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_task=manual_task
        )

        # Verify that no conditional data was extracted
        assert conditional_data == {}

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
            [{"profile": {"age": 25, "name": "John"}}],
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_satisfying_condition, manual_task=manual_task
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
            [{"profile": {"age": 15, "name": "John"}}],
        ]

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_not_satisfying_condition, manual_task=manual_task
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
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
    ):
        """Test that manual tasks only execute when conditional dependencies are satisfied"""
        manual_task, graph_task = build_graph_task

        # Test with data that satisfies the condition
        inputs_satisfying_condition = [
            [{"profile": {"age": 25, "name": "John"}}],
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
            [{"profile": {"age": 15, "name": "John"}}],
        ]

        # Call access_request with non-satisfying data
        result = graph_task.access_request(*inputs_not_satisfying_condition)

        # Should return empty list because condition is not satisfied
        assert len(result) == 0
