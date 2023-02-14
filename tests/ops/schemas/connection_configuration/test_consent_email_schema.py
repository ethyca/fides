import pytest

from fides.api.ops.schemas.connection_configuration import (
    ConsentEmailSchema,
    SovrnEmailSchema,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    AdvancedSettings,
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedConsentEmailSchema,
    ExtendedIdentityTypes,
    IdentityTypes,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_sovrn import (
    SOVRN_REQUIRED_IDENTITY,
)


class TestGenericConsentEmailSchema:
    def test_base_consent_email_schema(self):
        assert ConsentEmailSchema(
            third_party_vendor_name="Dawn's Bakery",
            recipient_email_address="test@example.com",
            advanced_settings=AdvancedSettings(
                identity_types=IdentityTypes(email=True, phone_number=False)
            ),
        )

    def test_no_identities_supplied(self):
        with pytest.raises(ValueError) as exc:
            ConsentEmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                recipient_email_address="test@example.com",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=False, phone_number=False)
                ),
            )
        assert exc.value.errors()[0]["msg"] == "Must supply at least one identity_type"

    def test_missing_advanced_settings(self):
        with pytest.raises(ValueError) as exc:
            ConsentEmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                recipient_email_address="test@example.com",
            )
        assert exc.value.errors()[0]["msg"] == "field required"
        assert exc.value.errors()[0]["loc"][0] == "advanced_settings"

    def test_missing_third_party_vendor_name(self):
        with pytest.raises(ValueError) as exc:
            ConsentEmailSchema(
                recipient_email_address="test@example.com",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=True, phone_number=False)
                ),
            )
        assert exc.value.errors()[0]["msg"] == "field required"
        assert exc.value.errors()[0]["loc"][0] == "third_party_vendor_name"

    def test_missing_recipient(self):
        with pytest.raises(ValueError) as exc:
            ConsentEmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=True, phone_number=False)
                ),
            )
        assert exc.value.errors()[0]["msg"] == "field required"
        assert exc.value.errors()[0]["loc"][0] == "recipient_email_address"

    def test_extra_field(self):
        with pytest.raises(ValueError) as exc:
            ConsentEmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                recipient_email_address="test@example.com",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=True, phone_number=False)
                ),
                extra_field="extra_value",
            )
        assert exc.value.errors()[0]["msg"] == "extra fields not permitted"


class TestExtnededConsentEmailSchema:
    def test_extended_consent_email_schema(self):
        schema = ExtendedConsentEmailSchema(
            third_party_vendor_name="Test Vendor Name",
            test_email_address="my_email@example.com",
            recipient_email_address="vendor@example.com",
            advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
                identity_types=ExtendedIdentityTypes(
                    email=False, phone_number=False, cookie_ids=["new_cookie_id"]
                )
            ),
        )
        assert schema.third_party_vendor_name == "Test Vendor Name"
        assert schema.test_email_address == "my_email@example.com"
        assert schema.recipient_email_address == "vendor@example.com"
        assert schema.advanced_settings.identity_types.cookie_ids == ["new_cookie_id"]

    def test_extended_consent_email_schema_no_identities(self):
        with pytest.raises(ValueError):
            ExtendedConsentEmailSchema(
                third_party_vendor_name="Test Vendor Name",
                test_email_address="my_email@example.com",
                recipient_email_address="vendor@example.com",
                advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
                    identity_types=ExtendedIdentityTypes(
                        email=False, phone_number=False, cookie_ids=[]
                    )
                ),
            )


class TestSovrnEmailSchema:
    def test_base_sovrn_consent_email_schema(self):
        schema = SovrnEmailSchema(
            recipient_email_address="sovrn@example.com",
            advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
                identity_types=ExtendedIdentityTypes(
                    email=False, phone_number=False, cookie_ids=[]
                )
            ),
        )
        assert schema.third_party_vendor_name == "Sovrn"
        assert schema.test_email_address is None
        assert schema.recipient_email_address == "sovrn@example.com"
        assert schema.advanced_settings.identity_types.cookie_ids == [
            SOVRN_REQUIRED_IDENTITY
        ]  # Automatically added
