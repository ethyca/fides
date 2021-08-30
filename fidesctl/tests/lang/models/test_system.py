import pytest

from fideslang.models.system import System, PrivacyDeclaration
from fideslang.models.validation import FidesValidationError


@pytest.mark.unit
def test_create_valid_system():
    System(
        organizationId=1,
        registryId=1,
        fidesKey="test_system",
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
            fidesKey="test_system",
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
