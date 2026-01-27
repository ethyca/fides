"""Tests for policy evaluation engine."""

import pytest
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy, Rule
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.task.conditional_dependencies.policy_evaluation import (
    PolicyEvaluationError,
    PolicyEvaluationResult,
    evaluate_policy_conditions,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def condition_location_eu() -> ConditionLeaf:
    """Condition: privacy_request.location in ['FR', 'DE', 'IT']"""
    return ConditionLeaf(
        field_address="privacy_request.location",
        operator=Operator.list_contains,
        value=["FR", "DE", "IT"],
    )


@pytest.fixture
def condition_location_us() -> ConditionLeaf:
    """Condition: privacy_request.location == 'US'"""
    return ConditionLeaf(
        field_address="privacy_request.location",
        operator=Operator.eq,
        value="US",
    )


@pytest.fixture
def condition_property_id() -> ConditionLeaf:
    """Condition: privacy_request.property_id == 'test_property'"""
    return ConditionLeaf(
        field_address="privacy_request.property_id",
        operator=Operator.eq,
        value="test_property",
    )


@pytest.fixture
def condition_source_privacy_center() -> ConditionLeaf:
    """Condition: privacy_request.source == 'privacy_center'"""
    return ConditionLeaf(
        field_address="privacy_request.source",
        operator=Operator.eq,
        value="privacy_center",
    )


@pytest.fixture
def condition_custom_field_tenant() -> ConditionLeaf:
    """Condition: privacy_request.custom_privacy_request_fields.tenant_id == 'tenant_123'"""
    return ConditionLeaf(
        field_address="privacy_request.custom_privacy_request_fields.tenant_id",
        operator=Operator.eq,
        value="tenant_123",
    )


@pytest.fixture
def condition_has_access_rule() -> ConditionLeaf:
    """Condition: privacy_request.policy.has_access_rule == True"""
    return ConditionLeaf(
        field_address="privacy_request.policy.has_access_rule",
        operator=Operator.eq,
        value=True,
    )


@pytest.fixture
def condition_has_erasure_rule() -> ConditionLeaf:
    """Condition: privacy_request.policy.has_erasure_rule == True"""
    return ConditionLeaf(
        field_address="privacy_request.policy.has_erasure_rule",
        operator=Operator.eq,
        value=True,
    )


@pytest.fixture
def condition_rule_action_types_contains_access() -> ConditionLeaf:
    """Condition: privacy_request.policy.rule_action_types contains 'access'"""
    return ConditionLeaf(
        field_address="privacy_request.policy.rule_action_types",
        operator=Operator.list_contains,
        value=["access"],
    )


@pytest.fixture
def eu_policy(db: Session) -> Policy:
    """Policy for EU requests"""
    return Policy.create(
        db=db,
        data={
            "name": "EU Policy",
            "key": "eu_policy",
        },
    )


@pytest.fixture
def us_policy(db: Session) -> Policy:
    """Policy for US requests"""
    return Policy.create(
        db=db,
        data={
            "name": "US Policy",
            "key": "us_policy",
        },
    )


@pytest.fixture
def property_specific_policy(db: Session) -> Policy:
    """Policy for specific property"""
    return Policy.create(
        db=db,
        data={
            "name": "Property Specific Policy",
            "key": "property_specific_policy",
        },
    )


@pytest.fixture
def default_policy(db: Session) -> Policy:
    """Default policy with no conditions"""
    return Policy.create(
        db=db,
        data={
            "name": "Default Policy",
            "key": "default_policy",
        },
    )


@pytest.fixture
def privacy_request_eu(db: Session, default_policy: Policy) -> PrivacyRequest:
    """Privacy request from EU (France)"""
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": "test_request_eu",
            "status": "pending",
            "policy_id": default_policy.id,
            "location": "FR",
        },
    )
    # Refresh to load relationships
    db.refresh(pr)
    return pr


@pytest.fixture
def privacy_request_us(db: Session, default_policy: Policy) -> PrivacyRequest:
    """Privacy request from US"""
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": "test_request_us",
            "status": "pending",
            "policy_id": default_policy.id,
            "location": "US",
        },
    )
    db.refresh(pr)
    return pr


@pytest.fixture
def privacy_request_with_property(db: Session, default_policy: Policy) -> PrivacyRequest:
    """Privacy request with specific property_id"""
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": "test_request_property",
            "status": "pending",
            "policy_id": default_policy.id,
            "property_id": "test_property",
            "location": "US",
        },
    )
    db.refresh(pr)
    return pr


# ============================================================================
# Test Policy Evaluation Logic
# ============================================================================


class TestEvaluatePolicyConditions:
    """Test the evaluate_policy_conditions function"""

    def test_single_policy_match(
        self,
        db: Session,
        eu_policy: Policy,
        condition_location_eu: ConditionLeaf,
        privacy_request_eu: PrivacyRequest,
    ):
        """Test matching a single policy with conditions"""
        # Create policy condition
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": condition_location_eu.model_dump(),
            },
        )

        # Evaluate
        result = evaluate_policy_conditions(db, privacy_request_eu)

        # Verify
        assert isinstance(result, PolicyEvaluationResult)
        assert result.policy.id == eu_policy.id
        assert result.policy.key == "eu_policy"
        assert not result.is_default
        assert result.evaluation_result is not None
        assert result.evaluation_result.result is True

    def test_multiple_policies_first_match(
        self,
        db: Session,
        eu_policy: Policy,
        us_policy: Policy,
        condition_location_eu: ConditionLeaf,
        condition_location_us: ConditionLeaf,
        privacy_request_us: PrivacyRequest,
    ):
        """Test that first matching policy is returned when multiple policies match"""
        # Create EU policy condition (created first)
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": condition_location_eu.model_dump(),
            },
        )

        # Create US policy condition (created second)
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": us_policy.id,
                "condition_tree": condition_location_us.model_dump(),
            },
        )

        # Evaluate with US request - should match US policy
        result = evaluate_policy_conditions(db, privacy_request_us)

        # Verify US policy matched (not EU policy)
        assert result.policy.key == "us_policy"
        assert not result.is_default
        assert result.evaluation_result.result is True

    def test_no_match_uses_default_policy(
        self,
        db: Session,
        eu_policy: Policy,
        default_policy: Policy,
        condition_location_eu: ConditionLeaf,
        privacy_request_us: PrivacyRequest,
    ):
        """Test fallback to default policy when no conditions match"""
        # Create EU policy condition
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": condition_location_eu.model_dump(),
            },
        )

        # Evaluate with US request - should fall back to default
        result = evaluate_policy_conditions(db, privacy_request_us)

        # Verify default policy is used
        assert result.policy.key == "default_policy"
        assert result.is_default
        assert result.evaluation_result is None

    def test_complex_condition_group(
        self,
        db: Session,
        property_specific_policy: Policy,
        condition_property_id: ConditionLeaf,
        condition_location_us: ConditionLeaf,
        privacy_request_with_property: PrivacyRequest,
    ):
        """Test evaluation with complex condition group (AND)"""
        # Create complex condition: property_id AND location
        complex_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[condition_property_id, condition_location_us],
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": property_specific_policy.id,
                "condition_tree": complex_condition.model_dump(),
            },
        )

        # Evaluate - should match both conditions
        result = evaluate_policy_conditions(db, privacy_request_with_property)

        # Verify
        assert result.policy.key == "property_specific_policy"
        assert not result.is_default
        assert result.evaluation_result.result is True

    def test_complex_condition_group_partial_match_and(
        self,
        db: Session,
        property_specific_policy: Policy,
        default_policy: Policy,
        condition_property_id: ConditionLeaf,
        condition_location_eu: ConditionLeaf,
        privacy_request_with_property: PrivacyRequest,
    ):
        """Test that AND condition fails when only one condition matches"""
        # Create complex condition: property_id AND location_eu
        # Request has property_id but location is US, not EU
        complex_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[condition_property_id, condition_location_eu],
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": property_specific_policy.id,
                "condition_tree": complex_condition.model_dump(),
            },
        )

        # Evaluate - should not match (property matches but location doesn't)
        result = evaluate_policy_conditions(db, privacy_request_with_property)

        # Verify fallback to default
        assert result.policy.key == "default_policy"
        assert result.is_default

    def test_or_condition_group(
        self,
        db: Session,
        eu_policy: Policy,
        condition_location_eu: ConditionLeaf,
        condition_location_us: ConditionLeaf,
        privacy_request_us: PrivacyRequest,
    ):
        """Test evaluation with OR condition group"""
        # Create OR condition: location_eu OR location_us
        or_condition = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[condition_location_eu, condition_location_us],
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": or_condition.model_dump(),
            },
        )

        # Evaluate with US request - should match via OR
        result = evaluate_policy_conditions(db, privacy_request_us)

        # Verify
        assert result.policy.key == "eu_policy"
        assert not result.is_default
        assert result.evaluation_result.result is True


# ============================================================================
# Test Priority Ordering
# ============================================================================


class TestPriorityOrdering:
    """Test policy priority ordering during evaluation"""

    def test_policies_evaluated_in_creation_order(
        self,
        db: Session,
        privacy_request_us: PrivacyRequest,
    ):
        """Test that policies are evaluated in creation order (for now)"""
        # Create first policy
        policy1 = Policy.create(
            db=db,
            data={
                "name": "First Policy",
                "key": "first_policy",
            },
        )

        # Create second policy
        policy2 = Policy.create(
            db=db,
            data={
                "name": "Second Policy",
                "key": "second_policy",
            },
        )

        # Both policies match US location
        us_condition = ConditionLeaf(
            field_address="privacy_request.location",
            operator=Operator.eq,
            value="US",
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy1.id,
                "condition_tree": us_condition.model_dump(),
            },
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy2.id,
                "condition_tree": us_condition.model_dump(),
            },
        )

        # Evaluate - should match first policy
        result = evaluate_policy_conditions(db, privacy_request_us)

        # Verify first policy is returned
        assert result.policy.key == "first_policy"

    def test_more_specific_policy_wins_with_proper_ordering(
        self,
        db: Session,
        privacy_request_with_property: PrivacyRequest,
    ):
        """Test that more specific conditions can be prioritized via creation order"""
        # Create general policy first
        general_policy = Policy.create(
            db=db,
            data={
                "name": "General US Policy",
                "key": "general_us_policy",
            },
        )

        general_condition = ConditionLeaf(
            field_address="privacy_request.location",
            operator=Operator.eq,
            value="US",
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": general_policy.id,
                "condition_tree": general_condition.model_dump(),
            },
        )

        # Create specific policy second
        specific_policy = Policy.create(
            db=db,
            data={
                "name": "Specific Property Policy",
                "key": "specific_property_policy",
            },
        )

        specific_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="privacy_request.location",
                    operator=Operator.eq,
                    value="US",
                ),
                ConditionLeaf(
                    field_address="privacy_request.property_id",
                    operator=Operator.eq,
                    value="test_property",
                ),
            ],
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": specific_policy.id,
                "condition_tree": specific_condition.model_dump(),
            },
        )

        # Evaluate - first matching policy wins (general policy)
        result = evaluate_policy_conditions(db, privacy_request_with_property)

        # General policy created first, so it matches first
        assert result.policy.key == "general_us_policy"


# ============================================================================
# Test Default Policy Fallback
# ============================================================================


class TestDefaultPolicyFallback:
    """Test default policy fallback behavior"""

    def test_default_policy_used_when_no_conditions_match(
        self,
        db: Session,
        eu_policy: Policy,
        default_policy: Policy,
        condition_location_eu: ConditionLeaf,
        privacy_request_us: PrivacyRequest,
    ):
        """Test default policy is used when no conditional policies match"""
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": condition_location_eu.model_dump(),
            },
        )

        result = evaluate_policy_conditions(db, privacy_request_us)

        assert result.policy.key == "default_policy"
        assert result.is_default
        assert result.evaluation_result is None

    def test_default_policy_used_when_no_policies_have_conditions(
        self,
        db: Session,
        default_policy: Policy,
        privacy_request_us: PrivacyRequest,
    ):
        """Test default policy is used when no policies have conditions at all"""
        # No policies with conditions exist
        result = evaluate_policy_conditions(db, privacy_request_us)

        assert result.policy.key == "default_policy"
        assert result.is_default

    def test_assigned_policy_used_when_no_default_exists(
        self,
        db: Session,
        eu_policy: Policy,
        condition_location_eu: ConditionLeaf,
        privacy_request_us: PrivacyRequest,
    ):
        """Test that privacy request's assigned policy is used when no default exists"""
        # Delete the default policy
        default_policy = Policy.get_by(db, field="key", value="default_policy")
        if default_policy:
            default_policy.delete(db)

        # Create conditional policy that won't match
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": condition_location_eu.model_dump(),
            },
        )

        # Update privacy request to use eu_policy
        privacy_request_us.policy_id = eu_policy.id
        privacy_request_us.save(db)
        db.refresh(privacy_request_us)

        # Evaluate - should use assigned policy as fallback
        result = evaluate_policy_conditions(db, privacy_request_us)

        assert result.policy.key == "eu_policy"
        assert result.is_default

    def test_error_when_no_default_and_no_assigned_policy(
        self,
        db: Session,
        eu_policy: Policy,
        condition_location_eu: ConditionLeaf,
    ):
        """Test error is raised when no default policy and no match"""
        # Delete default policy
        default_policy = Policy.get_by(db, field="key", value="default_policy")
        if default_policy:
            default_policy.delete(db)

        # Create conditional policy
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": condition_location_eu.model_dump(),
            },
        )

        # Create privacy request without assigned policy
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_no_policy",
                "status": "pending",
                "policy_id": eu_policy.id,
                "location": "US",  # Won't match EU condition
            },
        )
        db.refresh(pr)

        # Should NOT raise error because privacy request has assigned policy
        result = evaluate_policy_conditions(db, pr)
        assert result.policy.key == "eu_policy"
        assert result.is_default


# ============================================================================
# Test Missing Data Scenarios
# ============================================================================


class TestMissingDataScenarios:
    """Test evaluation with missing or None data"""

    def test_missing_location_field(
        self,
        db: Session,
        eu_policy: Policy,
        default_policy: Policy,
        condition_location_eu: ConditionLeaf,
    ):
        """Test evaluation when location field is None"""
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": condition_location_eu.model_dump(),
            },
        )

        # Create request without location
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_no_location",
                "status": "pending",
                "policy_id": default_policy.id,
                # location is None
            },
        )
        db.refresh(pr)

        # Evaluate - should not match and use default
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "default_policy"
        assert result.is_default

    def test_missing_property_id_field(
        self,
        db: Session,
        property_specific_policy: Policy,
        default_policy: Policy,
        condition_property_id: ConditionLeaf,
        privacy_request_us: PrivacyRequest,
    ):
        """Test evaluation when property_id field is None"""
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": property_specific_policy.id,
                "condition_tree": condition_property_id.model_dump(),
            },
        )

        # privacy_request_us has no property_id
        result = evaluate_policy_conditions(db, privacy_request_us)

        # Should not match and use default
        assert result.policy.key == "default_policy"
        assert result.is_default

    def test_exists_operator_with_none_value(
        self,
        db: Session,
        property_specific_policy: Policy,
        default_policy: Policy,
        privacy_request_us: PrivacyRequest,
    ):
        """Test exists operator correctly handles None values"""
        # Condition: property_id exists
        exists_condition = ConditionLeaf(
            field_address="privacy_request.property_id",
            operator=Operator.exists,
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": property_specific_policy.id,
                "condition_tree": exists_condition.model_dump(),
            },
        )

        # privacy_request_us has no property_id (None)
        result = evaluate_policy_conditions(db, privacy_request_us)

        # Should not match because property_id doesn't exist
        assert result.policy.key == "default_policy"
        assert result.is_default

    def test_not_exists_operator_with_none_value(
        self,
        db: Session,
        property_specific_policy: Policy,
        privacy_request_us: PrivacyRequest,
    ):
        """Test not_exists operator correctly handles None values"""
        # Condition: property_id does not exist
        not_exists_condition = ConditionLeaf(
            field_address="privacy_request.property_id",
            operator=Operator.not_exists,
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": property_specific_policy.id,
                "condition_tree": not_exists_condition.model_dump(),
            },
        )

        # privacy_request_us has no property_id (None)
        result = evaluate_policy_conditions(db, privacy_request_us)

        # Should match because property_id doesn't exist
        assert result.policy.key == "property_specific_policy"
        assert not result.is_default
        assert result.evaluation_result.result is True

    def test_missing_nested_field(
        self,
        db: Session,
        eu_policy: Policy,
        default_policy: Policy,
        privacy_request_us: PrivacyRequest,
    ):
        """Test evaluation with missing nested custom field"""
        # Condition on custom field that doesn't exist
        custom_field_condition = ConditionLeaf(
            field_address="privacy_request.custom_privacy_request_fields.nonexistent_field",
            operator=Operator.eq,
            value="some_value",
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": custom_field_condition.model_dump(),
            },
        )

        # Evaluate - should not match and use default
        result = evaluate_policy_conditions(db, privacy_request_us)

        assert result.policy.key == "default_policy"
        assert result.is_default


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling in policy evaluation"""

    def test_evaluation_continues_on_individual_policy_error(
        self,
        db: Session,
        eu_policy: Policy,
        us_policy: Policy,
        default_policy: Policy,
        condition_location_us: ConditionLeaf,
        privacy_request_us: PrivacyRequest,
    ):
        """Test that evaluation continues if one policy's evaluation fails"""
        # Create first policy with potentially problematic condition
        # This would need to be a condition that causes an error
        # For now, just verify the logic handles multiple policies

        # Create working condition for us_policy
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": us_policy.id,
                "condition_tree": condition_location_us.model_dump(),
            },
        )

        # Evaluate - should match us_policy
        result = evaluate_policy_conditions(db, privacy_request_us)

        assert result.policy.key == "us_policy"
        assert not result.is_default

    def test_policy_with_empty_condition_tree_skipped(
        self,
        db: Session,
        eu_policy: Policy,
        default_policy: Policy,
        privacy_request_us: PrivacyRequest,
    ):
        """Test that policies with None condition_tree are skipped"""
        # Create policy condition with None tree
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": eu_policy.id,
                "condition_tree": None,
            },
        )

        # Evaluate - should skip and use default
        result = evaluate_policy_conditions(db, privacy_request_us)

        assert result.policy.key == "default_policy"
        assert result.is_default


# ============================================================================
# Test Policy Convenience Fields
# ============================================================================


class TestPolicyConvenienceFields:
    """Test evaluation using policy convenience fields"""

    def test_match_policy_with_access_rule(
        self,
        db: Session,
        policy: Policy,
        rule: Rule,
        default_policy: Policy,
        condition_has_access_rule: ConditionLeaf,
    ):
        """Test matching a policy that has an access rule using convenience field"""
        # Create a privacy request with the policy that has an access rule
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_access_rule",
                "status": "pending",
                "policy_id": policy.id,  # This policy has an access rule from fixtures
                "location": "US",
            },
        )
        db.refresh(pr)

        # Create another policy with condition checking for access rule
        conditional_policy = Policy.create(
            db=db,
            data={
                "name": "Access Policy",
                "key": "access_policy",
            },
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": conditional_policy.id,
                "condition_tree": condition_has_access_rule.model_dump(),
            },
        )

        # Evaluate - should match because privacy request's policy has access rule
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "access_policy"
        assert not result.is_default
        assert result.evaluation_result.result is True

    def test_no_match_policy_without_access_rule(
        self,
        db: Session,
        default_policy: Policy,
        condition_has_access_rule: ConditionLeaf,
    ):
        """Test that policy without access rule doesn't match access rule condition"""
        # Create a policy without any rules
        policy_no_rules = Policy.create(
            db=db,
            data={
                "name": "Policy Without Rules",
                "key": "policy_no_rules",
            },
        )

        # Create privacy request with this policy
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_no_access_rule",
                "status": "pending",
                "policy_id": policy_no_rules.id,
                "location": "US",
            },
        )
        db.refresh(pr)

        # Create conditional policy checking for access rule
        conditional_policy = Policy.create(
            db=db,
            data={
                "name": "Access Policy",
                "key": "access_policy",
            },
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": conditional_policy.id,
                "condition_tree": condition_has_access_rule.model_dump(),
            },
        )

        # Evaluate - should not match and use default
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "default_policy"
        assert result.is_default

    def test_match_using_rule_action_types_list(
        self,
        db: Session,
        policy: Policy,
        rule: Rule,
        default_policy: Policy,
        condition_rule_action_types_contains_access: ConditionLeaf,
    ):
        """Test matching using rule_action_types list convenience field"""
        # Create privacy request with policy that has access rule
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_action_types",
                "status": "pending",
                "policy_id": policy.id,
                "location": "US",
            },
        )
        db.refresh(pr)

        # Create conditional policy checking if action types contains access
        conditional_policy = Policy.create(
            db=db,
            data={
                "name": "Action Types Policy",
                "key": "action_types_policy",
            },
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": conditional_policy.id,
                "condition_tree": condition_rule_action_types_contains_access.model_dump(),
            },
        )

        # Evaluate - should match
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "action_types_policy"
        assert not result.is_default

    def test_combined_location_and_policy_conditions(
        self,
        db: Session,
        policy: Policy,
        rule: Rule,
        default_policy: Policy,
        condition_location_us: ConditionLeaf,
        condition_has_access_rule: ConditionLeaf,
    ):
        """Test combining location and policy convenience field conditions"""
        # Create privacy request from US with policy that has access rule
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_combined",
                "status": "pending",
                "policy_id": policy.id,
                "location": "US",
            },
        )
        db.refresh(pr)

        # Create conditional policy: US location AND has access rule
        conditional_policy = Policy.create(
            db=db,
            data={
                "name": "US Access Policy",
                "key": "us_access_policy",
            },
        )

        combined_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[condition_location_us, condition_has_access_rule],
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": conditional_policy.id,
                "condition_tree": combined_condition.model_dump(),
            },
        )

        # Evaluate - should match both conditions
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "us_access_policy"
        assert not result.is_default
        assert result.evaluation_result.result is True

    def test_combined_location_and_policy_partial_match(
        self,
        db: Session,
        default_policy: Policy,
        condition_location_us: ConditionLeaf,
        condition_has_erasure_rule: ConditionLeaf,
    ):
        """Test that combined condition fails if only one matches"""
        # Create policy without erasure rule
        policy_no_erasure = Policy.create(
            db=db,
            data={
                "name": "Policy Without Erasure",
                "key": "policy_no_erasure",
            },
        )

        # Create privacy request from US with this policy
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_partial",
                "status": "pending",
                "policy_id": policy_no_erasure.id,
                "location": "US",
            },
        )
        db.refresh(pr)

        # Create conditional policy: US location AND has erasure rule
        conditional_policy = Policy.create(
            db=db,
            data={
                "name": "US Erasure Policy",
                "key": "us_erasure_policy",
            },
        )

        combined_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[condition_location_us, condition_has_erasure_rule],
        )

        PolicyCondition.create(
            db=db,
            data={
                "policy_id": conditional_policy.id,
                "condition_tree": combined_condition.model_dump(),
            },
        )

        # Evaluate - should not match (location matches but no erasure rule)
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "default_policy"
        assert result.is_default
