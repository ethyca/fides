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
        collection = Mock()
        collection.get_field_value.return_value = "test_value"
        return collection

    @pytest.fixture
    def mock_fides_data(self, mock_fides_collection):
        """Mock Fides data structure"""
        data = Mock()
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
        data = Mock()
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
        result = evaluator.evaluate_rule(condition, sample_data)
        assert result is expected_result, f"Failed for {description}"

    def test_leaf_condition_with_fides_data(self, evaluator, mock_fides_data):
        """Test leaf condition with Fides data structure"""
        condition = ConditionLeaf(
            field_address="user.name", operator=Operator.eq, value="test_value"
        )

        result = evaluator.evaluate_rule(condition, mock_fides_data)
        assert result is True


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
        result = evaluator.evaluate_rule(group, sample_data)
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
        result = evaluator.evaluate_rule(group, sample_data)
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
        result = evaluator.evaluate_rule(group, sample_data)
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
        result = evaluator.evaluate_rule(group, sample_data)
        assert result is False

    def test_single_condition_group(self, evaluator, sample_data):
        """Test group with single condition"""
        group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.name", operator=Operator.eq, value="john_doe"
                ),
            ],
        )
        result = evaluator.evaluate_rule(group, sample_data)
        assert result is True

    def test_unknown_logical_operator(self, evaluator, sample_data):
        """Test handling of unknown logical operator"""
        # Test the actual code path by creating a mock group that bypasses validation
        from unittest.mock import Mock

        # Create a mock group that simulates an unknown logical operator
        mock_group = Mock()
        mock_group.logical_operator = "invalid_operator"
        mock_group.conditions = [
            ConditionLeaf(
                field_address="user.name", operator=Operator.eq, value="john_doe"
            ),
        ]

        # This should trigger the unknown logical operator handling
        result = evaluator._evaluate_group_condition(mock_group, sample_data)
        assert result is False  # Should return False for unknown operators


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

        result = evaluator.evaluate_rule(outer_group, sample_data)
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

        result = evaluator.evaluate_rule(outer_group, sample_data)
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

        result = evaluator.evaluate_rule(outermost, sample_data)
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

    def test_empty_data(self, evaluator):
        """Test evaluation with empty data"""
        condition = ConditionLeaf(
            field_address="any.field_address", operator=Operator.exists
        )

        result = evaluator.evaluate_rule(condition, {})
        assert result is False

    def test_none_data(self, evaluator):
        """Test evaluation with None data"""
        condition = ConditionLeaf(
            field_address="any.field_address", operator=Operator.exists
        )

        result = evaluator.evaluate_rule(condition, None)
        assert result is False

    def test_missing_field_with_exists(self, evaluator, sample_data):
        """Test exists operator with missing field"""
        condition = ConditionLeaf(
            field_address="user.nonexistent", operator=Operator.exists
        )

        result = evaluator.evaluate_rule(condition, sample_data)
        assert result is False

    def test_missing_field_with_not_exists(self, evaluator, sample_data):
        """Test not_exists operator with missing field"""
        condition = ConditionLeaf(
            field_address="user.nonexistent", operator=Operator.not_exists
        )

        result = evaluator.evaluate_rule(condition, sample_data)
        assert result is True

    def test_none_value_comparison(self, evaluator, sample_data):
        """Test comparison with None values"""
        condition = ConditionLeaf(
            field_address="missing_field", operator=Operator.eq, value=None
        )

        result = evaluator.evaluate_rule(condition, sample_data)
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

        result = evaluator.evaluate_rule(condition, data)
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

        result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: age=25>=18, active=True, verified=True, subscription=active
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

        result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: order.status=completed, order.total=150>100
        assert result is True

    def test_fides_reference_scenario(self, evaluator, mock_fides_data):
        """Test scenario using Fides reference structures"""
        # Test that the evaluator works with Fides data structures
        condition = ConditionLeaf(
            field_address="customer.email", operator=Operator.eq, value="test_value"
        )

        result = evaluator.evaluate_rule(condition, mock_fides_data)
        assert result is True

    def test_list_operators_integration(self, evaluator, data_set):
        """Test integration of list operators in complex scenarios"""
        data = data_set

        # Test list_contains operator - check if user.roles contains "admin"
        condition = ConditionLeaf(
            field_address="user.roles", operator=Operator.list_contains, value="admin"
        )
        result = evaluator.evaluate_rule(condition, data)
        assert result is True  # "admin" is in the user.roles list

        # Test not_in_list operator
        condition = ConditionLeaf(
            field_address="user.roles",
            operator=Operator.not_in_list,
            value=["guest", "anonymous"],
        )
        result = evaluator.evaluate_rule(condition, data)
        assert result is True  # "admin" and "moderator" are not in the excluded list

        # Test list_contains operator with permissions
        condition = ConditionLeaf(
            field_address="user.permissions",
            operator=Operator.list_contains,
            value="write",
        )
        result = evaluator.evaluate_rule(condition, data)
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

        result = evaluator.evaluate_rule(final_condition, data)
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
        result = evaluator.evaluate_rule(condition, data)
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

        result = evaluator.evaluate_rule(combined_condition, data)
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
        result = evaluator.evaluate_rule(condition, data)
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

        result = evaluator.evaluate_rule(combined_condition, data_set)
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
        result = evaluator.evaluate_rule(condition, data)
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
        result = evaluator.evaluate_rule(condition, data)
        assert result is expected_result
