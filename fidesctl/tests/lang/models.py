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
def test_create_valid_data_category():
    DataCategory(
        organizationId=1,
        fides_key="customer_content_test_data",
        name="customer_content_data",
        clause="testDataClause",
        description="Test Data Category",
    )
    assert DataCategory


@pytest.mark.unit
def test_circular_dependency_data_category():
    with pytest.raises(FidesValidationError):
        DataCategory(
            organizationId=1,
            fides_key="customer_content_test_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
            parentKey="customer_content_test_data",
        )
    assert True


@pytest.mark.unit
def test_create_valid_data_category():
    DataUse(
        organizationId=1,
        fides_key="customer_content_test_data",
        name="customer_content_data",
        clause="testDataClause",
        description="Test Data Use",
    )
    assert True


@pytest.mark.unit
def test_circular_dependency_data_category():
    with pytest.raises(FidesValidationError):
        DataUse(
            organizationId=1,
            fides_key="customer_content_test_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
            parentKey="customer_content_test_data",
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
        fides_key="test_policy",
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
            fides_key="test_policy",
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
        organizationId=1,
        registryId=1,
        fides_key="test_system",
        systemType="SYSTEM",
        name="Test System",
        description="Test Policy",
        privacyDeclarations=[
            PrivacyDeclaration(
                name="declaration-name",
                dataCategories=[],
                dataUse="provide",
                dataSubjects=[],
                dataQualifier="aggregated_data",
                datasetReferences=[],
            )
        ],
        systemDependencies=["another_system", "yet_another_system"],
    )
    assert True


@pytest.mark.unit
def test_circular_dependency_system():
    with pytest.raises(FidesValidationError):
        System(
            organizationId=1,
            registryId=1,
            fides_key="test_system",
            systemType="SYSTEM",
            name="Test System",
            description="Test Policy",
            privacyDeclarations=[
                PrivacyDeclaration(
                    name="declaration-name",
                    dataCategories=[],
                    dataUse="provide",
                    dataSubjects=[],
                    dataQualifier="aggregated_data",
                    datasetReferences=["test_system"],
                )
            ],
            systemDependencies=["test_system"],
        )
    assert True
