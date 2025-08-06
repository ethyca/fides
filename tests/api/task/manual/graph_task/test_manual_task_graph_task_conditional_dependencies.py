from typing import Any

import pytest
from pytest import param
from sqlalchemy.orm import Session

from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
    StatusType,
)
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
)
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
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
    ):
        """Test that access_request includes conditional dependency data in output"""
        _, graph_task = build_graph_task
        inputs = [
            [{"profile": {"age": 25, "name": "John"}}],
        ]
        result = graph_task.access_request(*inputs)

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
        build_erasure_graph_task: tuple[ManualTask, ManualTaskGraphTask],
    ):
        """Test that erasure_request includes conditional dependency data in output"""
        _, graph_task = build_erasure_graph_task
        inputs = [
            [{"profile": {"age": 25, "name": "John"}}],
        ]
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

    @pytest.mark.usefixtures("condition_gt_18")
    @pytest.mark.parametrize(
        "test_input,expected_value",
        [
            param(
                [{"profile": {"age": None, "name": "John"}}],
                None,
                id="explicitly None value",
            ),
            param(
                [{"profile": {"age": 0, "name": "John"}}],
                0,
                id="falsy value (zero)",
            ),
            param(
                [{"profile": {"name": "John"}}],
                None,
                id="missing field",
            ),
            param(
                [{"profile": {"age": False, "name": "John"}}],
                False,
                id="False value",
            ),
            param(
                [{"profile": {"age": "", "name": "John"}}],
                "",
                id="empty string value",
            ),
        ],
    )
    def test_extract_conditional_dependency_data_with_various_values(
        self,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        test_input: list,
        expected_value: Any,
    ):
        """Test that conditional dependency extraction includes fields with various values"""
        manual_task, graph_task = build_graph_task

        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            test_input, manual_task=manual_task
        )

        # Verify that the field is included with the expected value
        assert "profile" in conditional_data, f"profile not found for {test_input}"
        assert "age" in conditional_data["profile"], f"age not found for {test_input}"
        assert (
            conditional_data["profile"]["age"] == expected_value
        ), f"wrong value for {test_input}"

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    @pytest.mark.parametrize(
        "test_input,expected_result",
        [
            param(
                [{"profile": {"age": 25, "name": "John"}}],
                True,
                id="valid value (25 >= 18)",
            ),
            param(
                [{"profile": {"age": 15, "name": "John"}}],
                False,
                id="invalid value (15 < 18)",
            ),
        ],
    )
    def test_conditional_dependency_evaluation_with_regular_task_data(
        self,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        test_input: list,
        expected_result: bool,
    ):
        """Test that manual tasks evaluate conditional dependencies using data from regular tasks"""
        manual_task, graph_task = build_graph_task
        # Extract conditional dependency data
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            test_input, manual_task=manual_task
        )

        # Evaluate conditional dependencies
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )

        assert should_execute is expected_result

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    @pytest.mark.parametrize(
        "test_input,expected_result",
        [
            param(
                [{"profile": {"age": None, "name": "John"}}],
                False,
                id="None value (not >= 18)",
            ),
            param(
                [{"profile": {"age": 0, "name": "John"}}],
                False,
                id="zero value (not >= 18)",
            ),
            param(
                [{"profile": {"name": "John"}}],
                False,
                id="missing field",
            ),
            param(
                [{"profile": {"age": 25, "name": "John"}}],
                True,
                id="valid value (25 >= 18)",
            ),
        ],
    )
    def test_conditional_dependency_evaluation_with_different_value_types(
        self,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        test_input: list,
        expected_result: bool,
    ):
        """Test that conditional dependencies evaluate correctly with None, falsy, and missing values"""
        manual_task, graph_task = build_graph_task

        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            test_input, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    @pytest.mark.parametrize(
        "test_input,expected_result",
        [
            param(
                [{"profile": {"age": "25", "name": "John"}}],
                False,
                id="string value (not >= 18)",
            ),
            param(
                [{"profile": {"age": 25.0, "name": "John"}}],
                True,
                id="float value (25.0 >= 18)",
            ),
            param(
                [{"profile": {"age": [25], "name": "John"}}],
                False,
                id="list value (not >= 18)",
            ),
            param(
                [{"profile": {"age": {"value": 25}, "name": "John"}}],
                False,
                id="dict value (not >= 18)",
            ),
            param(
                [{"profile": {"age": True, "name": "John"}}],
                False,
                id="boolean True (not >= 18)",
            ),
            param(
                [{"profile": {"age": False, "name": "John"}}],
                False,
                id="boolean False (not >= 18)",
            ),
            param(
                [{"profile": {"age": "", "name": "John"}}],
                False,
                id="empty string (not >= 18)",
            ),
            param(
                [{"profile": {"age": -5, "name": "John"}}],
                False,
                id="negative number (not >= 18)",
            ),
            param(
                [{"profile": {"age": 18, "name": "John"}}],
                True,
                id="boundary value (18 >= 18)",
            ),
        ],
    )
    def test_conditional_dependency_evaluation_with_different_data_types(
        self,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        test_input: list,
        expected_result: bool,
    ):
        """Test that conditional dependencies evaluate correctly with different data types"""
        manual_task, graph_task = build_graph_task

        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            test_input, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    @pytest.mark.parametrize(
        "test_input,expected_result",
        [
            param(
                [{"profile": {"age": 999999, "name": "John"}}],
                True,
                id="very large number (999999 >= 18)",
            ),
            param(
                [{"profile": {"age": 0, "name": "John"}}],
                False,
                id="zero (not >= 18)",
            ),
            param(
                [{"profile": {"age": 18.1, "name": "John"}}],
                True,
                id="decimal pass (18.1 >= 18)",
            ),
            param(
                [{"profile": {"age": 17.9, "name": "John"}}],
                False,
                id="decimal fail (17.9 not >= 18)",
            ),
            param(
                [{"profile": {"age": [], "name": "John"}}],
                False,
                id="empty list (not >= 18)",
            ),
            param(
                [{"profile": {"age": {}, "name": "John"}}],
                False,
                id="empty dict (not >= 18)",
            ),
        ],
    )
    def test_conditional_dependency_evaluation_with_edge_cases(
        self,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        test_input: list,
        expected_result: bool,
    ):
        """Test that conditional dependencies handle edge cases correctly"""
        manual_task, graph_task = build_graph_task

        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            test_input, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

    @pytest.mark.usefixtures("condition_gt_18", "completed_instance_access")
    @pytest.mark.parametrize(
        "test_input,expected_result",
        [
            param(
                [{"profile": {"age": {"value": 25, "unit": "years"}, "name": "John"}}],
                False,
                id="nested object (not >= 18)",
            ),
            param(
                [{"profile": {"age": [25, 30, 35], "name": "John"}}],
                False,
                id="list containing field (not >= 18)",
            ),
            param(
                [
                    {
                        "profile": {
                            "age": {
                                "data": {"value": 25, "metadata": {"source": "db"}}
                            },
                            "name": "John",
                        }
                    }
                ],
                False,
                id="deeply nested structure (not >= 18)",
            ),
        ],
    )
    def test_conditional_dependency_evaluation_with_nested_data_structures(
        self,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        test_input: list,
        expected_result: bool,
    ):
        """Test that conditional dependencies handle nested data structures correctly"""
        manual_task, graph_task = build_graph_task

        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            test_input, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

    @pytest.mark.usefixtures("completed_instance_access")
    @pytest.mark.parametrize(
        "operator,value,expected_result",
        [
            param("exists", None, True, id="exists operator"),
            param("not_exists", None, False, id="not_exists operator"),
        ],
    )
    def test_conditional_dependency_evaluation_with_existence_operators(
        self,
        db: Session,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        operator: str,
        value: Any,
        expected_result: bool,
    ):
        """Test that conditional dependencies evaluate correctly with existence operators"""
        manual_task, graph_task = build_graph_task

        # Create a condition that checks if the field exists
        condition = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": "leaf",
                "field_address": "profile.age",
                "operator": operator,
                "value": value,
                "sort_order": 1,
            },
        )

        inputs_with_field = [
            [{"profile": {"age": 25, "name": "John"}}],
        ]
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_with_field, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

        condition.delete(db)

    @pytest.mark.usefixtures("completed_instance_access")
    @pytest.mark.parametrize(
        "operator,value,expected_result",
        [
            param("eq", 25, True, id="eq operator"),
            param("neq", 30, True, id="neq operator"),
        ],
    )
    def test_conditional_dependency_evaluation_with_equality_operators(
        self,
        db: Session,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        operator: str,
        value: Any,
        expected_result: bool,
    ):
        """Test that conditional dependencies evaluate correctly with equality operators"""
        manual_task, graph_task = build_graph_task

        condition = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": "leaf",
                "field_address": "profile.age",
                "operator": operator,
                "value": value,
                "sort_order": 1,
            },
        )

        inputs_matching = [
            [{"profile": {"age": 25, "name": "John"}}],
        ]
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_matching, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

        condition.delete(db)

    @pytest.mark.usefixtures("completed_instance_access")
    @pytest.mark.parametrize(
        "operator,value,expected_result",
        [
            param("list_contains", "admin", True, id="list_contains operator"),
            param("list_contains", "superuser", False, id="list_contains operator"),
            param("not_in_list", "superuser", True, id="not_in_list operator"),
            param("not_in_list", ["user", "admin"], False, id="not_in_list operator"),
        ],
    )
    def test_conditional_dependency_evaluation_with_list_operators(
        self,
        db: Session,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        operator: str,
        value: Any,
        expected_result: bool,
    ):
        """Test that conditional dependencies evaluate correctly with list operators"""
        manual_task, graph_task = build_graph_task

        condition = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": "leaf",
                "field_address": "profile.roles",
                "operator": operator,
                "value": value,
                "sort_order": 1,
            },
        )

        inputs_with_admin_role = [
            [{"profile": {"roles": ["user", "admin", "moderator"], "name": "John"}}],
        ]
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_with_admin_role, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

        condition.delete(db)

    @pytest.mark.usefixtures("completed_instance_access")
    @pytest.mark.parametrize(
        "operator,value,expected_result",
        [
            param("starts_with", "John", True, id="starts_with operator"),
            param("ends_with", "Doe", True, id="ends_with operator"),
            param("contains", "ohn", True, id="contains operator"),
            param("starts_with", "Jane", False, id="starts_with operator"),
            param("ends_with", "Smith", False, id="ends_with operator"),
            param("contains", "xyz", False, id="contains operator"),
        ],
    )
    def test_conditional_dependency_evaluation_with_string_operators(
        self,
        db: Session,
        build_graph_task: tuple[ManualTask, ManualTaskGraphTask],
        operator: str,
        value: str,
        expected_result: bool,
    ):
        """Test that conditional dependencies evaluate correctly with string operators"""
        manual_task, graph_task = build_graph_task

        condition = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": "leaf",
                "field_address": "profile.name",
                "operator": operator,
                "value": value,
                "sort_order": 1,
            },
        )

        inputs_matching = [
            [{"profile": {"name": "John Doe", "age": 25}}],
        ]
        conditional_data = graph_task._extract_conditional_dependency_data_from_inputs(
            *inputs_matching, manual_task=manual_task
        )
        should_execute = graph_task._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        assert should_execute is expected_result

        condition.delete(db)

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
