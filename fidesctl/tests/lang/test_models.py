import pytest
from pydantic import ValidationError

from fideslang.models import (
    DataCategory,
    DataUse,
    FidesModel,
    Policy,
    PolicyRule,
    PrivacyDeclaration,
    PrivacyRule,
    System,
)

from fideslang.validation import FidesValidationError


@pytest.mark.unit
def test_top_level_resource():
    DataCategory(
        organization_fides_key=1,
        fides_key="user",
        name="Custom Test Data",
        description="Custom Test Data Category",
    )
    assert DataCategory


@pytest.mark.unit
def test_fides_key_doesnt_match_stated_parent_key():
    with pytest.raises(FidesValidationError):
        DataCategory(
            organization_fides_key=1,
            fides_key="user.provided.identifiable.custom_test_data",
            name="Custom Test Data",
            description="Custom Test Data Category",
            parent_key="user.derived",
        )
    assert DataCategory


@pytest.mark.unit
def test_fides_key_matches_stated_parent_key():
    DataCategory(
        organization_fides_key=1,
        fides_key="user.provided.identifiable.custom_test_data",
        name="Custom Test Data",
        description="Custom Test Data Category",
        parent_key="user.provided.identifiable",
    )
    assert DataCategory


@pytest.mark.unit
def test_no_parent_key_but_fides_key_contains_parent_key():
    with pytest.raises(FidesValidationError):
        DataCategory(
            organization_fides_key=1,
            fides_key="user.provided.identifiable.custom_test_data",
            name="Custom Test Data",
            description="Custom Test Data Category",
        )
    assert DataCategory


@pytest.mark.unit
def test_create_valid_data_category():
    DataCategory(
        organization_fides_key=1,
        fides_key="user.provided.identifiable.custom_test_data",
        name="Custom Test Data",
        description="Custom Test Data Category",
        parent_key="user.provided.identifiable",
    )
    assert DataCategory


@pytest.mark.unit
def test_circular_dependency_data_category():
    with pytest.raises(FidesValidationError):
        DataCategory(
            organization_fides_key=1,
            fides_key="user.provided.identifiable",
            name="User Provided Identifiable Data",
            description="Test Data Category",
            parent_key="user.provided.identifiable",
        )
    assert True


@pytest.mark.unit
def test_create_valid_data_use():
    DataUse(
        organization_fides_key=1,
        fides_key="provide.system",
        name="Provide the Product or Service",
        parent_key="provide",
        description="Test Data Use",
    )
    assert True


@pytest.mark.unit
def test_circular_dependency_data_use():
    with pytest.raises(FidesValidationError):
        DataUse(
            organization_fides_key=1,
            fides_key="provide.system",
            name="Provide the Product or Service",
            description="Test Data Use",
            parent_key="provide.system",
        )
    assert True


@pytest.mark.unit
def test_fides_model_valid():
    fides_key = FidesModel(fides_key="foo_bar", name="Foo Bar")
    assert fides_key


@pytest.mark.unit
def test_fides_model_fides_key_invalid():
    "Check for a bunch of different possible bad characters here."
    with pytest.raises(FidesValidationError):
        FidesModel(fides_key="foo-bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fides_key="foo/bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fides_key="foo=bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fides_key="foo^bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fides_key="_foo^bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fides_key="")


@pytest.mark.unit
def test_valid_privacy_rule():
    privacy_rule = PrivacyRule(matches="ANY", values=["foo_bar"])
    assert privacy_rule


@pytest.mark.unit
def test_invalid_fides_key_privacy_rule():
    with pytest.raises(FidesValidationError):
        PrivacyRule(matches="ANY", values=["foo-bar"])
    assert True


@pytest.mark.unit
def test_invalid_matches_privacy_rule():
    with pytest.raises(ValidationError):
        PrivacyRule(matches="AN", values=["foo_bar"])
    assert True


@pytest.mark.unit
def test_valid_policy_rule():
    assert PolicyRule(
        organization_fides_key=1,
        policyId=1,
        fides_key="test_policy",
        name="Test Policy",
        description="Test Policy",
        data_categories=PrivacyRule(matches="NONE", values=[]),
        data_uses=PrivacyRule(matches="NONE", values=["provide.system"]),
        data_subjects=PrivacyRule(matches="ANY", values=[]),
        data_qualifier="aggregated.anonymized.unlinked_pseudonymized.pseudonymized",
    )


@pytest.mark.unit
def test_valid_policy():
    Policy(
        organization_fides_key=1,
        fides_key="test_policy",
        name="Test Policy",
        version="1.3",
        description="Test Policy",
        rules=[],
    )
    assert True


@pytest.mark.unit
def test_create_valid_system():
    System(
        organization_fides_key=1,
        registryId=1,
        fides_key="test_system",
        system_type="SYSTEM",
        name="Test System",
        description="Test Policy",
        privacy_declarations=[
            PrivacyDeclaration(
                name="declaration-name",
                data_categories=[],
                data_use="provide.system",
                data_subjects=[],
                data_qualifier="aggregated_data",
                dataset_references=[],
            )
        ],
        system_dependencies=["another_system", "yet_another_system"],
    )
    assert True


@pytest.mark.unit
def test_circular_dependency_system():
    with pytest.raises(FidesValidationError):
        System(
            organization_fides_key=1,
            registryId=1,
            fides_key="test_system",
            system_type="SYSTEM",
            name="Test System",
            description="Test Policy",
            privacy_declarations=[
                PrivacyDeclaration(
                    name="declaration-name",
                    data_categories=[],
                    data_use="provide.system",
                    data_subjects=[],
                    data_qualifier="aggregated_data",
                    dataset_references=["test_system"],
                )
            ],
            system_dependencies=["test_system"],
        )
    assert True
