import pytest

from fides.api.schemas.connection_configuration import SovrnSchema
from fides.api.schemas.connection_configuration.connection_secrets_attentive import (
    AttentiveSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettings,
    AdvancedSettingsWithExtendedIdentityTypes,
    EmailSchema,
    ExtendedEmailSchema,
    ExtendedIdentityTypes,
    IdentityTypes,
)
from fides.api.service.connectors.email.sovrn_connector import SOVRN_REQUIRED_IDENTITY


class TestEmailSchema:
    def test_email_schema(self):
        assert EmailSchema(
            third_party_vendor_name="Dawn's Bakery",
            recipient_email_address="test@example.com",
            advanced_settings=AdvancedSettings(
                identity_types=IdentityTypes(email=True, phone_number=False)
            ),
        )

    def test_email_schema_default_identity_types(self):
        schema = EmailSchema(
            third_party_vendor_name="Dawn's Bakery",
            recipient_email_address="test@example.com",
        )
        assert schema.advanced_settings == AdvancedSettings(
            identity_types=IdentityTypes(email=True, phone_number=False)
        )

    def test_email_schema_invalid_email(self) -> None:
        with pytest.raises(ValueError) as exc:
            EmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                recipient_email_address="to_email",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=True, phone_number=False)
                ),
            )
        assert "value is not a valid email address" in exc.value.errors()[0]["msg"]

    def test_no_identities_supplied(self):
        with pytest.raises(ValueError) as exc:
            EmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                recipient_email_address="test@example.com",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=False, phone_number=False)
                ),
            )
        assert (
            exc.value.errors()[0]["msg"]
            == "Value error, Must supply at least one identity_type."
        )

    def test_missing_third_party_vendor_name(self):
        with pytest.raises(ValueError) as exc:
            EmailSchema(
                recipient_email_address="test@example.com",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=True, phone_number=False)
                ),
            )
        assert exc.value.errors()[0]["msg"] == "Field required"
        assert exc.value.errors()[0]["loc"][0] == "third_party_vendor_name"

    def test_missing_recipient(self):
        with pytest.raises(ValueError) as exc:
            EmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=True, phone_number=False)
                ),
            )
        assert exc.value.errors()[0]["msg"] == "Field required"
        assert exc.value.errors()[0]["loc"][0] == "recipient_email_address"

    def test_extra_field(self):
        with pytest.raises(ValueError) as exc:
            EmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                recipient_email_address="test@example.com",
                advanced_settings=AdvancedSettings(
                    identity_types=IdentityTypes(email=True, phone_number=False)
                ),
                extra_field="extra_value",
            )
        assert exc.value.errors()[0]["msg"] == "Extra inputs are not permitted"


class TestExtendedEmailSchema:
    def test_extended_email_schema(self):
        schema = ExtendedEmailSchema(
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

    def test_extended_email_schema_default_identity_types(self):
        schema = ExtendedEmailSchema(
            third_party_vendor_name="Test Vendor Name",
            test_email_address="my_email@example.com",
            recipient_email_address="vendor@example.com",
        )
        assert schema.advanced_settings.identity_types == ExtendedIdentityTypes(
            email=True, phone_number=False, cookie_ids=[]
        )

    def test_extended_consent_email_schema_no_identities(self):
        with pytest.raises(ValueError):
            ExtendedEmailSchema(
                third_party_vendor_name="Test Vendor Name",
                test_email_address="my_email@example.com",
                recipient_email_address="vendor@example.com",
                advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
                    identity_types=ExtendedIdentityTypes(
                        email=False, phone_number=False, cookie_ids=[]
                    )
                ),
            )


class TestSovrnSchema:
    def test_sovrn_email_schema(self):
        schema = SovrnSchema(
            recipient_email_address="sovrn@example.com",
        )
        assert schema.third_party_vendor_name == "Sovrn"
        assert schema.test_email_address is None
        assert schema.recipient_email_address == "sovrn@example.com"
        assert schema.advanced_settings == AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=False,
                phone_number=False,
                cookie_ids=[SOVRN_REQUIRED_IDENTITY],
            )
        )


class TestAttentiveSchema:
    def test_attentive_email_schema(self):
        schema = AttentiveSchema(recipient_email_address="attentive@example.com")
        assert schema.third_party_vendor_name == "Attentive Email"
        assert schema.test_email_address is None
        assert schema.recipient_email_address == "attentive@example.com"
        assert schema.advanced_settings == AdvancedSettings(
            identity_types=IdentityTypes(email=True, phone_number=False)
        )
