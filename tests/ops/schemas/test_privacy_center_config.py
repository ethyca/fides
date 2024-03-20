import pytest
from pydantic import ValidationError

from fides.api.schemas.privacy_center_config import (
    CustomPrivacyRequestField,
    IdentityInputs,
)


class TestPrivacyCenterConfig:
    def test_valid_custom_privacy_request_field(self):
        CustomPrivacyRequestField(label="Tenant ID", default_value="123", hidden=True)

    def test_custom_privacy_request_field_with_missing_default_value(self):
        with pytest.raises(ValidationError) as exc:
            CustomPrivacyRequestField(label="Tenant ID", hidden=True)
        assert "default_value is required when hidden is True" in str(exc.value)

    def test_custom_privacy_request_fields_with_missing_values(self):
        with pytest.raises(ValidationError):
            CustomPrivacyRequestField()

    def test_identity_inputs(self):
        IdentityInputs(email="required")

    def test_identity_inputs_invalid_value(self):
        with pytest.raises(ValidationError):
            IdentityInputs(email="test@example.com")
