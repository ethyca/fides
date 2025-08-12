from unittest.mock import Mock

import pytest
from pytest import param
from sqlalchemy.orm import Session

from fides.api.graph.config import FieldPath
from fides.api.task.conditional_dependencies.evaluator import (
    ConditionEvaluationError,
    ConditionEvaluator,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


class TestConditionEvaluator:
    """Test the ConditionEvaluator class"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def evaluator(self, mock_db):
        """Create evaluator instance"""
        return ConditionEvaluator(mock_db)

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return {
            "user": {
                "name": "john_doe",
                "age": 25,
                "email": "john@example.com",
                "active": True,
                "score": 95.5,
                "verified": True,
                "role": "user",
                "billing": {
                    "subscription": {"status": "active", "plan": "premium"},
                    "amount": 99.99,
                },
                "preferences": {"notifications": True, "theme": "dark"},
            },
            "order": {"id": 12345, "total": 150.00, "status": "completed"},
            "missing_field": None,
            "empty_dict": {},
            "nested_empty": {"level1": {"level2": {}}},
        }

    @pytest.fixture
    def mock_fides_collection(self):
        """Mock Fides collection with get_field_value method"""
        collection = Mock(autospec=True)
        collection.get_field_value.return_value = "test_value"
        return collection

    @pytest.fixture
    def mock_fides_data(self, mock_fides_collection):
        """Mock Fides data structure"""
        data = Mock(autospec=True)
        data.get_field_value.return_value = "test_value"
        return data


class TestNestedValueAccess(TestConditionEvaluator):
    """Test nested value access functionality"""

    def test_simple_field_access(self, evaluator, sample_data):
        """Test accessing simple fields"""
        value = evaluator._get_nested_value(sample_data, ["user", "name"])
        assert value == "john_doe"

    def test_deep_nested_access(self, evaluator, sample_data):
        """Test accessing deeply nested fields"""
        value = evaluator._get_nested_value(
            sample_data, ["user", "billing", "subscription", "status"]
        )
        assert value == "active"

    @pytest.mark.parametrize(
        "keys,description",
        [
            param(
                ["user", "nonexistent"], "non-existent field", id="non-existent field"
            ),
            param(
                ["user", "billing", "nonexistent"],
                "non-existent deeply nested field",
                id="non-existent deeply nested field",
            ),
            param(["empty_dict", "any_field"], "empty dict", id="empty dict"),
            param(
                ["nested_empty", "level1", "level2", "field_address"],
                "nested empty dict",
                id="nested empty dict",
            ),
            param(["missing_field"], "None field", id="None field"),
        ],
    )
    def test_missing_fields_return_none(
        self, evaluator, sample_data, keys, description
    ):
        """Test accessing missing fields returns None"""
        value = evaluator._get_nested_value(sample_data, keys)
        assert value is None, f"Failed for {description}"

    def test_non_dict_intermediate_returns_none(self, evaluator, sample_data):
        """Test accessing field when intermediate value is not a dict"""
        value = evaluator._get_nested_value(sample_data, ["user", "name", "subfield"])
        assert value is None

    def test_fides_collection_access(self, evaluator, mock_fides_collection):
        """Test accessing Fides collection with get_field_value method"""
        value = evaluator._get_nested_value(mock_fides_collection, ["field_name"])
        assert value == "test_value"
        mock_fides_collection.get_field_value.assert_called_once()

    def test_fides_data_access(self, evaluator, mock_fides_data):
        """Test accessing Fides data structure with get_field_value method"""
        value = evaluator._get_nested_value(
            mock_fides_data, ["field_address", "subfield"]
        )
        assert value == "test_value"
        mock_fides_data.get_field_value.assert_called_once()

    def test_fides_data_fallback_to_dict(self, evaluator):
        """Test Fides data falls back to dict access when get_field_value fails"""
        data = Mock(autospec=True)
        data.get_field_value.side_effect = AttributeError("No such method")
        data.get.return_value = "fallback_value"

        value = evaluator._get_nested_value(data, ["field_address"])
        assert value == "fallback_value"

    def test_empty_keys_returns_data(self, evaluator, sample_data):
        """Test that empty keys list returns the data itself"""
        value = evaluator._get_nested_value(sample_data, [])
        assert value == sample_data

    def test_fides_field_path_creation(self, evaluator, mock_fides_collection):
        """Test that FieldPath is created correctly for Fides access"""
        evaluator._get_nested_value(mock_fides_collection, ["user", "name"])
        # Verify that get_field_value was called with a FieldPath
        mock_fides_collection.get_field_value.assert_called_once()
        call_args = mock_fides_collection.get_field_value.call_args[0][0]
        assert isinstance(call_args, FieldPath)
        assert call_args.levels == ("user", "name")


class TestOperatorEvaluation(TestConditionEvaluator):
    """Test operator evaluation"""

    def test_unknown_operator(self, evaluator):
        """Test handling of unknown operator"""
        with pytest.raises(
            ConditionEvaluationError, match="Unknown operator: invalid_operator"
        ):
            evaluator._apply_operator(
                "test_value", "invalid_operator", "expected_value"
            )

    @pytest.mark.parametrize(
        "column_value,operator,user_input_value,expected_result",
        [
            # Test with None values and edge cases
            param(None, Operator.exists, None, False, id="none_exists"),
            param(None, Operator.not_exists, None, True, id="none_not_exists"),
            # Test with empty values
            param("", Operator.eq, "", True, id="empty_eq"),
            param(0, Operator.eq, 0, True, id="zero_eq"),
            param(False, Operator.eq, False, True, id="false_eq"),
            # Test with mixed types that should return False gracefully
            param("string", Operator.lt, 10, False, id="string_lt"),
            param(
                10,
                Operator.starts_with,
                "prefix",
                False,
                id="number_starts_with_string",
            ),
        ],
    )
    def test_operator_edge_cases(
        self, evaluator, column_value, operator, user_input_value, expected_result
    ):
        """Test edge cases for all operators
        This test covers edge cases that could potentially cause issues
        and the defensive programming in our operators
        """
        result = evaluator._apply_operator(column_value, operator, user_input_value)
        assert result == expected_result


class TestLeafConditionEvaluation(TestConditionEvaluator):
    """Test leaf condition evaluation"""

    @pytest.mark.parametrize(
        "field,operator,value,expected_result,description",
        [
            param(
                "user.name",
                Operator.eq,
                "john_doe",
                True,
                "simple string comparison",
                id="simple_string_eq",
            ),
            param(
                "user.billing.subscription.status",
                Operator.eq,
                "active",
                True,
                "nested field comparison",
                id="nested_field_eq",
            ),
            param(
                "user.email",
                Operator.exists,
                None,
                True,
                "exists operator",
                id="exists_operator",
            ),
            param(
                "user.nonexistent",
                Operator.not_exists,
                None,
                True,
                "not_exists operator",
                id="not_exists_operator",
            ),
            param(
                "user.name",
                Operator.eq,
                "wrong_name",
                False,
                "false string comparison",
                id="false_string_eq",
            ),
            param(
                "user.age",
                Operator.gte,
                18,
                True,
                "numeric comparison",
                id="numeric_gte",
            ),
            param(
                "user.score", Operator.gt, 90.0, True, "float comparison", id="float_gt"
            ),
            param(
                "user.active",
                Operator.eq,
                True,
                True,
                "boolean comparison",
                id="boolean_eq",
            ),
            param(
                "user.nonexistent",
                Operator.eq,
                "any_value",
                False,
                "missing field",
                id="missing_field",
            ),
        ],
    )
    def test_leaf_conditions_with_sample_data(
        self,
        evaluator,
        sample_data,
        field,
        operator,
        value,
        expected_result,
        description,
    ):
        """Test various leaf condition scenarios with sample data"""
        condition = ConditionLeaf(field_address=field, operator=operator, value=value)
        result, evaluation_result = evaluator.evaluate_rule(condition, sample_data)
        assert evaluation_result.field_address == field
        assert evaluation_result.operator == operator
        assert evaluation_result.expected_value == value
        assert evaluation_result.result == expected_result
        assert result is expected_result, f"Failed for {description}"


class TestGroupConditionEvaluation(TestConditionEvaluator):
    """Test group condition evaluation"""

    def test_and_group_all_true(self, evaluator, sample_data):
        """Test AND group with all conditions true"""
        group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),
                ConditionLeaf(
                    field_address="user.score", operator=Operator.gt, value=90
                ),
            ],
        )
        result, evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.and_
        assert len(evaluation_result.condition_results) == 3
        assert all(result.result for result in evaluation_result.condition_results)
        assert result is True

    def test_and_group_one_false(self, evaluator, sample_data):
        """Test AND group with one condition false"""
        group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),
                ConditionLeaf(
                    field_address="user.score", operator=Operator.gt, value=100
                ),  # False
            ],
        )
        result, evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.and_
        assert len(evaluation_result.condition_results) == 3
        assert evaluation_result.condition_results[2].result is False
        assert result is False

    def test_or_group_one_true(self, evaluator, sample_data):
        """Test OR group with one condition true"""
        group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.lt, value=18
                ),  # False
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),  # True
                ConditionLeaf(
                    field_address="user.score", operator=Operator.lt, value=90
                ),  # False
            ],
        )
        result, evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.or_
        assert len(evaluation_result.condition_results) == 3
        assert evaluation_result.condition_results[1].result is True
        assert result is True

    def test_or_group_all_false(self, evaluator, sample_data):
        """Test OR group with all conditions false"""
        group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.lt, value=18
                ),  # False
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=False
                ),  # False
                ConditionLeaf(
                    field_address="user.score", operator=Operator.lt, value=90
                ),  # False
            ],
        )
        result, evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.or_
        assert len(evaluation_result.condition_results) == 3
        assert not any(result.result for result in evaluation_result.condition_results)
        assert result is False

    def test_unknown_logical_operator(self, evaluator, sample_data):
        """Test handling of unknown logical operator"""
        # Test the actual code path by creating a mock group that bypasses validation
        from unittest.mock import Mock

        # Create a mock group that simulates an unknown logical operator
        mock_group = Mock(autospec=True)
        mock_group.logical_operator = "invalid_operator"
        mock_group.conditions = [
            ConditionLeaf(
                field_address="user.name", operator=Operator.eq, value="john_doe"
            ),
        ]

        # This should trigger the unknown logical operator handling
        with pytest.raises(
            ConditionEvaluationError, match="Unknown logical operator: invalid_operator"
        ):
            evaluator._evaluate_group_condition(mock_group, sample_data)


class TestNestedGroupEvaluation(TestConditionEvaluator):
    """Test nested group condition evaluation"""

    def test_nested_and_or_groups(self, evaluator, sample_data):
        """Test nested AND/OR groups"""
        # Structure: (user.age >= 18 AND (user.role = 'admin' OR user.verified = true))
        inner_group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="admin"
                ),
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),
            ],
        )

        outer_group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                inner_group,
            ],
        )

        result, evaluation_result = evaluator.evaluate_rule(outer_group, sample_data)
        # user.age >= 18 is True, user.verified = True is True, so result should be True
        assert result is True

    def test_complex_nested_structure(self, evaluator, sample_data):
        """Test complex nested structure"""
        # Structure: ((A AND B) OR (C AND D)) AND E
        # Where A=user.age>=18, B=user.active=True, C=user.role='admin', D=user.verified=True, E=user.name exists

        inner_group_1 = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),  # True
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        inner_group_2 = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="admin"
                ),  # False
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        middle_group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[inner_group_1, inner_group_2],  # True OR False = True
        )

        outer_group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                middle_group,  # True
                ConditionLeaf(
                    field_address="user.name", operator=Operator.exists
                ),  # True
            ],
        )

        result, evaluation_result = evaluator.evaluate_rule(outer_group, sample_data)
        assert result is True

    def test_deep_nesting(self, evaluator, sample_data):
        """Test very deep nesting"""
        # Create a deeply nested structure: (((A OR B) AND C) OR D) AND E
        deepest = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="admin"
                ),  # False
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        level_2 = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                deepest,  # True (OR of False and True)
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        level_3 = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                level_2,  # True (AND of True and True)
                ConditionLeaf(
                    field_address="user.age", operator=Operator.lt, value=18
                ),  # False
            ],
        )

        outermost = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                level_3,  # True (OR of True and False)
                ConditionLeaf(
                    field_address="user.name", operator=Operator.exists
                ),  # True
            ],
        )

        result, evaluation_result = evaluator.evaluate_rule(outermost, sample_data)
        assert result is True

    def test_mixed_conditions_in_group(self, evaluator, sample_data):
        """Test mixing ConditionLeaf and ConditionGroup in the same group"""
        inner_group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),
                ConditionLeaf(
                    field_address="user.premium", operator=Operator.eq, value=True
                ),
            ],
        )

        mixed_group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.admin", operator=Operator.eq, value=True
                ),
                inner_group,
                ConditionLeaf(
                    field_address="user.moderator", operator=Operator.eq, value=True
                ),
            ],
        )

        assert len(mixed_group.conditions) == 3
        assert isinstance(mixed_group.conditions[0], ConditionLeaf)
        assert isinstance(mixed_group.conditions[1], ConditionGroup)
        assert isinstance(mixed_group.conditions[2], ConditionLeaf)


class TestEdgeCases(TestConditionEvaluator):
    """Test edge cases and error conditions"""

    @pytest.mark.parametrize(
        "data,field_address,operator,expected_result",
        [
            param({}, "any.field_address", Operator.exists, False, id="empty_data"),
            param(None, "any.field_address", Operator.exists, False, id="none_data"),
            param(
                {"user": {"nonexistent": None}},
                "user.nonexistent",
                Operator.exists,
                False,
                id="missing_field",
            ),
            param(
                "sample_data",
                "user.nonexistent",
                Operator.not_exists,
                True,
                id="nested_missing_field_not_exists",
            ),
            param(
                "sample_data",
                "user.nonexistent",
                Operator.exists,
                False,
                id="nested_missing_field_with_exists",
            ),
        ],
    )
    def test_data_edge_cases(
        self, evaluator, data, field_address, operator, expected_result, sample_data
    ):
        """Test evaluation with empty data"""
        condition = ConditionLeaf(field_address=field_address, operator=operator)
        if data == "sample_data":
            data = sample_data

        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert result is expected_result
        assert evaluation_result.result is expected_result

    def test_none_value_comparison(self, evaluator, sample_data):
        """Test comparison with None values"""
        condition = ConditionLeaf(
            field_address="missing_field", operator=Operator.eq, value=None
        )

        result, evaluation_result = evaluator.evaluate_rule(condition, sample_data)
        assert evaluation_result.result is True
        assert result is True

    @pytest.mark.parametrize(
        "field_value,user_input_value,description",
        [
            ("", "", "empty string"),
            (0, 0, "zero value"),
            (False, False, "false boolean"),
        ],
    )
    def test_edge_case_comparisons(
        self, evaluator, field_value, user_input_value, description
    ):
        """Test edge case comparisons (empty string, zero, false)"""
        data = {"field_address": field_value}
        condition = ConditionLeaf(
            field_address="field_address", operator=Operator.eq, value=user_input_value
        )

        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is True
        assert result is True, f"Failed for {description}"


class TestIntegration(TestConditionEvaluator):
    """Test integration scenarios"""

    @pytest.fixture
    def data_set(self):
        return {
            "user": {
                "roles": ["admin", "moderator"],
                "permissions": ["read", "write"],
                "tags": ["premium", "verified"],
                "preferences": {
                    "languages": ["en", "es", "fr"],
                    "categories": ["tech", "business", "finance"],
                },
                "profile": {
                    "interests": ["programming", "reading", "gaming"],
                    "skills": ["python", "javascript", "sql"],
                },
                "subscriptions": {
                    "active": ["premium", "newsletter"],
                    "expired": ["trial"],
                },
                "email": "john.doe@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "domain": "example.com",
                "empty_string": "",
                "age": 25,
                "whitespace": "hello world",
            },
            "order": {
                "status": "completed",
                "items": ["laptop", "mouse", "keyboard", "monitor"],
                "categories": ["electronics", "accessories", "computers"],
            },
        }

    def test_complex_real_world_scenario(self, evaluator, sample_data):
        """Test a complex real-world scenario"""
        # Scenario: User must be 18+, active, and either have admin role OR be verified
        # AND their subscription must be active
        role_or_verified = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="admin"
                ),
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),
            ],
        )

        user_requirements = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),
                role_or_verified,
            ],
        )

        subscription_requirement = ConditionLeaf(
            field_address="user.billing.subscription.status",
            operator=Operator.eq,
            value="active",
        )

        final_rule = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_requirements, subscription_requirement],
        )

        result, evaluation_result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: age=25>=18, active=True, verified=True, subscription=active
        assert evaluation_result.result is True
        assert result is True

    def test_order_processing_scenario(self, evaluator, sample_data):
        """Test order processing scenario"""
        # Scenario: Order must be completed AND total > 100 OR user is premium
        order_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="order.status",
                    operator=Operator.eq,
                    value="completed",
                ),
                ConditionLeaf(
                    field_address="order.total", operator=Operator.gt, value=100.0
                ),
            ],
        )

        user_premium = ConditionLeaf(
            field_address="user.billing.subscription.plan",
            operator=Operator.eq,
            value="premium",
        )

        final_rule = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[order_condition, user_premium],
        )

        result, evaluation_result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: order.status=completed, order.total=150>100
        assert evaluation_result.result is True
        assert result is True

    def test_fides_reference_scenario(self, evaluator, mock_fides_data):
        """Test scenario using Fides reference structures"""
        # Test that the evaluator works with Fides data structures
        condition = ConditionLeaf(
            field_address="customer.email", operator=Operator.eq, value="test_value"
        )

        result, evaluation_result = evaluator.evaluate_rule(condition, mock_fides_data)
        assert evaluation_result.result is True
        assert result is True

    def test_list_operators_integration(self, evaluator, data_set):
        """Test integration of list operators in complex scenarios"""
        data = data_set

        # Test list_contains operator - check if user.roles contains "admin"
        condition = ConditionLeaf(
            field_address="user.roles", operator=Operator.list_contains, value="admin"
        )
        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is True
        assert result is True  # "admin" is in the user.roles list

        # Test not_in_list operator
        condition = ConditionLeaf(
            field_address="user.roles",
            operator=Operator.not_in_list,
            value=["guest", "anonymous"],
        )
        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is True
        assert result is True  # "admin" and "moderator" are not in the excluded list

        # Test list_contains operator with permissions
        condition = ConditionLeaf(
            field_address="user.permissions",
            operator=Operator.list_contains,
            value="write",
        )
        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is True
        assert result is True  # "write" is in the permissions list

    def test_complex_list_condition_group(self, evaluator, data_set):
        """Test complex condition group using list operators"""
        data = data_set

        # Complex condition: (user has admin role OR user has write permission) AND order is completed
        role_condition = ConditionLeaf(
            field_address="user.roles", operator=Operator.list_contains, value="admin"
        )

        permission_condition = ConditionLeaf(
            field_address="user.permissions",
            operator=Operator.list_contains,
            value="write",
        )

        order_condition = ConditionLeaf(
            field_address="order.status", operator=Operator.eq, value="completed"
        )

        role_or_permission = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[role_condition, permission_condition],
        )

        final_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[role_or_permission, order_condition],
        )

        result, evaluation_result = evaluator.evaluate_rule(final_condition, data)
        assert evaluation_result.result is True
        assert result is True  # admin role OR write permission AND completed order

    def test_list_operators_with_nested_data(self, evaluator, data_set):
        """Test list operators with deeply nested data structures"""
        data = data_set

        # Test nested field access with list operators
        condition = ConditionLeaf(
            field_address="user.profile.interests",
            operator=Operator.list_contains,
            value="programming",
        )
        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert result is True

        # Test multiple list conditions
        interests_condition = ConditionLeaf(
            field_address="user.profile.interests",
            operator=Operator.list_contains,
            value="programming",
        )

        skills_condition = ConditionLeaf(
            field_address="user.profile.skills",
            operator=Operator.list_contains,
            value="python",
        )

        subscription_condition = ConditionLeaf(
            field_address="user.subscriptions.active",
            operator=Operator.not_in_list,
            value=["expired", "cancelled"],
        )

        combined_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[interests_condition, skills_condition, subscription_condition],
        )

        result, evaluation_result = evaluator.evaluate_rule(combined_condition, data)
        assert evaluation_result.result is True
        assert result is True

    @pytest.mark.parametrize(
        "field_address,operator,value,expected_result",
        [
            # Test list_intersects operator - check if user roles intersect with admin roles
            param(
                "user.roles",
                Operator.list_intersects,
                ["admin", "superuser", "root"],
                True,
                id="list_intersects",
            ),
            # Test list_subset operator - check if user permissions are subset of allowed permissions
            param(
                "user.permissions",
                Operator.list_subset,
                ["read", "write", "delete", "manage", "approve", "reject"],
                True,
                id="list_subset",
            ),
            # Test list_superset operator - check if user tags contain required tags
            param(
                "user.tags",
                Operator.list_superset,
                ["premium", "verified"],
                True,
                id="list_superset",
            ),
            # Test list_disjoint operator - check if user languages are completely different from restricted languages
            param(
                "user.preferences.languages",
                Operator.list_disjoint,
                ["de", "it", "pt"],
                True,
                id="list_disjoint",
            ),
        ],
    )
    def test_advanced_list_operators_integration(
        self, evaluator, field_address, operator, value, expected_result
    ):
        """Test integration of advanced list operators in complex scenarios"""
        data = {
            "user": {
                "roles": ["admin", "moderator", "user"],
                "permissions": ["read", "write", "delete", "manage"],
                "tags": ["premium", "verified", "beta"],
                "preferences": {
                    "languages": ["en", "es", "fr"],
                    "categories": ["tech", "business", "finance"],
                },
            },
            "order": {
                "status": "completed",
                "items": ["laptop", "mouse", "keyboard", "monitor"],
                "categories": ["electronics", "accessories", "computers"],
            },
        }

        # Test list_intersects operator - check if user roles intersect with admin roles
        condition = ConditionLeaf(
            field_address=field_address,
            operator=operator,
            value=value,
        )
        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is expected_result
        assert result is expected_result  # "admin" is common between both lists

    def test_complex_list_condition_group(self, evaluator, data_set):
        """Test complex condition group using list operators"""

        # Test complex condition with multiple advanced list operators
        roles_intersect = ConditionLeaf(
            field_address="user.roles",
            operator=Operator.list_intersects,
            value=["admin", "superuser"],
        )

        permissions_subset = ConditionLeaf(
            field_address="user.permissions",
            operator=Operator.list_subset,
            value=["read", "write", "delete", "manage", "approve"],
        )

        tags_superset = ConditionLeaf(
            field_address="user.tags",
            operator=Operator.list_superset,
            value=["premium", "verified"],
        )

        languages_disjoint = ConditionLeaf(
            field_address="user.preferences.languages",
            operator=Operator.list_disjoint,
            value=["de", "it"],
        )

        combined_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                roles_intersect,
                permissions_subset,
                tags_superset,
                languages_disjoint,
            ],
        )

        result, evaluation_result = evaluator.evaluate_rule(
            combined_condition, data_set
        )
        assert result is True  # All conditions should be True

    @pytest.mark.parametrize(
        "field_address,operator,value,expected_result",
        [
            # Test positive cases
            param("user.email", Operator.starts_with, "john", True, id="starts_with"),
            param("user.email", Operator.ends_with, ".com", True, id="ends_with"),
            param("user.full_name", Operator.contains, "Doe", True, id="contains"),
            # Test negative cases
            param(
                "user.email",
                Operator.starts_with,
                "jane",
                False,
                id="starts_with_negative",
            ),
            param(
                "user.email", Operator.ends_with, ".org", False, id="ends_with_negative"
            ),
            param(
                "user.full_name",
                Operator.contains,
                "Smith",
                False,
                id="contains_negative",
            ),
        ],
    )
    def test_string_operators_integration(
        self, evaluator, field_address, operator, value, expected_result, data_set
    ):
        """Test string operators with real-world data"""
        data = data_set

        condition = ConditionLeaf(
            field_address=field_address, operator=operator, value=value
        )
        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is expected_result
        assert result is expected_result

    @pytest.mark.parametrize(
        "field_address,operator,value,expected_result",
        [
            param(
                "user.empty_string", Operator.starts_with, "", True, id="empty_string"
            ),
            param("user.email", Operator.contains, "test", False, id="none_value"),
            param("user.age", Operator.starts_with, "25", False, id="non_string_value"),
            param("user.whitespace", Operator.contains, " ", True, id="whitespace"),
        ],
    )
    def test_string_operators_with_edge_cases(
        self, evaluator, field_address, operator, value, expected_result
    ):
        """Test string operators with edge cases"""
        data = {
            "user": {
                "name": "",
                "email": None,
                "age": 25,
                "empty_string": "",
                "whitespace": "   ",
            }
        }

        condition = ConditionLeaf(
            field_address=field_address, operator=operator, value=value
        )
        result, evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is expected_result
        assert result is expected_result


class TestErrorHandling(TestConditionEvaluator):
    """Test error handling when conditions fail"""

    def test_unknown_operator_raises_error(self, evaluator):
        """Test that unknown operators raise ConditionEvaluationError"""
        # Test the _apply_operator method directly where the unknown operator error occurs
        with pytest.raises(
            ConditionEvaluationError, match="Unknown operator: invalid_operator"
        ):
            evaluator._apply_operator(
                "test_value", "invalid_operator", "expected_value"
            )

    def test_operator_method_raises_exception(self, evaluator):
        """Test that when an operator method raises an exception, it's wrapped in ConditionEvaluationError"""
        # We need to mock the operator_methods to simulate an exception
        from unittest.mock import patch

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise an exception
            mock_operators.get.return_value = (
                lambda a, b: 1 / 0
            )  # This will raise ZeroDivisionError

            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})

    def test_operator_method_raises_type_error(self, evaluator):
        """Test that TypeError from operator methods is wrapped in ConditionEvaluationError"""
        from unittest.mock import patch

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise TypeError
            mock_operators.get.return_value = lambda a, b: int("not_a_number")

            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})

    def test_operator_method_raises_attribute_error(self, evaluator):
        """Test that AttributeError from operator methods is wrapped in ConditionEvaluationError"""
        from unittest.mock import patch

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise AttributeError
            mock_operators.get.return_value = lambda a, b: a.nonexistent_method()

            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})

    def test_operator_method_raises_value_error(self, evaluator):
        """Test that ValueError from operator methods is wrapped in ConditionEvaluationError"""
        from unittest.mock import patch

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operator:
            # Make the operator method raise ValueError
            mock_operator.get.return_value = lambda a, b: int("not_a_number")

            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})

    def test_error_propagation_in_nested_conditions(self, evaluator):
        """Test that errors in nested conditions properly propagate up"""
        from unittest.mock import patch

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise an exception for the second condition
            def failing_operator(a, b):
                if b == 25:  # This will be the value for user.age
                    raise ValueError("Simulated error")
                return a == b

            mock_operators.get.return_value = failing_operator

            inner_condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            outer_group = ConditionGroup(
                logical_operator=GroupOperator.and_,
                conditions=[
                    ConditionLeaf(
                        field_address="user.name", operator=Operator.eq, value="john"
                    ),
                    inner_condition,  # This will raise an error
                ],
            )

            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(
                    outer_group, {"user": {"name": "john", "age": 25}}
                )

    def test_error_with_fides_data_structure(self, evaluator, mock_fides_data):
        """Test that errors work correctly with Fides data structures"""
        from unittest.mock import patch

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise an exception
            mock_operators.get.return_value = lambda a, b: 1 / 0

            condition = ConditionLeaf(
                field_address="user.name", operator=Operator.eq, value="test"
            )

            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(condition, mock_fides_data)

    def test_error_message_contains_original_exception(self, evaluator):
        """Test that error messages contain information about the original exception"""
        from unittest.mock import patch

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise a specific exception
            mock_operators.get.return_value = lambda a, b: int("not_a_number")

            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            with pytest.raises(ConditionEvaluationError) as exc_info:
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})

            # Check that the error message contains the original exception info
            assert "Unexpected error evaluating condition:" in str(exc_info.value)
            # The original exception should be preserved as the cause
            assert exc_info.value.__cause__ is not None

    def test_unknown_logical_operator_handling(self, evaluator, sample_data):
        """Test that unknown logical operators raise ConditionEvaluationError"""
        # Create a mock group with an unknown logical operator
        from unittest.mock import Mock

        mock_group = Mock(autospec=True)
        mock_group.logical_operator = "invalid_operator"
        mock_group.conditions = [
            ConditionLeaf(
                field_address="user.name", operator=Operator.eq, value="john_doe"
            ),
        ]

        # This should now raise an error for unknown logical operators
        with pytest.raises(
            ConditionEvaluationError, match="Unknown logical operator: invalid_operator"
        ):
            evaluator._evaluate_group_condition(mock_group, sample_data)

    def test_graceful_handling_of_type_mismatches(self, evaluator):
        """Test that type mismatches are handled gracefully by operators"""
        # These should NOT raise errors - they should return False gracefully

        # Test numeric operator on string
        condition = ConditionLeaf(
            field_address="user.name", operator=Operator.gt, value=10
        )

        # This should return False, not raise an error
        result, evaluation_result = evaluator.evaluate_rule(
            condition, {"user": {"name": "john"}}
        )
        assert result is False
        assert evaluation_result.result is False

        # Test string operator on number
        condition = ConditionLeaf(
            field_address="user.age", operator=Operator.starts_with, value="2"
        )

        # This should return False, not raise an error
        result, evaluation_result = evaluator.evaluate_rule(
            condition, {"user": {"age": 25}}
        )
        assert result is False
        assert evaluation_result.result is False

        # Test list operator on non-list
        condition = ConditionLeaf(
            field_address="user.name", operator=Operator.list_contains, value="admin"
        )

        # This should return False, not raise an error
        result, evaluation_result = evaluator.evaluate_rule(
            condition, {"user": {"name": "john"}}
        )
        assert result is False
        assert evaluation_result.result is False

    def test_fides_data_access_exception_handling(self, evaluator):
        """Test that exceptions in Fides data access are handled gracefully by the fallback mechanism"""

        # Create a real object that has get_field_value but raises an exception
        class FidesDataWithException:
            def get_field_value(self, field_path):
                raise AttributeError("Simulated Fides access error")

        obj = FidesDataWithException()

        # This should handle the AttributeError gracefully and fall back to dict access
        # Since the object doesn't have a get method, it should return None
        value = evaluator._get_nested_value(obj, ["field_name"])
        assert value is None

    def test_fides_data_access_with_fallback(self, evaluator):
        """Test that Fides data access falls back to dict access when get_field_value fails"""

        # Create an object that has both get_field_value and get methods
        class FidesDataWithFallback:
            def __init__(self):
                self.data = {"field_name": "fallback_value"}

            def get_field_value(self, field_path):
                raise ValueError("Simulated Fides access error")

            def get(self, key, default=None):
                return self.data.get(key, default)

        obj = FidesDataWithFallback()

        # This should handle the ValueError gracefully and fall back to dict access
        value = evaluator._get_nested_value(obj, ["field_name"])
        assert value == "fallback_value"

    def test_field_path_creation_failure_handling(self, evaluator):
        """Test that FieldPath creation failures are handled gracefully"""
        from unittest.mock import patch

        # Create an object that has get_field_value method
        class FidesData:
            def get_field_value(self, field_path):
                return "test_value"

        obj = FidesData()

        # Mock FieldPath to raise a ValueError (which is caught)
        with patch(
            "fides.api.task.conditional_dependencies.evaluator.FieldPath",
            side_effect=ValueError("Invalid field path"),
        ):
            # This should handle the ValueError gracefully and fall back to dict access
            # Since the object doesn't have a get method, it should return None
            value = evaluator._get_nested_value(obj, ["field_name"])
            assert value is None

    def test_field_path_creation_failure_with_dict_fallback(self, evaluator):
        """Test that FieldPath creation failures fall back to dict access when available"""
        from unittest.mock import patch

        # Create an object that has both get_field_value and get methods
        class FidesDataWithDict:
            def __init__(self):
                self.data = {"field_name": "dict_value"}

            def get_field_value(self, field_path):
                return "fides_value"

            def get(self, key, default=None):
                return self.data.get(key, default)

        obj = FidesDataWithDict()

        # Mock FieldPath to raise a ValueError (which is caught)
        with patch(
            "fides.api.task.conditional_dependencies.evaluator.FieldPath",
            side_effect=ValueError("Invalid field path"),
        ):
            # This should handle the ValueError gracefully and fall back to dict access
            value = evaluator._get_nested_value(obj, ["field_name"])
            assert value == "dict_value"

    def test_uncaught_exception_in_fides_data_access(self, evaluator):
        """Test that exceptions not caught by _get_nested_value are raised"""

        # Create an object that has get_field_value but raises an uncaught exception
        class FidesDataWithUncaughtException:
            def get_field_value(self, field_path):
                raise RuntimeError("Simulated uncaught exception")

        obj = FidesDataWithUncaughtException()

        # This should raise the RuntimeError since it's not caught by the try-catch block
        with pytest.raises(RuntimeError, match="Simulated uncaught exception"):
            evaluator._get_nested_value(obj, ["field_name"])

    def test_uncaught_exception_in_dict_access(self, evaluator):
        """Test that exceptions not caught in dict access are raised"""

        # Create an object that has a get method but raises an uncaught exception
        class ObjectWithUncaughtException:
            def get(self, key, default=None):
                raise RuntimeError("Simulated uncaught exception")

        obj = ObjectWithUncaughtException()

        # This should raise the RuntimeError since it's not caught
        with pytest.raises(RuntimeError, match="Simulated uncaught exception"):
            evaluator._get_nested_value(obj, ["field_name"])

    def test_hasattr_failure_handling(self, evaluator):
        """Test that hasattr failures are raised (not handled gracefully)"""
        from unittest.mock import patch

        # Create a simple object
        obj = {"field_name": "test_value"}

        # Mock hasattr to raise an exception
        with patch(
            "builtins.hasattr", side_effect=Exception("Simulated hasattr error")
        ):
            # This should raise the exception since hasattr failures are not caught
            with pytest.raises(Exception, match="Simulated hasattr error"):
                evaluator._get_nested_value(obj, ["field_name"])

    def test_complex_fallback_scenario(self, evaluator):
        """Test a complex scenario with multiple fallback mechanisms"""

        # Create an object that has get_field_value but fails with AttributeError
        # and then falls back to dict access which also fails with AttributeError
        class ComplexFailingObject:
            def get_field_value(self, field_path):
                raise AttributeError("Simulated Fides access error")

            def get(self, key, default=None):
                raise AttributeError("Simulated dict access error")

        obj = ComplexFailingObject()

        # This should raise the AttributeError since the dict access fallback doesn't have exception handling
        with pytest.raises(AttributeError, match="Simulated dict access error"):
            evaluator._get_nested_value(obj, ["field_name"])

    def test_get_nested_value_exception_propagation(self, evaluator):
        """Test that exceptions from _get_nested_value properly propagate to evaluate_rule"""

        # Create an object that will cause _get_nested_value to raise an exception
        class ObjectCausingException:
            def get_field_value(self, field_path):
                raise RuntimeError("Simulated _get_nested_value error")

        obj = ObjectCausingException()

        condition = ConditionLeaf(
            field_address="user.age", operator=Operator.eq, value=25
        )

        # This should raise the RuntimeError directly since _get_nested_value doesn't catch it
        # and the exception propagates up to evaluate_rule
        with pytest.raises(RuntimeError, match="Simulated _get_nested_value error"):
            evaluator.evaluate_rule(condition, obj)

    def test_error_in_group_condition_evaluate_rule_calls(self, evaluator, sample_data):
        """Test that errors in evaluate_rule calls within _evaluate_group_condition properly propagate"""
        from unittest.mock import patch, Mock

        # Create a mock result object
        mock_result = Mock(autospec=True)
        mock_result.result = True

        # Mock evaluate_rule to raise an exception for the second condition
        def failing_evaluate_rule(condition, data):
            if (
                hasattr(condition, "field_address")
                and condition.field_address == "user.age"
            ):
                raise ConditionEvaluationError("Simulated error in evaluate_rule")
            return True, mock_result  # Return a mock result for successful conditions

        with patch.object(
            evaluator, "evaluate_rule", side_effect=failing_evaluate_rule
        ):
            group = ConditionGroup(
                logical_operator=GroupOperator.and_,
                conditions=[
                    ConditionLeaf(
                        field_address="user.name",
                        operator=Operator.eq,
                        value="john_doe",
                    ),
                    ConditionLeaf(
                        field_address="user.age", operator=Operator.eq, value=25
                    ),
                ],
            )

            # This should raise the ConditionEvaluationError from the failing evaluate_rule call
            with pytest.raises(
                ConditionEvaluationError, match="Simulated error in evaluate_rule"
            ):
                evaluator._evaluate_group_condition(group, sample_data)

    def test_error_in_group_condition_logical_operator_handling(
        self, evaluator, sample_data
    ):
        """Test that errors in logical operator handling within _evaluate_group_condition are properly handled"""
        from unittest.mock import patch

        # Create a group with valid conditions
        group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.name", operator=Operator.eq, value="john_doe"
                ),
            ],
        )

        # Mock the logical operator functions to raise an exception
        with patch(
            "builtins.all", side_effect=Exception("Simulated logical operator error")
        ):
            # This should raise the exception from the logical operator function
            with pytest.raises(Exception, match="Simulated logical operator error"):
                evaluator._evaluate_group_condition(group, sample_data)

    def test_error_in_leaf_condition_operator_application(self, evaluator):
        """Test that errors in _apply_operator are properly caught and re-raised"""
        from unittest.mock import patch

        # Mock _apply_operator to raise a ConditionEvaluationError
        with patch.object(
            evaluator,
            "_apply_operator",
            side_effect=ConditionEvaluationError("Simulated operator error"),
        ):
            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            # This should catch the ConditionEvaluationError and re-raise it
            with pytest.raises(
                ConditionEvaluationError, match="Simulated operator error"
            ):
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})

    def test_error_in_leaf_condition_unexpected_exception(self, evaluator):
        """Test that unexpected exceptions in _apply_operator are properly wrapped"""
        from unittest.mock import patch

        # Instead of mocking _apply_operator directly, let's mock the operator_methods
        # to simulate an unexpected exception that will be caught and wrapped
        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise an unexpected exception
            mock_operators.get.return_value = (
                lambda a, b: 1 / 0
            )  # This will raise ZeroDivisionError

            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            # This should catch the ZeroDivisionError and wrap it in ConditionEvaluationError
            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})

    def test_apply_operator_exception_wrapping(self, evaluator):
        """Test that _apply_operator properly wraps different types of exceptions"""
        from unittest.mock import patch

        # Test with different types of exceptions
        test_cases = [
            (ZeroDivisionError("Division by zero"), "Division by zero"),
            (ValueError("Invalid value"), "Invalid value"),
            (TypeError("Type mismatch"), "Type mismatch"),
            (RuntimeError("Runtime error"), "Runtime error"),
            (AttributeError("Missing attribute"), "Missing attribute"),
        ]

        for exception_class, error_message in test_cases:
            with patch(
                "fides.api.task.conditional_dependencies.evaluator.operator_methods",
                autospec=True,
            ) as mock_operators:
                # Make the operator method raise the specific exception
                mock_operators.get.return_value = lambda a, b: exception_class(
                    error_message
                )

                condition = ConditionLeaf(
                    field_address="user.age", operator=Operator.eq, value=25
                )

                # This should catch the exception and wrap it in ConditionEvaluationError
                with pytest.raises(
                    ConditionEvaluationError,
                    match="Unexpected error evaluating condition:",
                ):
                    evaluator.evaluate_rule(condition, {"user": {"age": 25}})

    def test_apply_operator_with_complex_exception(self, evaluator):
        """Test that _apply_operator properly handles complex exceptions from operator methods"""
        from unittest.mock import patch

        # Create a complex exception scenario
        class ComplexException(Exception):
            def __init__(self, message, details):
                super().__init__(message)
                self.details = details

        with patch(
            "fides.api.task.conditional_dependencies.evaluator.operator_methods",
            autospec=True,
        ) as mock_operators:
            # Make the operator method raise a complex exception
            def complex_operator(a, b):
                if a == 25 and b == 25:
                    raise ComplexException("Complex error occurred", {"a": a, "b": b})
                return a == b

            mock_operators.get.return_value = complex_operator

            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            # This should catch the ComplexException and wrap it in ConditionEvaluationError
            with pytest.raises(
                ConditionEvaluationError, match="Unexpected error evaluating condition:"
            ):
                evaluator.evaluate_rule(condition, {"user": {"age": 25}})
