import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.ops.common_exceptions import PrivacyNoticeHistoryNotFound
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.models.privacy_preference import (
    PrivacyPreferenceHistory,
    RequestOrigin,
    UserConsentPreference,
)
from fides.api.ops.models.privacy_request import ProvidedIdentity, ProvidedIdentityType


class TestPrivacyPreferenceHistory:
    def test_create_privacy_preference_min_fields(self, db, privacy_notice):
        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_in",
                "privacy_notice_history_id": privacy_notice.histories[0].id,
            },
            check_name=False,
        )

        assert pref.preference == UserConsentPreference.opt_in
        assert pref.privacy_notice_history == privacy_notice.histories[0]

        pref.delete(db=db)

    def test_create_privacy_preference_no_privacy_notice_history(self, db):
        with pytest.raises(PrivacyNoticeHistoryNotFound):
            PrivacyPreferenceHistory.create(
                db=db,
                data={
                    "preference": "opt_in",
                    "privacy_notice_history_id": "nonexistent_notice",
                },
                check_name=False,
            )

    def test_create_privacy_notice(self, db, privacy_notice, system, privacy_request):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        privacy_notice_history = privacy_notice.histories[0]

        preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": provided_identity.encrypted_value["value"]
                if provided_identity.field_name == ProvidedIdentityType.email
                else None,
                "phone_number": provided_identity.encrypted_value["value"]
                if provided_identity.field_name == ProvidedIdentityType.phone_number
                else None,
                "preference": "opt_out",
                "privacy_notice_history_id": privacy_notice_history.id,
                "provided_identity_id": provided_identity.id,
                "request_origin": "privacy_center",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "us_ca",
                "url_recorded": "example.com/privacy_center",
            },
            check_name=False,
        )
        assert preference_history_record.affected_system_status == {}
        assert preference_history_record.email == "test@email.com"
        assert preference_history_record.phone_number is None
        assert preference_history_record.preference == UserConsentPreference.opt_out
        assert (
            preference_history_record.privacy_notice_history == privacy_notice_history
        )
        assert (
            preference_history_record.privacy_request is None
        )  # Hasn't been added yet
        assert preference_history_record.provided_identity == provided_identity
        assert preference_history_record.relevant_systems == [system.fides_key]
        assert preference_history_record.request_origin == RequestOrigin.privacy_center
        assert preference_history_record.secondary_user_ids == {"ga_client_id": "test"}
        assert (
            preference_history_record.user_agent
            == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
        )
        assert preference_history_record.user_geography == PrivacyNoticeRegion.us_ca
        assert preference_history_record.url_recorded == "example.com/privacy_center"

        # Assert PrivacyRequest.privacy_preferences relationship
        preference_history_record.privacy_request_id = privacy_request.id
        preference_history_record.save(db)
        assert preference_history_record.privacy_request == privacy_request
        assert privacy_request.privacy_preferences == [preference_history_record]

        # Assert CurrentPrivacyPreference record upserted
        current_privacy_preference = (
            preference_history_record.current_privacy_preference
        )
        current_privacy_preference_id = current_privacy_preference.id
        assert current_privacy_preference.preference == UserConsentPreference.opt_out
        assert (
            current_privacy_preference.privacy_notice_history == privacy_notice_history
        )

        # Save preferences again with an "opt in" preference for this privacy notice
        next_preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": provided_identity.encrypted_value["value"]
                if provided_identity.field_name == ProvidedIdentityType.email
                else None,
                "phone_number": provided_identity.encrypted_value["value"]
                if provided_identity.field_name == ProvidedIdentityType.phone_number
                else None,
                "preference": "opt_in",
                "privacy_notice_history_id": privacy_notice_history.id,
                "provided_identity_id": provided_identity.id,
                "request_origin": "privacy_center",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "us_ca",
                "url_recorded": "example.com/privacy_center",
            },
            check_name=False,
        )

        assert next_preference_history_record.preference == UserConsentPreference.opt_in
        assert (
            next_preference_history_record.privacy_notice_history
            == privacy_notice_history
        )

        # Assert CurrentPrivacyPreference record upserted
        db.refresh(current_privacy_preference)
        assert current_privacy_preference.preference == UserConsentPreference.opt_in
        assert (
            current_privacy_preference.privacy_notice_history == privacy_notice_history
        )
        assert (
            next_preference_history_record.current_privacy_preference
            == current_privacy_preference
        )
        assert current_privacy_preference.id == current_privacy_preference_id

        db.refresh(preference_history_record)
        assert (
            next_preference_history_record.current_privacy_preference
            == current_privacy_preference
        )
        assert preference_history_record.current_privacy_preference is None

        preference_history_record.delete(db)
        next_preference_history_record.delete(db)
