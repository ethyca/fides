import pytest
from pydantic import ValidationError

from fideslang.models.policy import Policy, PolicyRule, PrivacyRule
from fideslang.models.validation import FidesValidationError


@pytest.mark.unit
def test_valid_privacy_rule():
    privacy_rule = PrivacyRule(inclusion="ANY", values=["foo_bar"])
    assert privacy_rule


@pytest.mark.unit
def test_invalid_fides_key_privacy_rule():
    with pytest.raises(FidesValidationError):
        PrivacyRule(inclusion="ANY", values=["foo-bar"])
    assert True


@pytest.mark.unit
def test_invalid_inclusion_privacy_rule():
    with pytest.raises(ValidationError):
        PrivacyRule(inclusion="AN", values=["foo_bar"])
    assert True


@pytest.mark.unit
def test_valid_policy_rule():
    PolicyRule(
        organizationId=1,
        policyId=1,
        fidesKey="test_policy",
        name="Test Policy",
        description="Test Policy",
        dataCategories=PrivacyRule(inclusion="NONE", values=[]),
        dataUses=PrivacyRule(inclusion="NONE", values=["provide"]),
        dataSubjects=PrivacyRule(inclusion="ANY", values=[]),
        dataQualifier="unlinked_pseudonymized_data",
        action="REJECT",
    ),
    assert True


@pytest.mark.unit
def test_invalid_action_enum_policy_rule():
    with pytest.raises(ValidationError):
        PolicyRule(
            organizationId=1,
            policyId=1,
            fidesKey="test_policy",
            name="Test Policy",
            description="Test Policy",
            dataCategories=PrivacyRule(inclusion="NONE", values=[]),
            dataUses=PrivacyRule(inclusion="NONE", values=["provide"]),
            dataSubjects=PrivacyRule(inclusion="ANY", values=[]),
            dataQualifier="unlinked_pseudonymized_data",
            action="REJT",
        ),
    assert True


@pytest.mark.unit
def test_valid_policy():
    Policy(
        organizationId=1,
        fidesKey="test_policy",
        name="Test Policy",
        version="1.3",
        description="Test Policy",
        rules=[],
    )
    assert True
