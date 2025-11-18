import json
from pprint import pprint
from typing import Any

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_center_config import PrivacyCenterConfig
from fides.api.task.conditional_dependencies.privacy_request.convenience_fields import (
    build_convenience_field_list,
)
from fides.api.task.conditional_dependencies.privacy_request.util import (
    get_available_privacy_request_fields_dict,
    get_available_privacy_request_fields_list,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionalDependencyFieldInfo,
)
from fides.api.util.saas_util import load_as_string


@pytest.fixture
def convenience_fields():
    return build_convenience_field_list()


@pytest.fixture
def fields_dict(db: Session):
    return get_available_privacy_request_fields_dict(db)


@pytest.fixture
def fields_list(db: Session):
    return get_available_privacy_request_fields_list(db)


class TestGetAvailablePrivacyRequestFields:
    """Test the field generator for available privacy request fields."""

    def test_expected_fields_are_included(
        self,
        fields_list: list[ConditionalDependencyFieldInfo],
    ):
        # Extract all fields from list
        field_paths = {field.field_path for field in fields_list}
        for field in fields_list:
            assert field.field_path.startswith("privacy_request.")

        assert any("privacy_request.policy." in path for path in field_paths)
        assert any("privacy_request.identity." in path for path in field_paths)

    def test_nested_dict_with_custom_fields(self, db: Session):
        """Test that the function returns a nested dictionary with custom fields."""
        # Load base config from resource file
        base_config = json.loads(
            load_as_string("tests/ops/resources/privacy_center_config.json")
        )

        # Add custom identity fields to the actions
        base_config["actions"][0]["identity_inputs"]["loyalty_id"] = {
            "label": "Loyalty ID"
        }
        base_config["actions"][1]["identity_inputs"]["account_number"] = {
            "label": "Account Number"
        }

        # Add custom fields to the actions
        base_config["actions"][0]["custom_privacy_request_fields"] = {
            "first_name": {"label": "First name"},
            "last_name": {"label": "Last name", "required": False},
            "preferred_format": {
                "label": "Preferred format",
                "field_type": "select",
                "options": ["JSON", "CSV", "HTML"],
            },
        }
        base_config["actions"][1]["custom_privacy_request_fields"] = {
            "data_categories": {
                "label": "Select data categories to erase",
                "field_type": "multiselect",
                "options": ["Profile Information", "Activity History"],
            },
            "confirmation_code": {
                "label": "Confirmation code",
            },
        }

        # Create the privacy center config
        PrivacyCenterConfig.create_or_update(db=db, data={"config": base_config})

        # Get available fields with DB session
        fields = get_available_privacy_request_fields_dict(db=db)

        # Verify custom_privacy_request_fields is NOT at top level
        assert "custom_privacy_request_fields" not in fields["privacy_request"]

        policy_fields = fields["privacy_request"]["policy"]
        # Verify custom_privacy_request_fields is nested under policy
        assert "custom_privacy_request_fields" in policy_fields
        custom_fields_dict = policy_fields["custom_privacy_request_fields"]

        # Verify that custom fields from both policies are present
        expected_custom_field_names = {
            "first_name",
            "last_name",
            "preferred_format",
            "data_categories",
            "confirmation_code",
        }
        custom_field_names = set(custom_fields_dict.keys())
        assert expected_custom_field_names.issubset(custom_field_names)

        # Verify custom identity fields are included
        identity_dict = fields["privacy_request"]["identity"]["custom_identity_fields"]
        assert "loyalty_id" in identity_dict
        assert "account_number" in identity_dict
