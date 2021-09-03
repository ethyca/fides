import pytest

from fideslang.models.data_category import DataCategory
from fideslang.models.validation import FidesValidationError


@pytest.mark.unit
def test_create_valid_data_category():
    DataCategory(
        organizationId=1,
        fidesKey="customer_content_test_data",
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
            fidesKey="customer_content_test_data",
            name="customer_content_data",
            clause="testDataClause",
            description="Test Data Category",
            parentKey="customer_content_test_data",
        )
    assert True
