from fides.api.models.consent_settings import ConsentSettings


class TestConsentSettings:
    def test_get_or_create(self, db):
        consent_settings = ConsentSettings.get_or_create_with_defaults(db)
        if consent_settings:
            consent_settings.delete(db)

        consent_settings = ConsentSettings.get_or_create_with_defaults(db)
        assert consent_settings.tcf_enabled is False
        assert consent_settings.created_at is not None
        assert consent_settings.updated_at is not None
        settings_id = consent_settings.id

        consent_settings = ConsentSettings.get_or_create_with_defaults(db)
        assert consent_settings.id == settings_id
