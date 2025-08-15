from unittest.mock import Mock, patch

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

    # Common condition fixtures
    @pytest.fixture
    def user_age_gte_18(self):
        """Common condition: user.age >= 18"""
        return ConditionLeaf(field_address="user.age", operator=Operator.gte, value=18)

    @pytest.fixture
    def user_active_true(self):
        """Common condition: user.active == True"""
        return ConditionLeaf(
            field_address="user.active", operator=Operator.eq, value=True
        )

    @pytest.fixture
    def user_verified_true(self):
        """Common condition: user.verified == True"""
        return ConditionLeaf(
            field_address="user.verified", operator=Operator.eq, value=True
        )

    @pytest.fixture
    def user_role_admin(self):
        """Common condition: user.role == 'admin'"""
        return ConditionLeaf(
            field_address="user.role", operator=Operator.eq, value="admin"
        )

    @pytest.fixture
    def user_score_gt_90(self):
        """Common condition: user.score > 90"""
        return ConditionLeaf(field_address="user.score", operator=Operator.gt, value=90)

    @pytest.fixture
    def user_name_john_doe(self):
        """Common condition: user.name == 'john_doe'"""
        return ConditionLeaf(
            field_address="user.name", operator=Operator.eq, value="john_doe"
        )

    @pytest.fixture
    def user_name_exists(self):
        """Common condition: user.name exists"""
        return ConditionLeaf(field_address="user.name", operator=Operator.exists)

    @pytest.fixture
    def order_status_completed(self):
        """Common condition: order.status == 'completed'"""
        return ConditionLeaf(
            field_address="order.status", operator=Operator.eq, value="completed"
        )

    @pytest.fixture
    def order_total_gt_100(self):
        """Common condition: order.total > 100"""
        return ConditionLeaf(
            field_address="order.total", operator=Operator.gt, value=100.0
        )

    @pytest.fixture
    def subscription_status_active(self):
        """Common condition: user.billing.subscription.status == 'active'"""
        return ConditionLeaf(
            field_address="user.billing.subscription.status",
            operator=Operator.eq,
            value="active",
        )

    @pytest.fixture
    def subscription_plan_premium(self):
        """Common condition: user.billing.subscription.plan == 'premium'"""
        return ConditionLeaf(
            field_address="user.billing.subscription.plan",
            operator=Operator.eq,
            value="premium",
        )

    @pytest.fixture
    def user_age_eq_25(self):
        """Common condition: user.age == 25"""
        return ConditionLeaf(field_address="user.age", operator=Operator.eq, value=25)

    # Common condition group fixtures
    @pytest.fixture
    def user_basic_requirements(
        self, user_age_gte_18, user_active_true, user_verified_true
    ):
        """Common condition group: user.age >= 18 AND user.active == True AND user.verified == True"""
        return ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_age_gte_18, user_active_true, user_verified_true],
        )

    @pytest.fixture
    def user_role_or_verified(self, user_role_admin, user_verified_true):
        """Common condition group: user.role == 'admin' OR user.verified == True"""
        return ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[user_role_admin, user_verified_true],
        )

    @pytest.fixture
    def order_requirements(self, order_status_completed, order_total_gt_100):
        """Common condition group: order.status == 'completed' AND order.total > 100"""
        return ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[order_status_completed, order_total_gt_100],
        )


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
        evaluation_result = evaluator.evaluate_rule(condition, sample_data)
        assert evaluation_result.field_address == field
        assert evaluation_result.operator == operator
        assert evaluation_result.expected_value == value
        assert evaluation_result.result == expected_result
        assert (
            evaluation_result.message
            == f"Condition '{field} {operator} {value}' evaluated to {expected_result}"
        )

    def test_leaf_condition_with_colon_separated_field_address(self, evaluator):
        """Test leaf condition evaluation with colon-separated field addresses"""
        # Test colon-separated field address like "dataset:collection:field"
        condition = ConditionLeaf(
            field_address="user:profile:age", operator=Operator.eq, value=25
        )

        data = {"user": {"profile": {"age": 25}}}

        result = evaluator.evaluate_rule(condition, data)
        assert result.result is True
        assert result.field_address == "user:profile:age"

    def test_get_nested_value_from_dict_attribute_error_handling(self, evaluator):
        """Test that AttributeError exceptions in _get_nested_value_from_dict are properly handled"""
        # Test with data that will cause AttributeError when calling .get()
        data = {"user": "not_a_dict"}  # String doesn't have .get method
        keys = ["user", "field"]

        # This should return None due to AttributeError handling
        result = evaluator._get_nested_value_from_dict(data, keys)
        assert result is None

    def test_get_nested_value_empty_keys(self, evaluator):
        """Test _get_nested_value with empty keys list"""
        data = {"test": "value"}
        result = evaluator._get_nested_value(data, [])
        assert result == data

    def test_get_nested_value_fides_reference_structure_fallback(self, evaluator):
        """Test that _get_nested_value falls back to dict access when Fides reference structure fails"""
        # Create data that will fail Fides reference structure validation
        data = {"user": {"profile": {"age": 25}}}
        keys = ["user", "profile", "age"]

        # This should fall back to dict access and succeed
        result = evaluator._get_nested_value(data, keys)
        assert result == 25


class TestGroupConditionEvaluation(TestConditionEvaluator):
    """Test group condition evaluation"""

    def test_and_group_all_true(
        self,
        evaluator,
        sample_data,
        user_age_gte_18,
        user_active_true,
        user_score_gt_90,
    ):
        """Test AND group with all conditions true"""
        group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_age_gte_18, user_active_true, user_score_gt_90],
        )
        evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.and_
        assert len(evaluation_result.condition_results) == 3
        assert all(result.result for result in evaluation_result.condition_results)
        assert evaluation_result.result is True

    def test_and_group_one_false(
        self, evaluator, sample_data, user_age_gte_18, user_active_true
    ):
        """Test AND group with one condition false"""
        # Create a condition that will be false
        user_score_gt_100 = ConditionLeaf(
            field_address="user.score", operator=Operator.gt, value=100
        )

        group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_age_gte_18, user_active_true, user_score_gt_100],
        )
        evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.and_
        assert len(evaluation_result.condition_results) == 3
        assert evaluation_result.condition_results[2].result is False
        assert evaluation_result.result is False

    def test_or_group_one_true(self, evaluator, sample_data, user_active_true):
        """Test OR group with one condition true"""
        # Create conditions that will be false
        user_age_lt_18 = ConditionLeaf(
            field_address="user.age", operator=Operator.lt, value=18
        )
        user_score_lt_90 = ConditionLeaf(
            field_address="user.score", operator=Operator.lt, value=90
        )

        group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[user_age_lt_18, user_active_true, user_score_lt_90],
        )
        evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.or_
        assert len(evaluation_result.condition_results) == 3
        assert evaluation_result.condition_results[1].result is True
        assert evaluation_result.result is True

    def test_or_group_all_false(self, evaluator, sample_data):
        """Test OR group with all conditions false"""
        # Create conditions that will be false
        user_age_lt_18 = ConditionLeaf(
            field_address="user.age", operator=Operator.lt, value=18
        )
        user_active_false = ConditionLeaf(
            field_address="user.active", operator=Operator.eq, value=False
        )
        user_score_lt_90 = ConditionLeaf(
            field_address="user.score", operator=Operator.lt, value=90
        )

        group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[user_age_lt_18, user_active_false, user_score_lt_90],
        )
        evaluation_result = evaluator.evaluate_rule(group, sample_data)
        assert evaluation_result.logical_operator == GroupOperator.or_
        assert len(evaluation_result.condition_results) == 3
        assert not any(result.result for result in evaluation_result.condition_results)
        assert evaluation_result.result is False


class TestNestedGroupEvaluation(TestConditionEvaluator):
    """Test nested group condition evaluation"""

    def test_nested_and_or_groups(
        self,
        evaluator,
        sample_data,
        user_age_gte_18,
        user_role_admin,
        user_verified_true,
    ):
        """Test nested AND/OR groups"""
        # Structure: (user.age >= 18 AND (user.role = 'admin' OR user.verified = true))
        inner_group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[user_role_admin, user_verified_true],
        )

        outer_group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_age_gte_18, inner_group],
        )

        evaluation_result = evaluator.evaluate_rule(outer_group, sample_data)
        # user.age >= 18 is True, user.verified = True is True, so result should be True
        assert evaluation_result.result is True

    def test_complex_nested_structure(
        self,
        evaluator,
        sample_data,
        user_age_gte_18,
        user_active_true,
        user_role_admin,
        user_verified_true,
        user_name_exists,
    ):
        """Test complex nested structure"""
        # Structure: ((A AND B) OR (C AND D)) AND E
        # Where A=user.age>=18, B=user.active=True, C=user.role='admin', D=user.verified=True, E=user.name exists

        inner_group_1 = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_age_gte_18, user_active_true],  # True AND True = True
        )

        inner_group_2 = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_role_admin, user_verified_true],  # False AND True = False
        )

        middle_group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[inner_group_1, inner_group_2],  # True OR False = True
        )

        outer_group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[middle_group, user_name_exists],  # True AND True = True
        )

        evaluation_result = evaluator.evaluate_rule(outer_group, sample_data)
        assert evaluation_result.result is True

    def test_deep_nesting(
        self,
        evaluator,
        sample_data,
        user_role_admin,
        user_verified_true,
        user_active_true,
        user_name_exists,
    ):
        """Test very deep nesting"""
        # Create a deeply nested structure: (((A OR B) AND C) OR D) AND E
        deepest = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[user_role_admin, user_verified_true],  # False OR True = True
        )

        level_2 = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                deepest,  # True (OR of False and True)
                user_active_true,  # True
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
                user_name_exists,  # True
            ],
        )

        evaluation_result = evaluator.evaluate_rule(outermost, sample_data)
        assert evaluation_result.result is True

    def test_mixed_conditions_in_group(
        self, evaluator, sample_data, user_verified_true
    ):
        """Test mixing ConditionLeaf and ConditionGroup in the same group"""
        # Create additional conditions for this test
        user_premium_true = ConditionLeaf(
            field_address="user.premium", operator=Operator.eq, value=True
        )
        user_admin_true = ConditionLeaf(
            field_address="user.admin", operator=Operator.eq, value=True
        )
        user_moderator_true = ConditionLeaf(
            field_address="user.moderator", operator=Operator.eq, value=True
        )

        inner_group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_verified_true, user_premium_true],
        )

        mixed_group = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[user_admin_true, inner_group, user_moderator_true],
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
        # Create a condition for this test
        field_address_operator = ConditionLeaf(
            field_address=field_address, operator=operator
        )
        if data == "sample_data":
            data = sample_data

        evaluation_result = evaluator.evaluate_rule(field_address_operator, data)
        assert evaluation_result.result is expected_result

    def test_none_value_comparison(self, evaluator, sample_data):
        """Test comparison with None values"""
        # Create a condition for this test
        missing_field_eq_none = ConditionLeaf(
            field_address="missing_field", operator=Operator.eq, value=None
        )

        evaluation_result = evaluator.evaluate_rule(missing_field_eq_none, sample_data)
        assert evaluation_result.result is True

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
        # Create a condition for this test
        field_address_eq_value = ConditionLeaf(
            field_address="field_address", operator=Operator.eq, value=user_input_value
        )

        evaluation_result = evaluator.evaluate_rule(field_address_eq_value, data)
        assert evaluation_result.result is True


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

    def test_complex_real_world_scenario(
        self,
        evaluator,
        sample_data,
        user_age_gte_18,
        user_active_true,
        user_role_admin,
        user_verified_true,
        subscription_status_active,
    ):
        """Test a complex real-world scenario"""
        # Scenario: User must be 18+, active, and either have admin role OR be verified
        # AND their subscription must be active
        role_or_verified = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[user_role_admin, user_verified_true],
        )

        user_requirements = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_age_gte_18, user_active_true, role_or_verified],
        )

        final_rule = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_requirements, subscription_status_active],
        )

        evaluation_result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: age=25>=18, active=True, verified=True, subscription=active
        assert evaluation_result.result is True

    def test_order_processing_scenario(
        self,
        evaluator,
        sample_data,
        order_status_completed,
        order_total_gt_100,
        subscription_plan_premium,
    ):
        """Test order processing scenario"""
        # Scenario: Order must be completed AND total > 100 OR user is premium
        order_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[order_status_completed, order_total_gt_100],
        )

        final_rule = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[order_condition, subscription_plan_premium],
        )

        evaluation_result = evaluator.evaluate_rule(final_rule, sample_data)
        # Should be True: order.status=completed, order.total=150>100
        assert evaluation_result.result is True

    def test_fides_reference_scenario(self, evaluator, mock_fides_data):
        """Test scenario using Fides reference structures"""
        # Test that the evaluator works with Fides data structures
        condition = ConditionLeaf(
            field_address="customer.email", operator=Operator.eq, value="test_value"
        )

        evaluation_result = evaluator.evaluate_rule(condition, mock_fides_data)
        assert evaluation_result.result is True

    @pytest.mark.parametrize(
        "field_address,operator,value,expected_result,description",
        [
            # Test list_contains operator - check if user.roles contains "admin"
            param(
                "user.roles",
                Operator.list_contains,
                "admin",
                True,
                "roles contains admin",
            ),
            # Test not_in_list operator
            param(
                "user.roles",
                Operator.not_in_list,
                ["guest", "anonymous"],
                True,
                "roles not in guest/anonymous",
            ),
            # Test list_contains operator with permissions
            param(
                "user.permissions",
                Operator.list_contains,
                "write",
                True,
                "permissions contains write",
            ),
        ],
    )
    def test_list_operators_integration(
        self,
        evaluator,
        field_address,
        operator,
        value,
        expected_result,
        description,
        data_set,
    ):
        """Test integration of list operators in complex scenarios"""
        data = data_set

        condition = ConditionLeaf(
            field_address=field_address, operator=operator, value=value
        )
        evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is expected_result

    def test_complex_list_condition_group(
        self, evaluator, data_set, order_status_completed
    ):
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

        role_or_permission = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[role_condition, permission_condition],
        )

        final_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[role_or_permission, order_status_completed],
        )

        evaluation_result = evaluator.evaluate_rule(final_condition, data)
        assert evaluation_result.result is True

    def test_list_operators_with_nested_data(self, evaluator, data_set):
        """Test list operators with deeply nested data structures"""
        data = data_set

        # Test nested field access with list operators
        condition = ConditionLeaf(
            field_address="user.profile.interests",
            operator=Operator.list_contains,
            value="programming",
        )
        evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is True

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

        evaluation_result = evaluator.evaluate_rule(combined_condition, data)
        assert evaluation_result.result is True

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

        condition = ConditionLeaf(
            field_address=field_address,
            operator=operator,
            value=value,
        )
        evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is expected_result

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
        evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is expected_result

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
        evaluation_result = evaluator.evaluate_rule(condition, data)
        assert evaluation_result.result is expected_result


class TestErrorHandling(TestConditionEvaluator):
    """Test error handling when conditions fail"""

    @pytest.fixture
    def fallback_fides_data(self):
        """Create an object that has both get_field_value and get methods"""

        class FidesDataWithFallback:
            def __init__(self):
                self.data = {"field_name": "fallback_value"}

            def get_field_value(self, field_path):
                raise ValueError("Simulated Fides access error")

            def get(self, key, default=None):
                return self.data.get(key, default)

        return FidesDataWithFallback()

    def _raise_attribute_error_dict(self):
        """Helper function to raise AttributeError for dict access"""
        raise AttributeError("Simulated dict access error")

    def _raise_attribute_error(self):
        """Helper function to raise AttributeError"""
        raise AttributeError("No such method")

    def _raise_runtime_error(self):
        """Helper function to raise RuntimeError"""
        raise RuntimeError("Simulated uncaught exception")

    def test_unknown_operator_raises_error(self, evaluator):
        """Test that unknown operators raise ConditionEvaluationError"""
        # Test the _apply_operator method directly where the unknown operator error occurs
        with pytest.raises(
            ConditionEvaluationError, match="Unknown operator: invalid_operator"
        ):
            evaluator._apply_operator(
                "test_value", "invalid_operator", "expected_value"
            )

    @pytest.mark.parametrize(
        "leaf,data,expected_result",
        [
            param(
                ConditionLeaf(
                    field_address="user.name", operator=Operator.gt, value=10
                ),
                {"user": {"name": "john"}},
                False,
                id="numeric_operator_on_string",
            ),
            param(
                ConditionLeaf(
                    field_address="user.age", operator=Operator.starts_with, value="2"
                ),
                {"user": {"age": 25}},
                False,
                id="string_operator_on_number",
            ),
            param(
                ConditionLeaf(
                    field_address="user.name",
                    operator=Operator.list_contains,
                    value="admin",
                ),
                {"user": {"name": "john"}},
                False,
                id="list_operator_on_non_list",
            ),
        ],
    )
    def test_graceful_handling_of_type_mismatches(
        self, evaluator, leaf, data, expected_result
    ):
        """Test that type mismatches are handled gracefully by operators"""
        # These should NOT raise errors - they should return False gracefully
        evaluation_result = evaluator.evaluate_rule(leaf, data)
        assert evaluation_result.result is expected_result

    def test_hasattr_failure_handling(self, evaluator):
        """Test that hasattr failures are raised (not handled gracefully)"""
        # Create a simple object
        obj = {"field_name": "test_value"}

        # Mock hasattr to raise an exception
        with patch(
            "builtins.hasattr", side_effect=Exception("Simulated hasattr error")
        ):
            # This should raise the exception since hasattr failures are not caught
            with pytest.raises(Exception, match="Simulated hasattr error"):
                evaluator._get_nested_value(obj, ["field_name"])

    def test_complex_fallback_scenario(self, evaluator, fallback_fides_data):
        """Test a complex scenario with multiple fallback mechanisms"""

        # Modify the fixture to also fail on dict access
        fallback_fides_data.get = (
            lambda key, default=None: self._raise_attribute_error_dict()
        )

        # This should return None for evaluation purposes as the value is not present
        # in the data structure and this is still valid for operations like exists, not_exists, etc.
        value = evaluator._get_nested_value(fallback_fides_data, ["field_name"])
        assert value is None

    def test_get_nested_value_exception_propagation(
        self, evaluator, fallback_fides_data, user_age_eq_25
    ):
        """Test that exceptions from _get_nested_value properly propagate to evaluate_rule"""

        # Modify the fixture to raise RuntimeError
        fallback_fides_data.get_field_value = (
            lambda field_path: self._raise_runtime_error()
        )

        # This should raise the RuntimeError directly since _get_nested_value doesn't catch it
        # and the exception propagates up to evaluate_rule
        with pytest.raises(RuntimeError, match="Simulated uncaught exception"):
            evaluator.evaluate_rule(user_age_eq_25, fallback_fides_data)

    @pytest.mark.parametrize(
        "error_type,error_message",
        [
            param(
                "evaluate_rule",
                "Simulated error in evaluate_rule",
                id="evaluate_rule_error",
            ),
            param(
                "logical_operator",
                "Unknown logical operator: invalid_operator",
                id="logical_operator_error",
            ),
        ],
    )
    def test_error_in_group_condition_handling(
        self,
        evaluator,
        sample_data,
        user_name_john_doe,
        user_age_eq_25,
        error_type,
        error_message,
    ):
        """Test that various errors in group condition evaluation are properly handled"""
        group = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[user_name_john_doe, user_age_eq_25],
        )

        if error_type == "evaluate_rule":
            # Mock evaluate_rule to raise an exception for the second condition
            def failing_evaluate_rule(condition, data):
                if (
                    hasattr(condition, "field_address")
                    and condition.field_address == "user.age"
                ):
                    raise ConditionEvaluationError(error_message)
                return True, Mock(
                    autospec=True, result=True
                )  # Return a mock result for successful conditions

            with patch.object(
                evaluator, "evaluate_rule", side_effect=failing_evaluate_rule
            ):

                # This should raise the ConditionEvaluationError from the failing evaluate_rule call
                with pytest.raises(ConditionEvaluationError, match=error_message):
                    evaluator._evaluate_group_condition(group, sample_data)
        else:
            group.logical_operator = "invalid_operator"
            # This should raise the exception from the logical operator function
            with pytest.raises(ConditionEvaluationError, match=error_message):
                evaluator._evaluate_group_condition(group, sample_data)

    def test_error_in_leaf_condition_operator_application(
        self, evaluator, user_age_eq_25
    ):
        """Test that errors in _apply_operator are properly caught and re-raised"""
        # Mock _apply_operator to raise a ConditionEvaluationError
        with patch.object(
            evaluator,
            "_apply_operator",
            side_effect=ConditionEvaluationError("Simulated operator error"),
        ):
            # This should catch the ConditionEvaluationError and re-raise it
            with pytest.raises(
                ConditionEvaluationError, match="Simulated operator error"
            ):
                evaluator.evaluate_rule(user_age_eq_25, {"user": {"age": 25}})

    @pytest.mark.parametrize(
        "operator_type,invalid_value,expected_error_message,description",
        [
            param(
                "logical_operator",
                "invalid_operator",
                "Unknown logical operator: invalid_operator",
                "logical operator",
                id="invalid_logical_operator",
            ),
            param(
                "operator",
                "invalid_operator",
                "invalid_operator",
                "operator",
                id="invalid_operator",
            ),
        ],
    )
    def test_invalid_operator_handling(
        self,
        evaluator,
        sample_data,
        user_name_john_doe,
        operator_type,
        invalid_value,
        expected_error_message,
        description,
    ):
        """Test that invalid operators raise appropriate errors when accessing operator dicts"""

        if operator_type == "logical_operator":
            # Create a valid group first, then modify it to have an invalid operator
            group = ConditionGroup(
                logical_operator=GroupOperator.and_,
                conditions=[user_name_john_doe],
            )

            # Manually set an invalid logical operator to bypass Pydantic validation
            group.logical_operator = invalid_value

            # This should raise a ConditionEvaluationError when trying to access logical_operators["invalid_operator"]
            with pytest.raises(ConditionEvaluationError, match=expected_error_message):
                evaluator._evaluate_group_condition(group, sample_data)
        else:
            # Create a valid condition first, then modify it to have an invalid operator
            condition = ConditionLeaf(
                field_address="user.age", operator=Operator.eq, value=25
            )

            # Manually set an invalid operator to bypass Pydantic validation
            condition.operator = invalid_value

            data = {"user": {"age": 25}}

            # This should raise a ConditionEvaluationError when trying to access operator_methods["invalid_operator"]
            with pytest.raises(ConditionEvaluationError, match=expected_error_message):
                evaluator.evaluate_rule(condition, data)

    def test_operator_runtime_exception_handling(self, evaluator):
        """Test that runtime exceptions from operator methods are caught and re-raised as ConditionEvaluationError"""

        # Mock the operator method to raise a runtime exception
        def failing_operator(data_value, user_input_value):
            raise RuntimeError("Simulated operator runtime error")

        with patch.dict(
            "fides.api.task.conditional_dependencies.evaluator.OPERATOR_METHODS",
            {Operator.eq: failing_operator},
        ):
            # This should catch the RuntimeError and re-raise it as ConditionEvaluationError
            with pytest.raises(
                ConditionEvaluationError,
                match="Unexpected error evaluating condition: Simulated operator runtime error",
            ):
                evaluator._apply_operator(25, Operator.eq, 25)

    @pytest.mark.parametrize(
        "exception_class,exception_message,description",
        [
            param(
                ValueError,
                "Invalid field path",
                "ValueError from Fides reference structure",
                id="value_error",
            ),
            param(
                ConditionEvaluationError,
                "Condition evaluation error",
                "ConditionEvaluationError from Fides reference structure",
                id="condition_evaluation_error",
            ),
            param(
                AttributeError,
                "Fides reference structure attribute error",
                "AttributeError from Fides reference structure",
                id="attribute_error",
            ),
        ],
    )
    def test_fides_reference_structure_error_handling(
        self, evaluator, exception_class, exception_message, description
    ):
        """Test that various Fides reference structure errors are properly handled"""

        # Create data that looks like a Fides reference structure but will fail validation
        class MockFidesStructure:
            def get_field_value(self, field_path):
                raise exception_class(exception_message)

        data = MockFidesStructure()
        keys = ["user", "profile", "age"]

        # This should raise the specific exception from the Fides reference structure
        with pytest.raises(exception_class, match=exception_message):
            evaluator._get_nested_value_from_fides_reference_structure(data, keys)
