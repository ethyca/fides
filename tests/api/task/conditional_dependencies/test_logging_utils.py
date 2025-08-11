from unittest.mock import Mock

import pytest

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


def create_leaf_mock(field_address: str, operator: str, expected_value=None):
    """Create a properly configured leaf condition mock"""
    mock = Mock(spec=[])
    mock.field_address = field_address
    mock.operator = operator
    mock.expected_value = expected_value
    return mock


def create_group_mock(logical_operator: str, condition_results=None):
    """Create a properly configured group condition mock"""
    if condition_results is None:
        condition_results = []

    mock = Mock(spec=[])
    mock.logical_operator = logical_operator
    mock.condition_results = condition_results
    return mock


class TestLeafConditionFormatting:
    """Test formatting of individual leaf conditions"""

    def test_format_leaf_condition_with_value(self):
        """Test formatting a leaf condition with an expected value"""
        mock_condition = create_leaf_mock("user:profile:age", ">=", 18)

        result = _format_leaf_condition(mock_condition)
        assert result == "user:profile:age >= 18"

    def test_format_leaf_condition_without_value(self):
        """Test formatting a leaf condition without an expected value"""
        mock_condition = create_leaf_mock("user:profile:active", "==", None)

        result = _format_leaf_condition(mock_condition)
        assert result == "user:profile:active =="


class TestHelperFunctions:
    """Test the new helper functions"""

    def test_is_group_condition_valid(self):
        """Test _is_group_condition with a valid group condition"""
        mock_group = create_group_mock("and", [])
        assert _is_group_condition(mock_group) is True

    def test_is_group_condition_invalid_logical_operator(self):
        """Test _is_group_condition with invalid logical_operator"""
        mock_group = create_group_mock("and", [])
        mock_group.logical_operator = None
        assert _is_group_condition(mock_group) is False

    def test_is_group_condition_invalid_type(self):
        """Test _is_group_condition with non-string logical_operator"""
        mock_group = create_group_mock("and", [])
        mock_group.logical_operator = 123  # Not a string
        assert _is_group_condition(mock_group) is False

    def test_is_group_condition_missing_condition_results(self):
        """Test _is_group_condition without condition_results"""
        mock_group = Mock(spec=[])
        mock_group.logical_operator = "and"
        # Don't set condition_results
        assert _is_group_condition(mock_group) is False

    def test_is_leaf_condition_valid(self):
        """Test _is_leaf_condition with a valid leaf condition"""
        mock_leaf = create_leaf_mock("user:profile:age", ">=", 18)
        assert _is_leaf_condition(mock_leaf) is True

    def test_is_leaf_condition_invalid_field_address(self):
        """Test _is_leaf_condition with invalid field_address"""
        mock_leaf = create_leaf_mock("user:profile:age", ">=", 18)
        mock_leaf.field_address = None
        assert _is_leaf_condition(mock_leaf) is False

    def test_is_leaf_condition_invalid_type(self):
        """Test _is_leaf_condition with non-string field_address"""
        mock_leaf = create_leaf_mock("user:profile:age", ">=", 18)
        mock_leaf.field_address = 123  # Not a string
        assert _is_leaf_condition(mock_leaf) is False

    def test_is_leaf_condition_missing_operator(self):
        """Test _is_leaf_condition without operator"""
        mock_leaf = Mock(spec=[])
        mock_leaf.field_address = "user:profile:age"
        # Don't set operator
        assert _is_leaf_condition(mock_leaf) is False

    def test_is_leaf_condition_mock_object(self):
        """Test _is_leaf_condition with a basic Mock object (should fail)"""
        mock_unknown = Mock(spec=[])
        assert _is_leaf_condition(mock_unknown) is False

    def test_is_group_condition_mock_object(self):
        """Test _is_group_condition with a basic Mock object (should fail)"""
        mock_unknown = Mock(spec=[])
        assert _is_group_condition(mock_unknown) is False

    def test_format_group_condition_success(self):
        """Test _format_group_condition with success=True"""
        mock_group = create_group_mock("and", [])
        mock_condition1 = create_leaf_mock("user:profile:age", ">=", 18)
        mock_condition2 = create_leaf_mock("user:profile:active", "==", True)
        mock_group.condition_results = [mock_condition1, mock_condition2]

        result = _format_group_condition(mock_group, success=True, depth=0)
        assert "All conditions in AND group were met" in result
        assert "user:profile:age >=" in result
        assert "user:profile:active ==" in result

    def test_format_group_condition_failure_with_conditions(self):
        """Test _format_group_condition with success=False and conditions"""
        mock_group = create_group_mock("or", [])
        mock_condition1 = create_leaf_mock("user:profile:age", ">=", 18)
        mock_condition2 = create_leaf_mock("user:profile:active", "==", True)
        mock_group.condition_results = [mock_condition1, mock_condition2]

        result = _format_group_condition(mock_group, success=False, depth=0)
        assert "Failed conditions in OR group" in result
        assert "user:profile:age >=" in result
        assert "user:profile:active ==" in result

    def test_format_group_condition_failure_no_conditions(self):
        """Test _format_group_condition with success=False and no conditions"""
        mock_group = create_group_mock("and", [])

        result = _format_group_condition(mock_group, success=False, depth=0)
        assert "Group condition with AND operator failed" in result

    def test_format_leaf_condition_message_success(self):
        """Test _format_leaf_condition_message with success=True"""
        mock_leaf = create_leaf_mock("user:profile:age", ">=", 18)

        result = _format_leaf_condition_message(mock_leaf, success=True)
        assert "Condition 'user:profile:age >= 18' was met" in result

    def test_format_leaf_condition_message_failure(self):
        """Test _format_leaf_condition_message with success=False"""
        mock_leaf = create_leaf_mock("user:profile:age", ">=", 18)

        result = _format_leaf_condition_message(mock_leaf, success=False)
        assert "Condition 'user:profile:age >= 18' was not met" in result


class TestConditionListFormatting:
    """Test formatting lists of conditions"""

    def test_format_condition_list_with_leaf_conditions(self):
        """Test formatting a list containing only leaf conditions"""
        mock_condition1 = create_leaf_mock("user:profile:age", ">=", 18)
        mock_condition2 = create_leaf_mock("user:profile:active", "==", True)

        results = [mock_condition1, mock_condition2]
        result = _format_condition_list(results, success=True, depth=0)

        assert len(result) == 2
        assert "user:profile:age >=" in result[0]
        assert "user:profile:active ==" in result[1]

    def test_format_condition_list_with_mixed_conditions(self):
        """Test formatting a list with both leaf and group conditions"""
        # Create a nested group condition with empty results (should succeed when success=True)
        mock_nested_group = create_group_mock("or", [])

        # Create a leaf condition
        mock_leaf = create_leaf_mock("user:profile:age", ">=", 18)

        results = [mock_nested_group, mock_leaf]
        result = _format_condition_list(results, success=True, depth=0)

        assert len(result) == 2
        # The nested group should be formatted recursively - empty group succeeds when success=True
        assert "All conditions in OR group were met" in result[0]
        assert "user:profile:age >=" in result[1]


class TestEvaluationMessageFormatting:
    """Test the main evaluation message formatting function"""

    def test_format_leaf_condition_success(self):
        """Test formatting a successful leaf condition"""
        mock_condition = create_leaf_mock("user:profile:age", ">=", 18)

        result = _format_evaluation_message(mock_condition, success=True, depth=0)
        assert "Condition 'user:profile:age >= 18' was met" in result

    def test_format_leaf_condition_failure(self):
        """Test formatting a failed leaf condition"""
        mock_condition = create_leaf_mock("user:profile:age", ">=", 18)

        result = _format_evaluation_message(mock_condition, success=False, depth=0)
        assert "Condition 'user:profile:age >= 18' was not met" in result

    def test_format_group_condition_success(self):
        """Test formatting a successful group condition"""
        mock_group = create_group_mock("and", [])

        # Create leaf conditions for the group
        mock_condition1 = create_leaf_mock("user:profile:age", ">=", 18)
        mock_condition2 = create_leaf_mock("user:profile:active", "==", True)

        mock_group.condition_results = [mock_condition1, mock_condition2]

        result = _format_evaluation_message(mock_group, success=True, depth=0)
        assert "All conditions in AND group were met" in result
        assert "user:profile:age >=" in result
        assert "user:profile:active ==" in result

    def test_format_group_condition_failure(self):
        """Test formatting a failed group condition"""
        mock_group = create_group_mock("or", [])

        # Create leaf conditions for the group
        mock_condition1 = create_leaf_mock("user:profile:age", ">=", 18)
        mock_condition2 = create_leaf_mock("user:profile:active", "==", True)

        mock_group.condition_results = [mock_condition1, mock_condition2]

        result = _format_evaluation_message(mock_group, success=False, depth=0)
        assert "Failed conditions in OR group" in result
        assert "user:profile:age >=" in result
        assert "user:profile:active ==" in result

    def test_format_nested_group_conditions(self):
        """Test formatting deeply nested group conditions"""
        # Create a deeply nested structure
        mock_leaf = create_leaf_mock("user:profile:age", ">=", 18)
        mock_inner_group = create_group_mock("and", [mock_leaf])
        mock_outer_group = create_group_mock("or", [mock_inner_group])

        result = _format_evaluation_message(mock_outer_group, success=True, depth=0)
        assert "All conditions in OR group were met" in result
        assert "All conditions in AND group were met" in result

    def test_depth_limit_protection(self):
        """Test that depth limit prevents infinite recursion"""
        # Create a mock that will cause deep recursion
        mock_deep = create_group_mock("and", [])
        mock_deep.condition_results = [mock_deep]  # Self-referencing

        result = _format_evaluation_message(mock_deep, success=True, depth=110)
        assert result == "Condition evaluation too deeply nested"

    def test_unknown_condition_type(self):
        """Test handling of unknown condition types"""
        # Create a mock with no relevant attributes
        mock_unknown = Mock(spec=[])

        result = _format_evaluation_message(mock_unknown, success=True, depth=0)
        assert result == "Evaluation result details unavailable"


class TestPublicInterface:
    """Test the public interface functions"""

    def test_format_evaluation_success_message(self):
        """Test the success message formatter"""
        mock_condition = create_leaf_mock("user:profile:age", ">=", 18)

        result = format_evaluation_success_message(mock_condition)
        assert "Condition 'user:profile:age >= 18' was met" in result

    def test_format_evaluation_failure_message(self):
        """Test the failure message formatter"""
        mock_condition = create_leaf_mock("user:profile:age", ">=", 18)

        result = format_evaluation_failure_message(mock_condition)
        assert "Condition 'user:profile:age >= 18' was not met" in result

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
        mock_group = create_group_mock("and", [])

        result = _format_evaluation_message(mock_group, success=False, depth=0)
        assert "Group condition with AND operator failed" in result

    def test_leaf_condition_with_special_characters(self):
        """Test formatting leaf conditions with special characters in values"""
        mock_condition = create_leaf_mock(
            "user:profile:email", "contains", "test@example.com"
        )

        result = _format_leaf_condition(mock_condition)
        assert result == "user:profile:email contains test@example.com"
