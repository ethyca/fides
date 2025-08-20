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

    def test_valid_location_collection_required(self):
        """Test that location collection with 'required' setting is valid."""
        location_config = LocationCollectionConfig(
            collection="required", ip_geolocation_hint=True
        )
        assert location_config.collection == "required"
        assert location_config.ip_geolocation_hint is True

    def test_valid_location_collection_optional(self):
        """Test that location collection with 'optional' setting is valid."""
        location_config = LocationCollectionConfig(
            collection="optional", ip_geolocation_hint=False
        )
        assert location_config.collection == "optional"
        assert location_config.ip_geolocation_hint is False

    def test_location_collection_default_values(self):
        """Test that ip_geolocation_hint defaults to False."""
        location_config = LocationCollectionConfig(collection="required")
        assert location_config.collection == "required"
        assert location_config.ip_geolocation_hint is False

    def test_invalid_location_collection_value(self):
        """Test that invalid collection values are rejected."""
        with pytest.raises(ValidationError) as exc:
            LocationCollectionConfig(collection="invalid_value")
        assert "Input should be 'optional' or 'required'" in str(exc.value)

    def test_privacy_center_config_with_location(self):
        """Test that PrivacyCenterConfig accepts location configuration."""
        config_data = json.loads(
            load_as_string("tests/ops/resources/privacy_center_config.json")
        )
        # Add location configuration
        config_data["location"] = {
            "collection": "required",
            "ip_geolocation_hint": True,
        }

        config = PrivacyCenterConfig(**config_data)
        assert config.location is not None
        assert config.location.collection == "required"
        assert config.location.ip_geolocation_hint is True

    def test_privacy_center_config_without_location(self):
        """Test that PrivacyCenterConfig works without location configuration."""
        config_data = json.loads(
            load_as_string("tests/ops/resources/privacy_center_config.json")
        )

        config = PrivacyCenterConfig(**config_data)
        assert config.location is None
