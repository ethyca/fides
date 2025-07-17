from unittest.mock import Mock

import pytest
from pytest import param
from sqlalchemy.orm import Session

from fides.api.graph.config import FieldPath
from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator
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
                ["nested_empty", "level1", "level2", "field"],
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
        value = evaluator._get_nested_value(mock_fides_data, ["field", "subfield"])
        assert value == "test_value"
        mock_fides_data.get_field_value.assert_called_once()

    def test_fides_data_fallback_to_dict(self, evaluator):
        """Test Fides data falls back to dict access when get_field_value fails"""
        data = Mock()
        data.get_field_value.side_effect = AttributeError("No such method")
        data.get.return_value = "fallback_value"

        value = evaluator._get_nested_value(data, ["field"])
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
    """Test individual operator evaluations"""

    @pytest.mark.parametrize(
        "actual_value,operator,expected_value,expected_result",
        [
            param("some_value", Operator.exists, None, True, id="exists"),
            param(None, Operator.exists, None, False, id="exists None"),
            param(None, Operator.not_exists, None, True, id="not_exists None"),
            param("some_value", Operator.not_exists, None, False, id="not_exists"),
            param("test", Operator.eq, "test", True, id="eq"),
            param("test", Operator.eq, "different", False, id="eq different"),
            param("test", Operator.neq, "different", True, id="neq"),
            param("test", Operator.neq, "test", False, id="neq test"),
        ],
    )
    def test_basic_operators(
        self, evaluator, actual_value, operator, expected_value, expected_result
    ):
        """Test basic operators (exists, not_exists, eq, neq)"""
        result = evaluator._apply_operator(actual_value, operator, expected_value)
        assert result is expected_result

    @pytest.mark.parametrize(
        "actual_value,operator,expected_value,expected_result",
        [
            param(5, Operator.lt, 10, True, id="5_lt_10_success"),
            param(15, Operator.lt, 10, False, id="15_lt_10_failure"),
            param(None, Operator.lt, 10, False, id="None_lt_10_failure"),
            param(10, Operator.lte, 10, True, id="10_lte_10_success"),
            param(5, Operator.lte, 10, True, id="5_lte_10_success"),
            param(15, Operator.lte, 10, False, id="15_lte_10_failure"),
            param(15, Operator.gt, 10, True, id="15_gt_10_success"),
            param(5, Operator.gt, 10, False, id="5_gt_10_failure"),
            param(10, Operator.gte, 10, True, id="10_gte_10_success"),
            param(15, Operator.gte, 10, True, id="15_gte_10_success"),
            param(5, Operator.gte, 10, False, id="5_gte_10_failure"),
        ],
    )
    def test_comparison_operators(
        self, evaluator, actual_value, operator, expected_value, expected_result
    ):
        """Test comparison operators (lt, lte, gt, gte)"""
        result = evaluator._apply_operator(actual_value, operator, expected_value)
        assert result is expected_result

    def test_unknown_operator(self, evaluator):
        """Test unknown operator returns False"""

        # Create a mock operator that doesn't exist in the enum
        class MockOperator:
            def __str__(self):
                return "unknown"

        result = evaluator._apply_operator("test", MockOperator(), "test")
        assert result is False

    def test_numeric_comparisons(self, evaluator):
        """Test numeric comparisons with different types"""
        # Integer comparisons
        assert evaluator._apply_operator(5, Operator.lt, 10.0) is True
        assert evaluator._apply_operator(10.0, Operator.eq, 10) is True
        assert evaluator._apply_operator(15.5, Operator.gt, 10) is True

    def test_string_comparisons(self, evaluator):
        """Test string comparisons"""
        assert evaluator._apply_operator("abc", Operator.lt, "def") is True
        assert evaluator._apply_operator("xyz", Operator.gt, "abc") is True
        assert evaluator._apply_operator("test", Operator.eq, "test") is True

    def test_boolean_comparisons(self, evaluator):
        """Test boolean comparisons"""
        assert evaluator._apply_operator(True, Operator.eq, True) is True
        assert evaluator._apply_operator(False, Operator.eq, False) is True
        assert evaluator._apply_operator(True, Operator.neq, False) is True

    @pytest.mark.parametrize(
        "actual_value,operator,expected_value,expected_result",
        [
            param(
                ["apple", "banana", "cherry"],
                Operator.list_contains,
                "banana",
                True,
                id="list_contains_banana",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_contains,
                "orange",
                False,
                id="list_contains_orange",
            ),
            param(
                [1, 3, 5, 7, 9], Operator.list_contains, 5, True, id="list_contains_5"
            ),
            param(
                [1, "test", True, 3.14],
                Operator.list_contains,
                True,
                True,
                id="list_contains_True",
            ),
            param(
                [],
                Operator.list_contains,
                "anything",
                False,
                id="list_contains_anything",
            ),
            param(
                "not_a_list",
                Operator.list_contains,
                "test",
                False,
                id="list_contains_not_a_list",
            ),
            param(None, Operator.list_contains, "test", False, id="list_contains_None"),
            param(
                "orange",
                Operator.not_in_list,
                ["apple", "banana", "cherry"],
                True,
                id="not_in_list_orange",
            ),
            param(
                "apple",
                Operator.not_in_list,
                ["apple", "banana", "cherry"],
                False,
                id="not_in_list_apple",
            ),
            param(
                "anything", Operator.not_in_list, [], True, id="not_in_list_anything"
            ),
            param(
                "test", Operator.not_in_list, "not_a_list", True, id="not_in_list_test"
            ),
        ],
    )
    def test_list_operators(
        self, evaluator, actual_value, operator, expected_value, expected_result
    ):
        """Test list operators (list_contains, not_in_list)"""
        result = evaluator._apply_operator(actual_value, operator, expected_value)
        assert result is expected_result


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
        condition = ConditionLeaf(field=field, operator=operator, value=value)
        result = evaluator.evaluate_rule(condition, sample_data)
        assert result is expected_result, f"Failed for {description}"

    def test_leaf_condition_with_fides_data(self, evaluator, mock_fides_data):
        """Test leaf condition with Fides data structure"""
        condition = ConditionLeaf(
            field="user.name", operator=Operator.eq, value="test_value"
        )

        result = evaluator.evaluate_rule(condition, mock_fides_data)
        assert result is True


class TestGroupConditionEvaluation(TestConditionEvaluator):
    """Test group condition evaluation"""

    def test_and_group_all_true(self, evaluator, sample_data):
        """Test AND group with all conditions true"""
        group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field="user.age", operator=Operator.gte, value=18),
                ConditionLeaf(field="user.active", operator=Operator.eq, value=True),
                ConditionLeaf(field="user.name", operator=Operator.exists),
            ],
        )

        result = evaluator.evaluate_rule(group, sample_data)
        assert result is True

    def test_and_group_one_false(self, evaluator, sample_data):
        """Test AND group with one condition false"""
        group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field="user.age", operator=Operator.gte, value=18),
                ConditionLeaf(
                    field="user.active", operator=Operator.eq, value=False
                ),  # This is false
                ConditionLeaf(field="user.name", operator=Operator.exists),
            ],
        )

        result = evaluator.evaluate_rule(group, sample_data)
        assert result is False

    def test_or_group_one_true(self, evaluator, sample_data):
        """Test OR group with one condition true"""
        group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field="user.age", operator=Operator.lt, value=18
                ),  # This is false
                ConditionLeaf(
                    field="user.active", operator=Operator.eq, value=True
                ),  # This is true
                ConditionLeaf(
                    field="user.name", operator=Operator.eq, value="wrong_name"
                ),  # This is false
            ],
        )

        result = evaluator.evaluate_rule(group, sample_data)
        assert result is True

    def test_or_group_all_false(self, evaluator, sample_data):
        """Test OR group with all conditions false"""
        group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(field="user.age", operator=Operator.lt, value=18),
                ConditionLeaf(field="user.active", operator=Operator.eq, value=False),
                ConditionLeaf(
                    field="user.name", operator=Operator.eq, value="wrong_name"
                ),
            ],
        )

        result = evaluator.evaluate_rule(group, sample_data)
        assert result is False

    def test_single_condition_group(self, evaluator, sample_data):
        """Test group with single condition"""
        group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field="user.name", operator=Operator.eq, value="john_doe")
            ],
        )

        result = evaluator.evaluate_rule(group, sample_data)
        assert result is True


class TestNestedGroupEvaluation(TestConditionEvaluator):
    """Test nested group condition evaluation"""

    def test_nested_and_or_groups(self, evaluator, sample_data):
        """Test nested AND/OR groups"""
        # Structure: (user.age >= 18 AND (user.role = 'admin' OR user.verified = true))
        inner_group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(field="user.role", operator=Operator.eq, value="admin"),
                ConditionLeaf(field="user.verified", operator=Operator.eq, value=True),
            ],
        )

        outer_group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field="user.age", operator=Operator.gte, value=18),
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
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field="user.age", operator=Operator.gte, value=18
                ),  # True
                ConditionLeaf(
                    field="user.active", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        inner_group_2 = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field="user.role", operator=Operator.eq, value="admin"
                ),  # False
                ConditionLeaf(
                    field="user.verified", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        middle_group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[inner_group_1, inner_group_2],  # True OR False = True
        )

        outer_group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                middle_group,  # True
                ConditionLeaf(field="user.name", operator=Operator.exists),  # True
            ],
        )

        result = evaluator.evaluate_rule(outer_group, sample_data)
        assert result is True

    def test_deep_nesting(self, evaluator, sample_data):
        """Test very deep nesting"""
        # Create a deeply nested structure: (((A OR B) AND C) OR D) AND E
        deepest = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field="user.role", operator=Operator.eq, value="admin"
                ),  # False
                ConditionLeaf(
                    field="user.verified", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        level_2 = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                deepest,  # True (OR of False and True)
                ConditionLeaf(
                    field="user.active", operator=Operator.eq, value=True
                ),  # True
            ],
        )

        level_3 = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                level_2,  # True (AND of True and True)
                ConditionLeaf(
                    field="user.age", operator=Operator.lt, value=18
                ),  # False
            ],
        )

        outermost = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                level_3,  # True (OR of True and False)
                ConditionLeaf(field="user.name", operator=Operator.exists),  # True
            ],
        )

        result = evaluator.evaluate_rule(outermost, sample_data)
        assert result is True

    def test_mixed_conditions_in_group(self, evaluator, sample_data):
        """Test mixing ConditionLeaf and ConditionGroup in the same group"""
        inner_group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field="user.verified", operator=Operator.eq, value=True),
                ConditionLeaf(field="user.premium", operator=Operator.eq, value=True),
            ],
        )

        mixed_group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(field="user.admin", operator=Operator.eq, value=True),
                inner_group,
                ConditionLeaf(field="user.moderator", operator=Operator.eq, value=True),
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
        condition = ConditionLeaf(field="any.field", operator=Operator.exists)

        result = evaluator.evaluate_rule(condition, {})
        assert result is False

    def test_none_data(self, evaluator):
        """Test evaluation with None data"""
        condition = ConditionLeaf(field="any.field", operator=Operator.exists)

        result = evaluator.evaluate_rule(condition, None)
        assert result is False

    def test_missing_field_with_exists(self, evaluator, sample_data):
        """Test exists operator with missing field"""
        condition = ConditionLeaf(field="user.nonexistent", operator=Operator.exists)

        result = evaluator.evaluate_rule(condition, sample_data)
        assert result is False

    def test_missing_field_with_not_exists(self, evaluator, sample_data):
        """Test not_exists operator with missing field"""
        condition = ConditionLeaf(
            field="user.nonexistent", operator=Operator.not_exists
        )

        result = evaluator.evaluate_rule(condition, sample_data)
        assert result is True

    def test_none_value_comparison(self, evaluator, sample_data):
        """Test comparison with None values"""
        condition = ConditionLeaf(
            field="missing_field", operator=Operator.eq, value=None
        )

        result = evaluator.evaluate_rule(condition, sample_data)
        assert result is True

    @pytest.mark.parametrize(
        "field_value,expected_value,description",
        [
            ("", "", "empty string"),
            (0, 0, "zero value"),
            (False, False, "false boolean"),
        ],
    )
    def test_edge_case_comparisons(
        self, evaluator, field_value, expected_value, description
    ):
        """Test edge case comparisons (empty string, zero, false)"""
        data = {"field": field_value}
        condition = ConditionLeaf(
            field="field", operator=Operator.eq, value=expected_value
        )

        result = evaluator.evaluate_rule(condition, data)
        assert result is True, f"Failed for {description}"


class TestIntegration(TestConditionEvaluator):
    """Test integration scenarios"""

    def test_complex_real_world_scenario(self, evaluator, sample_data):
        """Test a complex real-world scenario"""
        # Scenario: User must be 18+, active, and either have admin role OR be verified
        # AND their subscription must be active
        role_or_verified = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(field="user.role", operator=Operator.eq, value="admin"),
                ConditionLeaf(field="user.verified", operator=Operator.eq, value=True),
            ],
        )

        user_requirements = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field="user.age", operator=Operator.gte, value=18),
                ConditionLeaf(field="user.active", operator=Operator.eq, value=True),
                role_or_verified,
            ],
        )

        subscription_requirement = ConditionLeaf(
            field="user.billing.subscription.status",
            operator=Operator.eq,
            value="active",
        )

        final_rule = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[user_requirements, subscription_requirement],
        )

        result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: age=25>=18, active=True, verified=True, subscription=active
        assert result is True

    def test_order_processing_scenario(self, evaluator, sample_data):
        """Test order processing scenario"""
        # Scenario: Order must be completed AND total > 100 OR user is premium
        order_condition = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field="order.status", operator=Operator.eq, value="completed"
                ),
                ConditionLeaf(field="order.total", operator=Operator.gt, value=100.0),
            ],
        )

        user_premium = ConditionLeaf(
            field="user.billing.subscription.plan",
            operator=Operator.eq,
            value="premium",
        )

        final_rule = ConditionGroup(
            op=GroupOperator.or_, conditions=[order_condition, user_premium]
        )

        result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: order.status=completed, order.total=150>100
        assert result is True

    def test_fides_reference_scenario(self, evaluator, mock_fides_data):
        """Test scenario using Fides reference structures"""
        # Test that the evaluator works with Fides data structures
        condition = ConditionLeaf(
            field="customer.email", operator=Operator.eq, value="test_value"
        )

        result = evaluator.evaluate_rule(condition, mock_fides_data)
        assert result is True

    def test_list_operators_integration(self, evaluator):
        """Test integration of list operators in complex scenarios"""
        data = {
            "user": {
                "roles": ["admin", "moderator"],
                "permissions": ["read", "write", "delete"],
                "tags": ["premium", "verified"],
                "preferences": {
                    "languages": ["en", "es", "fr"],
                    "categories": ["tech", "business"],
                },
            },
            "order": {
                "status": "completed",
                "items": ["laptop", "mouse", "keyboard"],
                "categories": ["electronics", "accessories"],
            },
        }

        # Test list_contains operator - check if user.roles contains "admin"
        condition = ConditionLeaf(
            field="user.roles", operator=Operator.list_contains, value="admin"
        )
        result = evaluator.evaluate_rule(condition, data)
        assert result is True  # "admin" is in the user.roles list

        # Test not_in_list operator
        condition = ConditionLeaf(
            field="user.roles",
            operator=Operator.not_in_list,
            value=["guest", "anonymous"],
        )
        result = evaluator.evaluate_rule(condition, data)
        assert result is True  # "admin" and "moderator" are not in the excluded list

        # Test list_contains operator with permissions
        condition = ConditionLeaf(
            field="user.permissions", operator=Operator.list_contains, value="write"
        )
        result = evaluator.evaluate_rule(condition, data)
        assert result is True  # "write" is in the permissions list

    def test_complex_list_condition_group(self, evaluator):
        """Test complex condition group using list operators"""
        data = {
            "user": {
                "roles": ["admin", "moderator"],
                "permissions": ["read", "write"],
                "tags": ["premium", "verified"],
            },
            "order": {"status": "completed", "items": ["laptop", "mouse"]},
        }

        # Complex condition: (user has admin role OR user has write permission) AND order is completed
        role_condition = ConditionLeaf(
            field="user.roles", operator=Operator.list_contains, value="admin"
        )

        permission_condition = ConditionLeaf(
            field="user.permissions", operator=Operator.list_contains, value="write"
        )

        order_condition = ConditionLeaf(
            field="order.status", operator=Operator.eq, value="completed"
        )

        role_or_permission = ConditionGroup(
            op=GroupOperator.or_, conditions=[role_condition, permission_condition]
        )

        final_condition = ConditionGroup(
            op=GroupOperator.and_, conditions=[role_or_permission, order_condition]
        )

        result = evaluator.evaluate_rule(final_condition, data)
        assert result is True  # admin role OR write permission AND completed order

    def test_list_operators_with_nested_data(self, evaluator):
        """Test list operators with deeply nested data structures"""
        data = {
            "user": {
                "profile": {
                    "interests": ["programming", "reading", "gaming"],
                    "skills": ["python", "javascript", "sql"],
                },
                "subscriptions": {
                    "active": ["premium", "newsletter"],
                    "expired": ["trial"],
                },
            }
        }

        # Test nested field access with list operators
        condition = ConditionLeaf(
            field="user.profile.interests",
            operator=Operator.list_contains,
            value="programming",
        )
        result = evaluator.evaluate_rule(condition, data)
        assert result is True

        # Test multiple list conditions
        interests_condition = ConditionLeaf(
            field="user.profile.interests",
            operator=Operator.list_contains,
            value="programming",
        )

        skills_condition = ConditionLeaf(
            field="user.profile.skills", operator=Operator.list_contains, value="python"
        )

        subscription_condition = ConditionLeaf(
            field="user.subscriptions.active",
            operator=Operator.not_in_list,
            value=["expired", "cancelled"],
        )

        combined_condition = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[interests_condition, skills_condition, subscription_condition],
        )

        result = evaluator.evaluate_rule(combined_condition, data)
        assert result is True
