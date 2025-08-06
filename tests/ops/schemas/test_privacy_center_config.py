import json

import pytest
from pydantic import ValidationError

from fides.api.schemas.privacy_center_config import (
    ConsentConfigPage,
    CustomPrivacyRequestField,
    IdentityInputs,
    LocationIdentityField,
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

    def test_location_identity_field(self):
        location_field = LocationIdentityField(
            label="Location", required=True, ip_geolocation_hint=True
        )
        assert location_field.label == "Location"
        assert location_field.required is True
        assert location_field.ip_geolocation_hint is True
        assert location_field.default_value is None

    def test_location_identity_field_with_all_options(self):
        location_field = LocationIdentityField(
            label="Your Location",
            required=False,
            default_value="US",
            query_param_key="region",
            ip_geolocation_hint=False,
        )
        assert location_field.label == "Your Location"
        assert location_field.required is False
        assert location_field.default_value == "US"
        assert location_field.query_param_key == "region"
        assert location_field.ip_geolocation_hint is False

    def test_identity_inputs_with_location_object(self):
        identity_inputs = IdentityInputs(
            email="required",
            location={
                "label": "Location",
                "required": True,
                "ip_geolocation_hint": True,
            },
        )
        assert identity_inputs.email == "required"
        assert isinstance(identity_inputs.location, LocationIdentityField)
        assert identity_inputs.location.label == "Location"
        assert identity_inputs.location.required is True
        assert identity_inputs.location.ip_geolocation_hint is True

    def test_identity_inputs_with_location_string(self):
        identity_inputs = IdentityInputs(email="required", location="required")
        assert identity_inputs.email == "required"
        assert identity_inputs.location == "required"

    def test_mixed_identity_inputs_with_location(self):
        identity_inputs = IdentityInputs(
            email="required",
            location={"label": "Location", "ip_geolocation_hint": True},
            loyalty_id={"label": "Loyalty ID"},
        )
        assert identity_inputs.email == "required"
        assert isinstance(identity_inputs.location, LocationIdentityField)
        assert identity_inputs.location.ip_geolocation_hint is True

    def test_location_identity_field_validation_error(self):
        with pytest.raises(ValidationError):
            LocationIdentityField()  # Missing required label field

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
