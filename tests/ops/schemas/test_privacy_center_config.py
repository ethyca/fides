import json

import pytest
from pydantic import ValidationError

from fides.api.schemas.privacy_center_config import (
    BaseCustomPrivacyRequestField,
    ConsentConfigPage,
    CustomPrivacyRequestField,
    IdentityInputs,
    LocationCustomPrivacyRequestField,
    PrivacyCenterConfig,
)
from fides.api.util.saas_util import load_as_string


class TestPrivacyCenterConfig:

    @pytest.fixture
    def privacy_center_config(self) -> PrivacyCenterConfig:
        return PrivacyCenterConfig(
            **json.loads(
                load_as_string("tests/ops/resources/privacy_center_config.json")
            )
        )

    def test_valid_custom_privacy_request_field(self):
        CustomPrivacyRequestField(label="Tenant ID", default_value="123", hidden=True)

    def test_valid_custom_privacy_request_field_with_query_param(self):
        CustomPrivacyRequestField(
            label="Tenant ID", query_param_key="site_id", hidden=True
        )

    def test_custom_privacy_request_field_with_missing_default_value(self):
        with pytest.raises(ValidationError) as exc:
            CustomPrivacyRequestField(label="Tenant ID", hidden=True)
        assert (
            "default_value or query_param_key are required when hidden is True"
            in str(exc.value)
        )

    def test_custom_privacy_request_fields_with_missing_values(self):
        with pytest.raises(ValidationError):
            CustomPrivacyRequestField()

    def test_identity_inputs(self):
        IdentityInputs(email="required")

    def test_identity_inputs_invalid_value(self):
        with pytest.raises(ValidationError):
            IdentityInputs(email="test@example.com")

    def test_custom_identity_inputs(self):
        IdentityInputs(loyalty_id={"label": "Loyalty ID"})

    def test_mixed_identity_inputs(self):
        IdentityInputs(email="required", loyalty_id={"label": "Loyalty ID"})

    def test_invalid_custom_identity_inputs(self):
        with pytest.raises(ValueError):
            IdentityInputs(loyalty_id="invalid")

    def test_location_select_custom_privacy_request_field(self):
        """Test basic LocationCustomPrivacyRequestField creation and properties"""
        location_field = LocationCustomPrivacyRequestField(
            label="User Location",
            required=True,
            ip_geolocation_hint=True,
            default_value="US",
        )
        assert location_field.label == "User Location"
        assert location_field.field_type == "location"
        assert location_field.required is True
        assert location_field.ip_geolocation_hint is True
        assert location_field.default_value == "US"

    def test_location_select_field_defaults(self):
        """Test LocationCustomPrivacyRequestField with default values"""
        location_field = LocationCustomPrivacyRequestField(label="Location")
        assert location_field.label == "Location"
        assert location_field.field_type == "location"
        assert location_field.required is True  # Default from parent
        assert location_field.ip_geolocation_hint is False  # Default
        assert location_field.default_value is None  # Default from parent
        assert location_field.hidden is False  # Default from parent

    def test_location_select_field_rejects_options(self):
        """Test that LocationCustomPrivacyRequestField rejects options"""
        with pytest.raises(ValueError) as exc:
            LocationCustomPrivacyRequestField(
                label="Location", options=["US", "CA", "UK"]
            )
        assert "LocationCustomPrivacyRequestField does not support options" in str(
            exc.value
        )

    def test_location_select_field_missing_label(self):
        """Test validation error when label is missing"""
        with pytest.raises(ValidationError):
            LocationCustomPrivacyRequestField()  # Missing required label field

    def test_location_select_field_with_all_properties(self):
        """Test LocationCustomPrivacyRequestField with all possible properties"""
        location_field = LocationCustomPrivacyRequestField(
            label="Your Current Location",
            required=False,
            default_value="Unknown",
            query_param_key="user_region",
            ip_geolocation_hint=True,
        )
        assert location_field.label == "Your Current Location"
        assert location_field.field_type == "location"
        assert location_field.required is False
        assert location_field.default_value == "Unknown"
        assert location_field.hidden is False  # Location fields cannot be hidden
        assert location_field.query_param_key == "user_region"
        assert location_field.ip_geolocation_hint is True

    def test_location_field_rejects_hidden(self):
        """Test that LocationCustomPrivacyRequestField rejects hidden=True"""
        with pytest.raises(ValidationError) as exc_info:
            LocationCustomPrivacyRequestField(
                label="Location",
                hidden=True,
            )
        assert "Custom location fields cannot be hidden" in str(exc_info.value)

    def test_privacy_center_config_with_location_custom_field(self):
        """Test that PrivacyCenterConfig correctly handles location fields in custom_privacy_request_fields"""
        config_data = json.loads(
            load_as_string("tests/ops/resources/privacy_center_config.json")
        )
        # Add location field to the first action's custom_privacy_request_fields
        config_data["actions"][0]["custom_privacy_request_fields"] = {
            "user_location": {
                "label": "Your Location",
                "field_type": "location",
                "required": True,
                "ip_geolocation_hint": True,
            }
        }

        config = PrivacyCenterConfig(**config_data)
        location_field = config.actions[0].custom_privacy_request_fields[
            "user_location"
        ]

        # Verify the field was parsed as LocationCustomPrivacyRequestField
        assert isinstance(location_field, LocationCustomPrivacyRequestField)
        assert location_field.field_type == "location"
        assert location_field.label == "Your Location"
        assert location_field.required is True
        assert location_field.ip_geolocation_hint is True

    def test_privacy_center_config_mixed_custom_fields_with_location(self):
        """Test PrivacyCenterConfig with a mix of regular and location custom fields"""
        config_data = json.loads(
            load_as_string("tests/ops/resources/privacy_center_config.json")
        )
        # Add mixed custom fields including location to the first action
        config_data["actions"][0]["custom_privacy_request_fields"] = {
            "preferred_format": {
                "label": "Preferred Format",
                "field_type": "select",
                "options": ["JSON", "CSV", "HTML"],
            },
            "user_location": {
                "label": "Your Location",
                "field_type": "location",
                "required": False,
                "ip_geolocation_hint": False,
            },
            "comments": {
                "label": "Additional Comments",
                "field_type": "text",
            },
        }

        config = PrivacyCenterConfig(**config_data)
        custom_fields = config.actions[0].custom_privacy_request_fields

        # Test regular custom field
        format_field = custom_fields["preferred_format"]
        assert isinstance(format_field, CustomPrivacyRequestField)
        assert format_field.field_type == "select"
        assert format_field.options == ["JSON", "CSV", "HTML"]

        # Test location custom field
        location_field = custom_fields["user_location"]
        assert isinstance(location_field, LocationCustomPrivacyRequestField)
        assert location_field.field_type == "location"
        assert location_field.required is False
        assert location_field.ip_geolocation_hint is False

        # Test text custom field (defaults to regular CustomPrivacyRequestField)
        comments_field = custom_fields["comments"]
        assert isinstance(comments_field, CustomPrivacyRequestField)
        assert comments_field.field_type == "text"

    def test_union_serialization_excludes_location_properties_from_non_location_fields(
        self,
    ):
        """Test that CustomPrivacyRequestFieldUnion serialization correctly excludes
        location-specific properties from non-location field types"""
        config_data = json.loads(
            load_as_string("tests/ops/resources/privacy_center_config.json")
        )
        # Add mixed custom fields to test serialization behavior
        config_data["actions"][0]["custom_privacy_request_fields"] = {
            "location": {
                "label": "Location",
                "field_type": "location",
                "ip_geolocation_hint": True,
                "required": True,
            },
            "first_name": {
                "label": "First Name",
                "field_type": "text",
                "required": True,
            },
            "preferred_format": {
                "label": "Preferred Format",
                "field_type": "select",
                "options": ["JSON", "CSV"],
                "required": False,
            },
            "topics": {
                "label": "Topics of Interest",
                "field_type": "multiselect",
                "options": ["Privacy", "Security", "Data"],
                "required": False,
            },
        }

        config = PrivacyCenterConfig(**config_data)

        # Serialize to dict to check the actual output
        serialized = config.model_dump(mode="json")
        fields = serialized["actions"][0]["custom_privacy_request_fields"]

        # Location field should have ip_geolocation_hint
        location_field = fields["location"]
        assert "ip_geolocation_hint" in location_field
        assert location_field["ip_geolocation_hint"] is True
        assert location_field["field_type"] == "location"

        # Non-location fields should NOT have ip_geolocation_hint or other location-specific properties
        text_field = fields["first_name"]
        assert (
            "ip_geolocation_hint" not in text_field
        ), f"Text field should not have ip_geolocation_hint: {text_field}"
        assert text_field["field_type"] == "text"
        assert "options" in text_field  # Text fields can have options (though null)

        select_field = fields["preferred_format"]
        assert (
            "ip_geolocation_hint" not in select_field
        ), f"Select field should not have ip_geolocation_hint: {select_field}"
        assert select_field["field_type"] == "select"
        assert select_field["options"] == ["JSON", "CSV"]

        multiselect_field = fields["topics"]
        assert (
            "ip_geolocation_hint" not in multiselect_field
        ), f"Multiselect field should not have ip_geolocation_hint: {multiselect_field}"
        assert multiselect_field["field_type"] == "multiselect"
        assert multiselect_field["options"] == ["Privacy", "Security", "Data"]

        # Verify that all non-location fields have the correct base properties but not location-specific ones
        for field_name, field_data in fields.items():
            if field_name != "location":
                # All fields should have base properties
                assert "label" in field_data
                assert "required" in field_data
                assert "field_type" in field_data

                # Non-location fields should never have location-specific properties
                assert (
                    "ip_geolocation_hint" not in field_data
                ), f"Non-location field '{field_name}' should not have ip_geolocation_hint"

    def test_privacy_center_config_location_field_validation_in_config(self):
        """Test that location field validation works within PrivacyCenterConfig"""
        config_data = json.loads(
            load_as_string("tests/ops/resources/privacy_center_config.json")
        )

        # Test that location field rejects options when defined in config
        config_data["actions"][0]["custom_privacy_request_fields"] = {
            "invalid_location": {
                "label": "Invalid Location",
                "field_type": "location",
                "options": ["US", "CA", "UK"],  # This should be rejected
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            PrivacyCenterConfig(**config_data)
        assert "LocationCustomPrivacyRequestField does not support options" in str(
            exc_info.value
        )

    def test_invalid_executable_consent(
        self, privacy_center_config: PrivacyCenterConfig
    ):
        consent_page = privacy_center_config.consent.page
        for consent_option in consent_page.consent_options:
            consent_option.executable = True

        with pytest.raises(ValueError) as exc:
            ConsentConfigPage(**consent_page.model_dump(by_alias=True))
        assert "Cannot have more than one consent option be executable." in str(
            exc.value
        )

    def test_serialize_by_alias(self, privacy_center_config: PrivacyCenterConfig):
        assert (
            "includeConsent" in privacy_center_config.model_dump(by_alias=True).keys()
        )
        assert (
            "consentOptions"
            in privacy_center_config.consent.page.model_dump(by_alias=True).keys()
        )
        for field in ["cookieKeys", "fidesDataUseKey"]:
            assert (
                field
                in privacy_center_config.consent.page.consent_options[0]
                .model_dump(by_alias=True)
                .keys()
            )
        for field in ["confirmButtonText", "cancelButtonText", "modalTitle"]:
            assert (
                field
                in privacy_center_config.consent.button.model_dump(by_alias=True).keys()
            )
        assert (
            "globalPrivacyControl"
            in privacy_center_config.consent.page.consent_options[0]
            .default.model_dump(by_alias=True)
            .keys()
        )
