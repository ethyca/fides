import pytest

from fides.api.task.conditional_dependencies.privacy_request.convenience_fields import (
    build_convenience_field_list,
)
from fides.api.task.conditional_dependencies.privacy_request.util import (
    get_available_privacy_request_fields,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionalDependencyFieldInfo,
)


@pytest.fixture
def convenience_fields():
    return build_convenience_field_list()


@pytest.fixture
def fields():
    return get_available_privacy_request_fields()


class TestGetAvailablePrivacyRequestFields:
    """Test the field generator for available privacy request fields."""

    def test_returns_list_of_field_info(
        self, fields: list[ConditionalDependencyFieldInfo]
    ):
        """Test that the function returns a list of ConditionalDependencyFieldInfo objects."""
        assert isinstance(fields, list)
        assert len(fields) > 0
        assert all(
            isinstance(field, ConditionalDependencyFieldInfo) for field in fields
        )

    def test_convenience_fields_is_subset_of_available_fields(
        self,
        fields: list[ConditionalDependencyFieldInfo],
        convenience_fields: list[ConditionalDependencyFieldInfo],
    ):
        # verify that all convenience fields are included
        assert {field.field_path for field in convenience_fields}.issubset(
            {field.field_path for field in fields}
        )
        for field in fields:
            if field not in convenience_fields:
                assert field.is_convenience_field is False
            else:
                assert field.is_convenience_field is True

    def test_expected_fields_are_included(
        self,
        fields: list[ConditionalDependencyFieldInfo],
    ):
        field_paths = {field.field_path for field in fields}
        for field in fields:
            assert field.field_path.startswith("privacy_request.")

            assert field.field_type in [
                "string",
                "integer",
                "float",
                "boolean",
                "array",
                "object",
                "any",
            ]

        # Check for some basic fields
        assert "privacy_request.id" in field_paths
        assert "privacy_request.status" in field_paths
        assert "privacy_request.location" in field_paths
        assert "privacy_request.source" in field_paths

        # Check for policy fields
        assert any("privacy_request.policy." in path for path in field_paths)
        assert "privacy_request.policy.id" in field_paths
        assert "privacy_request.policy.key" in field_paths
        assert "privacy_request.policy.name" in field_paths

        # Check for identity fields
        assert any("privacy_request.identity" in path for path in field_paths)

        # Check for custom privacy request fields
        assert any(
            "privacy_request.custom_privacy_request_fields" in path
            for path in field_paths
        )
