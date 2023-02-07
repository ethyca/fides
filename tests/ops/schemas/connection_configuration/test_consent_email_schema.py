import pytest

from fides.api.ops.schemas.connection_configuration import (
    ConsentEmailSchema,
    SovrnEmailSchema,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    AdvancedSettings,
    CookieIds,
)


class TestGenericConsentEmailSchema:
    def test_base_consent_email_schema(self):
        assert ConsentEmailSchema(
            third_party_vendor_name="Dawn's Bakery",
            recipient_email_address="test@example.com",
            advanced_settings=AdvancedSettings(
                identity_types=["email"], browser_identity_types=[]
            ),
        )

    def test_no_identities_supplied(self):
        with pytest.raises(ValueError) as exc:
            ConsentEmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                recipient_email_address="test@example.com",
                advanced_settings=AdvancedSettings(
                    identity_types=[], browser_identity_types=[]
                ),
            )
        assert (
            exc.value.errors()[0]["msg"]
            == "Must supply at least one identity_type or one browser_identity_type"
        )

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
                    identity_types=["email"], browser_identity_types=[]
                ),
            )
        assert exc.value.errors()[0]["msg"] == "field required"
        assert exc.value.errors()[0]["loc"][0] == "third_party_vendor_name"

    def test_missing_recipient(self):
        with pytest.raises(ValueError) as exc:
            ConsentEmailSchema(
                third_party_vendor_name="Dawn's Bakery",
                advanced_settings=AdvancedSettings(
                    identity_types=["email"], browser_identity_types=[]
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
                    identity_types=["email"], browser_identity_types=[]
                ),
                extra_field="extra_value",
            )
        assert exc.value.errors()[0]["msg"] == "extra fields not permitted"


class TestSovrnEmailSchema:
    def test_base_sovrn_consent_email_schema(self):
        schema = SovrnEmailSchema(
            recipient_email_address="sovrn@example.com",
            advanced_settings=AdvancedSettings(
                identity_types=["email"], browser_identity_types=[]
            ),
        )
        assert schema.third_party_vendor_name == "Sovrn"
        assert schema.advanced_settings.identity_types == []
        assert schema.test_email_address is None
        assert schema.recipient_email_address == "sovrn@example.com"
        assert schema.advanced_settings.browser_identity_types == [
            CookieIds.ljt_readerID
        ]  # Automatically added
