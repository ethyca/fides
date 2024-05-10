import json

import pytest
from pydantic import ValidationError

from fides.api.schemas.privacy_center_config import (
    ConsentConfigPage,
    CustomPrivacyRequestField,
    IdentityInputs,
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

    def test_custom_identity_inputs(self):
        IdentityInputs(loyalty_id={"label": "Loyalty ID"})

    def test_mixed_identity_inputs(self):
        IdentityInputs(email="required", loyalty_id={"label": "Loyalty ID"})

    def test_invalid_custom_identity_inputs(self):
        with pytest.raises(ValueError) as exc:
            IdentityInputs(loyalty_id="Loyalty ID")
        assert (
            'Custom identity "loyalty_id" must be an instance of CustomIdentity (e.g. {"label": "Field label"})'
            in str(exc.value)
        )

    def test_invalid_executable_consent(
        self, privacy_center_config: PrivacyCenterConfig
    ):
        consent_page = privacy_center_config.consent.page
        for consent_option in consent_page.consentOptions:
            consent_option.executable = True

        with pytest.raises(ValueError) as exc:
            ConsentConfigPage(**consent_page.dict())
        assert "Cannot have more than one consent option be executable." in str(
            exc.value
        )
