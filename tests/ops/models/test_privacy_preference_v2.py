from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.privacy_preference_v2 import (
    ConsentIdentitiesMixin,
    PrivacyPreferenceHistoryV2,
    ServedNoticeHistoryV2,
)


class TestPrivacyPreferenceV2:
    def test_privacy_notice_preference(
        self,
        db,
        privacy_experience_privacy_center,
        privacy_notice_us_ca_provide,
        served_notice_history,
    ):
        preference_history_record = PrivacyPreferenceHistoryV2.create(
            db=db,
            data={
                "anonymized_ip_address": "92.158.1.0",
                "email": "test@email.com",
                "method": "button",
                "privacy_experience_config_history_id": privacy_experience_privacy_center.experience_config.experience_config_history_id,
                "privacy_experience_id": privacy_experience_privacy_center.id,
                "preference": "opt_in",
                "privacy_notice_history_id": privacy_notice_us_ca_provide.histories[
                    0
                ].id,
                "request_origin": "privacy_center",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "us_ca",
                "url_recorded": "https://example.com/privacy_center",
                "served_notice_history_id": served_notice_history.served_notice_history_id,
            },
            check_name=False,
        )

        assert preference_history_record.preference == UserConsentPreference.opt_in
        assert (
            preference_history_record.privacy_notice_history_id
            == privacy_notice_us_ca_provide.histories[0].id
        )
        assert (
            preference_history_record.privacy_notice_history
            == privacy_notice_us_ca_provide.histories[0]
        )

        preference_history_record.delete(db)

    def test_tcf_preference(
        self,
        db,
        privacy_experience_france_overlay,
    ):
        preference_history_record = PrivacyPreferenceHistoryV2.create(
            db=db,
            data={
                "anonymized_ip_address": "92.158.1.0",
                "email": "test@email.com",
                "fides_user_device": "051b219f-20e4-45df-82f7-5eb68a00889f",
                "method": "accept",
                "privacy_experience_config_history_id": None,
                "privacy_experience_id": privacy_experience_france_overlay.id,
                "preference": "tcf",
                "request_origin": "tcf_overlay",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "fr_idg",
                "url_recorded": "example.com/",
                "served_notice_history_id": "served_notice_history_test_id",
                "tcf_preferences": {
                    "purpose_consent_preferences": [{"id": 1, "preference": "opt_out"}],
                    "purpose_legitimate_interests_preferences": [
                        {"id": 1, "preference": "opt_in"},
                        {"id": 2, "preference": "opt_in"},
                    ],
                    "vendor_consent_preferences": [
                        {"id": "gvl.8", "preference": "opt_out"}
                    ],
                    "vendor_legitimate_interests_preferences": [],
                    "special_feature_preferences": [],
                    "special_purpose_preferences": [],
                    "feature_preferences": [],
                    "system_legitimate_interests_preferences": [],
                },
            },
        )
        assert preference_history_record.preference == UserConsentPreference.tcf
        assert preference_history_record.privacy_notice_history_id is None
        assert preference_history_record.tcf_preferences == {
            "purpose_consent_preferences": [{"id": 1, "preference": "opt_out"}],
            "purpose_legitimate_interests_preferences": [
                {"id": 1, "preference": "opt_in"},
                {"id": 2, "preference": "opt_in"},
            ],
            "vendor_consent_preferences": [{"id": "gvl.8", "preference": "opt_out"}],
            "vendor_legitimate_interests_preferences": [],
            "special_feature_preferences": [],
            "special_purpose_preferences": [],
            "feature_preferences": [],
            "system_legitimate_interests_preferences": [],
        }

        preference_history_record.delete(db)


class TestConsentIdentitiesHashMixin:
    def test_hash_value_null(self):
        assert ConsentIdentitiesMixin.hash_value("") is None

    def test_hash_value_not_null(self):
        assert ConsentIdentitiesMixin.hash_value("customer_one@example.com") is not None

    class TestServedNoticeHistoryV2:
        def test_get_by_served_id(self, served_notice_history, db):
            """Assert looked up by served id field, not id"""
            assert ServedNoticeHistoryV2.get_by_served_id(db, "ser_12345").all() == [
                served_notice_history
            ]

            assert (
                ServedNoticeHistoryV2.get_by_served_id(
                    db, served_notice_history.id
                ).all()
                == []
            )
