from fides.api.task.conditional_dependencies.logging_utils import (
    _format_condition_list,
    _format_evaluation_message,
    _format_group_condition,
    _format_leaf_condition,
    _format_leaf_condition_message,
    _is_group_condition,
    _is_leaf_condition,
    format_evaluation_failure_message,
    format_evaluation_success_message,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionEvaluationResult,
    GroupEvaluationResult,
    GroupOperator,
    Operator,
)


def create_leaf_result(
    field_address: str,
    operator: Operator,
    expected_value=None,
    actual_value=None,
    result: bool = True,
    message: str = None,
):
    """Create a properly configured leaf condition evaluation result"""
    if message is None:
        message = f"Condition '{field_address} {operator} {expected_value}' evaluated to {result}"

    return ConditionEvaluationResult(
        field_address=field_address,
        operator=operator,
        expected_value=expected_value,
        actual_value=actual_value or expected_value,
        result=result,
        message=message,
    )


def create_group_result(
    logical_operator: GroupOperator, condition_results=None, result: bool = True
):
    """Create a properly configured group condition evaluation result"""
    if condition_results is None:
        condition_results = []

    return GroupEvaluationResult(
        logical_operator=logical_operator,
        condition_results=condition_results,
        result=result,
    )


class TestLeafConditionFormatting:
    """Test formatting of individual leaf conditions"""

    def test_format_leaf_condition_with_value(self):
        """Test formatting a leaf condition with an expected value"""
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)

        result = _format_leaf_condition(leaf_condition)
        assert result == "user:profile:age gte 18"

    def test_format_leaf_condition_without_value(self):
        """Test formatting a leaf condition without an expected value"""
        leaf_condition = create_leaf_result("user:profile:active", Operator.eq, None)

        result = _format_leaf_condition(leaf_condition)
        assert result == "user:profile:active eq"


class TestHelperFunctions:
    """Test the new helper functions"""

    def test_is_group_condition_valid(self):
        """Test _is_group_condition with a valid group condition"""
        group_result = create_group_result(GroupOperator.and_, [])
        assert _is_group_condition(group_result) is True

    def test_is_group_condition_invalid_logical_operator(self):
        """Test _is_group_condition with invalid logical_operator"""
        # Create a dict that looks like a group but has invalid logical_operator
        invalid_group = {
            "logical_operator": None,
            "condition_results": [],
            "result": True,
        }
        assert _is_group_condition(invalid_group) is False

    def test_is_group_condition_invalid_type(self):
        """Test _is_group_condition with non-string logical_operator"""
        # Create a dict that looks like a group but has invalid logical_operator type
        invalid_group = {
            "logical_operator": 123,  # Not a string
            "condition_results": [],
            "result": True,
        }
        assert _is_group_condition(invalid_group) is False

    def test_is_group_condition_missing_condition_results(self):
        """Test _is_group_condition without condition_results"""
        # Create a dict that looks like a group but is missing condition_results
        invalid_group = {
            "logical_operator": "and",
            "result": True,
            # Missing condition_results
        }
        assert _is_group_condition(invalid_group) is False

    def test_is_group_condition_with_group_operator_enum(self):
        """Test _is_group_condition with GroupOperator enum values"""
        group_result = create_group_result(GroupOperator.and_, [])
        assert _is_group_condition(group_result) is True

        group_result = create_group_result(GroupOperator.or_, [])
        assert _is_group_condition(group_result) is True

    def test_is_leaf_condition_valid(self):
        """Test _is_leaf_condition with a valid leaf condition"""
        leaf_result = create_leaf_result("user:profile:age", Operator.gte, 18)
        assert _is_leaf_condition(leaf_result) is True

    def test_is_leaf_condition_invalid_field_address(self):
        """Test _is_leaf_condition with invalid field_address"""
        # Create a dict that looks like a leaf but has invalid field_address
        invalid_leaf = {
            "field_address": None,
            "operator": "gte",
            "expected_value": 18,
            "actual_value": 18,
            "result": True,
            "message": "test",
        }
        assert _is_leaf_condition(invalid_leaf) is False

    def test_is_leaf_condition_invalid_type(self):
        """Test _is_leaf_condition with non-string field_address"""
        # Create a dict that looks like a leaf but has invalid field_address type
        invalid_leaf = {
            "field_address": 123,  # Not a string
            "operator": "gte",
            "expected_value": 18,
            "actual_value": 18,
            "result": True,
            "message": "test",
        }
        assert _is_leaf_condition(invalid_leaf) is False

    def test_is_leaf_condition_missing_operator(self):
        """Test _is_leaf_condition without operator"""
        # Create a dict that looks like a leaf but is missing operator
        invalid_leaf = {
            "field_address": "user:profile:age",
            "expected_value": 18,
            "actual_value": 18,
            "result": True,
            "message": "test",
            # Missing operator
        }
        assert _is_leaf_condition(invalid_leaf) is False

    def test_is_leaf_condition_with_operator_enum(self):
        """Test _is_leaf_condition with Operator enum values"""
        leaf_result = create_leaf_result("user:profile:age", Operator.gte, 18)
        assert _is_leaf_condition(leaf_result) is True

        leaf_result = create_leaf_result("user:profile:active", Operator.eq, True)
        assert _is_leaf_condition(leaf_result) is True

        leaf_result = create_leaf_result("user:profile:email", Operator.exists, None)
        assert _is_leaf_condition(leaf_result) is True

        leaf_result = create_leaf_result(
            "user:profile:roles", Operator.list_contains, ["admin", "user"]
        )
        assert _is_leaf_condition(leaf_result) is True

    def test_is_leaf_condition_invalid_object(self):
        """Test _is_leaf_condition with an invalid object (should fail)"""
        invalid_object = {"not_a_leaf": "field"}
        assert _is_leaf_condition(invalid_object) is False

    def test_is_group_condition_invalid_object(self):
        """Test _is_group_condition with an invalid object (should fail)"""
        invalid_object = {"not_a_group": "field"}
        assert _is_group_condition(invalid_object) is False

    def test_format_group_condition_success(self):
        """Test _format_group_condition with success=True"""
        leaf_condition1 = create_leaf_result("user:profile:age", Operator.gte, 18)
        leaf_condition2 = create_leaf_result("user:profile:active", Operator.eq, True)
        group_result = create_group_result(
            GroupOperator.and_, [leaf_condition1, leaf_condition2]
        )

        result = _format_group_condition(group_result, success=True, depth=0)
        assert "All conditions in AND group were met" in result
        assert "user:profile:age gte 18" in result
        assert "user:profile:active eq" in result

    def test_format_group_condition_failure_with_conditions(self):
        """Test _format_group_condition with success=False and conditions"""
        leaf_condition1 = create_leaf_result("user:profile:age", Operator.gte, 18)
        leaf_condition2 = create_leaf_result("user:profile:active", Operator.eq, True)
        group_result = create_group_result(
            GroupOperator.or_, [leaf_condition1, leaf_condition2]
        )

        result = _format_group_condition(group_result, success=False, depth=0)
        assert "Failed conditions in OR group" in result
        assert "user:profile:age gte 18" in result
        assert "user:profile:active eq" in result

    def test_format_group_condition_failure_no_conditions(self):
        """Test _format_group_condition with success=False and no conditions"""
        group_result = create_group_result(GroupOperator.and_, [])

        result = _format_group_condition(group_result, success=False, depth=0)
        assert "Group condition with AND operator failed" in result

    def test_format_leaf_condition_message_success(self):
        """Test _format_leaf_condition_message with success=True"""
        leaf_result = create_leaf_result("user:profile:age", Operator.gte, 18)

        result = _format_leaf_condition_message(leaf_result, success=True)
        assert "Condition 'user:profile:age gte 18' was met" in result

    def test_format_leaf_condition_message_failure(self):
        """Test _format_leaf_condition_message with success=False"""
        leaf_result = create_leaf_result("user:profile:age", Operator.gte, 18)

        result = _format_leaf_condition_message(leaf_result, success=False)
        assert "Condition 'user:profile:age gte 18' was not met" in result


class TestConditionListFormatting:
    """Test formatting lists of conditions"""

    def test_format_condition_list_with_leaf_conditions(self):
        """Test formatting a list containing only leaf conditions"""
        leaf_condition1 = create_leaf_result("user:profile:age", Operator.gte, 18)
        leaf_condition2 = create_leaf_result("user:profile:active", Operator.eq, True)

        results = [leaf_condition1, leaf_condition2]
        result = _format_condition_list(results, success=True, depth=0)

        assert len(result) == 2
        assert "user:profile:age gte 18" in result[0]
        assert "user:profile:active eq" in result[1]

    def test_format_condition_list_with_mixed_conditions(self):
        """Test formatting a list with both leaf and group conditions"""
        # Create a nested group condition with empty results (should succeed when success=True)
        nested_group = create_group_result(GroupOperator.or_, [])

        # Create a leaf condition
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)

        results = [nested_group, leaf_condition]
        result = _format_condition_list(results, success=True, depth=0)

        assert len(result) == 2
        # The nested group should be formatted recursively - empty group succeeds when success=True
        assert "All conditions in OR group were met" in result[0]
        assert "user:profile:age gte 18" in result[1]

    def test_format_condition_list_with_unknown_condition_type(self):
        """Test formatting a list containing an unknown condition type (neither leaf nor group)"""
        # Create a leaf condition
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)

        # Create an unknown object that's neither leaf nor group
        unknown_condition = {"not_a_condition": "field", "type": "unknown"}

        results = [leaf_condition, unknown_condition]
        result = _format_condition_list(results, success=True, depth=0)

        # Should only format the leaf condition, unknown condition should be ignored
        assert len(result) == 1
        assert "user:profile:age gte 18" in result[0]


class TestEvaluationMessageFormatting:
    """Test the main evaluation message formatting function"""

    def test_format_leaf_condition_success(self):
        """Test formatting a successful leaf condition"""
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)

        result = _format_evaluation_message(leaf_condition, success=True, depth=0)
        assert "Condition 'user:profile:age gte 18' was met" in result

    def test_format_leaf_condition_failure(self):
        """Test formatting a failed leaf condition"""
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)

        result = _format_evaluation_message(leaf_condition, success=False, depth=0)
        assert "Condition 'user:profile:age gte 18' was not met" in result

    def test_format_group_condition_success(self):
        """Test formatting a successful group condition"""
        # Create leaf conditions for the group
        leaf_condition1 = create_leaf_result("user:profile:age", Operator.gte, 18)
        leaf_condition2 = create_leaf_result("user:profile:active", Operator.eq, True)

        group_result = create_group_result(
            GroupOperator.and_, [leaf_condition1, leaf_condition2]
        )

        result = _format_evaluation_message(group_result, success=True, depth=0)
        assert "All conditions in AND group were met" in result
        assert "user:profile:age gte 18" in result
        assert "user:profile:active eq" in result

    def test_format_group_condition_failure(self):
        """Test formatting a failed group condition"""
        # Create leaf conditions for the group
        leaf_condition1 = create_leaf_result("user:profile:age", Operator.gte, 18)
        leaf_condition2 = create_leaf_result("user:profile:active", Operator.eq, True)

        group_result = create_group_result(
            GroupOperator.or_, [leaf_condition1, leaf_condition2]
        )

        result = _format_evaluation_message(group_result, success=False, depth=0)
        assert "Failed conditions in OR group" in result
        assert "user:profile:age gte 18" in result
        assert "user:profile:active eq" in result

    def test_format_nested_group_conditions(self):
        """Test formatting deeply nested group conditions"""
        # Create a deeply nested structure
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)
        inner_group = create_group_result(GroupOperator.and_, [leaf_condition])
        outer_group = create_group_result(GroupOperator.or_, [inner_group])

        result = _format_evaluation_message(outer_group, success=True, depth=0)
        assert "All conditions in OR group were met" in result
        assert "All conditions in AND group were met" in result

    def test_depth_limit_protection(self):
        """Test that depth limit prevents infinite recursion"""
        # Create a group that will cause deep recursion
        deep_group = create_group_result(GroupOperator.and_, [])
        # Create a self-referencing structure by setting condition_results to contain itself
        deep_group.condition_results = [deep_group]

        result = _format_evaluation_message(deep_group, success=True, depth=110)
        assert result == "Condition evaluation too deeply nested"

    def test_unknown_condition_type(self):
        """Test handling of unknown condition types"""
        # Create an object with no relevant attributes
        unknown_object = {"not_a_condition": "field"}

        result = _format_evaluation_message(unknown_object, success=True, depth=0)
        assert result == "Evaluation result details unavailable"


class TestPublicInterface:
    """Test the public interface functions"""

    def test_format_evaluation_success_message(self):
        """Test the success message formatter"""
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)

        result = format_evaluation_success_message(leaf_condition)
        assert "Condition 'user:profile:age gte 18' was met" in result

    def test_format_evaluation_failure_message(self):
        """Test the failure message formatter"""
        leaf_condition = create_leaf_result("user:profile:age", Operator.gte, 18)

        result = format_evaluation_failure_message(leaf_condition)
        assert "Condition 'user:profile:age gte 18' was not met" in result

    def test_format_evaluation_success_message_none(self):
        """Test success message formatter with None input"""
        result = format_evaluation_success_message(None)
        assert result == "No conditional dependencies to evaluate."

    def test_format_evaluation_failure_message_none(self):
        """Test failure message formatter with None input"""
        result = format_evaluation_failure_message(None)
        assert result == "No conditional dependencies to evaluate."


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_condition_list(self):
        """Test formatting an empty list of conditions"""
        result = _format_condition_list([], success=True, depth=0)
        assert result == []

    def test_group_with_empty_results(self):
        """Test formatting a group with no condition results"""
        group_result = create_group_result(GroupOperator.and_, [])

        result = _format_evaluation_message(group_result, success=False, depth=0)
        assert "Group condition with AND operator failed" in result

    def test_leaf_condition_with_special_characters(self):
        """Test formatting leaf conditions with special characters in values"""
        leaf_condition = create_leaf_result(
            "user:profile:email", Operator.contains, "test@example.com"
        )

        result = _format_leaf_condition(leaf_condition)
        assert result == "user:profile:email contains test@example.com"
