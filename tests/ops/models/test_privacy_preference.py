import pytest
from sqlalchemy.exc import InvalidRequestError

from fides.api.api.v1.endpoints.privacy_preference_endpoints import (
    anonymize_ip_address,
    extract_identity_from_provided_identity,
)
from fides.api.common_exceptions import (
    IdentityNotFoundException,
    PrivacyNoticeHistoryNotFound,
    PrivacyPreferenceSaveError,
)
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    LastServedNotice,
    PreferenceType,
    PrivacyPreferenceHistory,
    RequestOrigin,
    ServedNoticeHistory,
    ServingComponent,
    UserConsentPreference,
)
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    ProvidedIdentity,
    ProvidedIdentityType,
)


class TestPrivacyPreferenceHistory:
    def test_create_privacy_preference_min_fields(self, db, privacy_notice):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": ProvidedIdentity.hash_value("test@email.com"),
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        pref = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_in",
                "privacy_notice_history_id": privacy_notice.histories[0].id,
                "provided_identity_id": provided_identity.id,
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

    def test_create_privacy_preference_history_without_identity(
        self, db, privacy_notice
    ):
        with pytest.raises(IdentityNotFoundException):
            PrivacyPreferenceHistory.create(
                db=db,
                data={
                    "preference": "opt_in",
                    "privacy_notice_history_id": privacy_notice.histories[0].id,
                },
                check_name=False,
            )

    def test_create_privacy_preference_for_notice(
        self, db, privacy_notice, system, privacy_request
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": ProvidedIdentity.hash_value("test@email.com"),
            "encrypted_value": {"value": "test@email.com"},
        }
        fides_user_provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "fides_user_device_id",
            "hashed_value": ProvidedIdentity.hash_value(
                "test_fides_user_device_id_1234567"
            ),
            "encrypted_value": {"value": "test_fides_user_device_id_1234567"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        fides_user_provided_identity = ProvidedIdentity.create(
            db, data=fides_user_provided_identity_data
        )

        privacy_notice_history = privacy_notice.histories[0]

        email, hashed_email = extract_identity_from_provided_identity(
            provided_identity, ProvidedIdentityType.email
        )
        phone_number, hashed_phone_number = extract_identity_from_provided_identity(
            provided_identity, ProvidedIdentityType.phone_number
        )
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": email,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": hashed_email,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": hashed_phone_number,
                "phone_number": phone_number,
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
        assert (
            preference_history_record.hashed_email
            == provided_identity.hashed_value
            is not None
        )
        assert (
            preference_history_record.fides_user_device
            == fides_user_device_id
            is not None
        )
        assert (
            preference_history_record.hashed_fides_user_device
            == hashed_device_id
            is not None
        )
        assert (
            preference_history_record.fides_user_device_provided_identity
            == fides_user_provided_identity
        )

        assert preference_history_record.email == "test@email.com"
        assert (
            preference_history_record.hashed_email
            == provided_identity.hashed_value
            is not None
        )

        assert preference_history_record.phone_number is None
        assert preference_history_record.hashed_phone_number is None
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
        assert preference_history_record.user_geography == "us_ca"
        assert preference_history_record.url_recorded == "example.com/privacy_center"

        # Assert PrivacyRequest.privacy_preferences relationship
        assert privacy_request.privacy_preferences == []

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

    def test_create_privacy_preference_for_multiple_preference_types(
        self, db, system, fides_user_provided_identity
    ):
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        with pytest.raises(PrivacyPreferenceSaveError):
            PrivacyPreferenceHistory.create(
                db=db,
                data={
                    "purpose": 8,
                    "vendor": "amplitude",
                    "fides_user_device": fides_user_device_id,
                    "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                    "hashed_fides_user_device": hashed_device_id,
                    "preference": "opt_out",
                    "request_origin": "tcf_overlay",
                },
                check_name=False,
            )

    def test_create_privacy_preference_for_purpose(
        self, db, system, fides_user_provided_identity
    ):
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "purpose": 4,
                "email": None,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": None,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": None,
                "phone_number": None,
                "preference": "opt_out",
                "privacy_notice_history_id": None,
                "provided_identity_id": None,
                "request_origin": "tcf_overlay",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "fr",
                "url_recorded": "example.com",
            },
            check_name=False,
        )
        assert preference_history_record.affected_system_status == {}
        assert preference_history_record.email is None
        assert preference_history_record.hashed_email is None
        assert (
            preference_history_record.fides_user_device
            == fides_user_device_id
            is not None
        )
        assert (
            preference_history_record.hashed_fides_user_device
            == hashed_device_id
            is not None
        )
        assert (
            preference_history_record.fides_user_device_provided_identity
            == fides_user_provided_identity
        )
        assert preference_history_record.purpose == 4
        assert preference_history_record.tcf_version == "2.2"

        assert preference_history_record.phone_number is None
        assert preference_history_record.hashed_phone_number is None
        assert preference_history_record.preference == UserConsentPreference.opt_out
        assert preference_history_record.privacy_notice_history is None
        assert preference_history_record.privacy_request is None
        assert preference_history_record.provided_identity is None
        assert preference_history_record.relevant_systems is None
        assert preference_history_record.request_origin == RequestOrigin.tcf_overlay
        assert preference_history_record.secondary_user_ids == {"ga_client_id": "test"}
        assert (
            preference_history_record.user_agent
            == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
        )
        assert preference_history_record.user_geography == "fr"
        assert preference_history_record.url_recorded == "example.com"

        # Assert CurrentPrivacyPreference record upserted
        current_privacy_preference = (
            preference_history_record.current_privacy_preference
        )
        current_privacy_preference_id = current_privacy_preference.id
        assert current_privacy_preference.preference == UserConsentPreference.opt_out
        assert current_privacy_preference.privacy_notice_history is None
        assert current_privacy_preference.purpose == 4
        assert current_privacy_preference.tcf_version == "2.2"

        # Save preferences again with an "opt in" preference for this purpose
        next_preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_in",
                "purpose": 4,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "request_origin": "tcf_overlay",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "fr",
            },
            check_name=False,
        )

        assert next_preference_history_record.preference == UserConsentPreference.opt_in
        assert next_preference_history_record.privacy_notice_history is None
        assert next_preference_history_record.purpose == 4

        # Assert CurrentPrivacyPreference record upserted
        db.refresh(current_privacy_preference)
        assert current_privacy_preference.preference == UserConsentPreference.opt_in
        assert current_privacy_preference.privacy_notice_history is None
        assert current_privacy_preference.purpose == 4
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

        # Save preferences again with an "opt in" preference for a special purpose

        special_purpose_preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_in",
                "special_purpose": 1,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "request_origin": "tcf_overlay",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "fr",
            },
            check_name=False,
        )

        assert special_purpose_preference_history_record.special_purpose == 1
        assert special_purpose_preference_history_record.purpose is None
        assert special_purpose_preference_history_record.feature is None
        assert special_purpose_preference_history_record.special_feature is None
        assert (
            special_purpose_preference_history_record.privacy_notice_history_id is None
        )
        current_special_purpose_preference = (
            special_purpose_preference_history_record.current_privacy_preference
        )

        assert current_special_purpose_preference.special_purpose == 1
        assert current_special_purpose_preference.purpose is None
        assert current_special_purpose_preference.feature is None
        assert current_special_purpose_preference.special_feature is None
        assert current_special_purpose_preference.privacy_notice_history_id is None

        current_special_purpose_preference.delete(db)
        special_purpose_preference_history_record.delete(db)

    def test_create_privacy_preference_for_vendor(
        self, db, system, fides_user_provided_identity
    ):
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "vendor": "sendgrid",
                "email": None,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": None,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": None,
                "phone_number": None,
                "preference": "opt_out",
                "privacy_notice_history_id": None,
                "provided_identity_id": None,
                "request_origin": "tcf_overlay",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "fr",
                "url_recorded": "example.com",
            },
            check_name=False,
        )
        assert preference_history_record.affected_system_status == {}
        assert preference_history_record.email is None
        assert preference_history_record.hashed_email is None
        assert (
            preference_history_record.fides_user_device
            == fides_user_device_id
            is not None
        )
        assert (
            preference_history_record.hashed_fides_user_device
            == hashed_device_id
            is not None
        )
        assert (
            preference_history_record.fides_user_device_provided_identity
            == fides_user_provided_identity
        )
        assert preference_history_record.vendor == "sendgrid"
        assert preference_history_record.tcf_version == "2.2"

        assert preference_history_record.phone_number is None
        assert preference_history_record.hashed_phone_number is None
        assert preference_history_record.preference == UserConsentPreference.opt_out
        assert preference_history_record.privacy_notice_history is None
        assert preference_history_record.privacy_request is None
        assert preference_history_record.provided_identity is None
        assert preference_history_record.relevant_systems is None
        assert preference_history_record.request_origin == RequestOrigin.tcf_overlay
        assert preference_history_record.secondary_user_ids == {"ga_client_id": "test"}
        assert (
            preference_history_record.user_agent
            == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
        )
        assert preference_history_record.user_geography == "fr"
        assert preference_history_record.url_recorded == "example.com"

        # Assert CurrentPrivacyPreference record upserted
        current_privacy_preference = (
            preference_history_record.current_privacy_preference
        )
        current_privacy_preference_id = current_privacy_preference.id
        assert current_privacy_preference.preference == UserConsentPreference.opt_out
        assert current_privacy_preference.privacy_notice_history is None
        assert current_privacy_preference.vendor == "sendgrid"
        assert current_privacy_preference.tcf_version == "2.2"

        # Save preferences again with an "opt in" preference for this privacy notice
        next_preference_history_record = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "preference": "opt_in",
                "vendor": "sendgrid",
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "request_origin": "tcf_overlay",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "fr",
            },
            check_name=False,
        )

        assert next_preference_history_record.preference == UserConsentPreference.opt_in
        assert next_preference_history_record.privacy_notice_history is None
        assert next_preference_history_record.vendor == "sendgrid"

        # Assert CurrentPrivacyPreference record upserted
        db.refresh(current_privacy_preference)
        assert current_privacy_preference.preference == UserConsentPreference.opt_in
        assert current_privacy_preference.privacy_notice_history is None
        assert current_privacy_preference.vendor == "sendgrid"
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

    def test_create_history_and_upsert_current_preferences(
        self,
        db,
        privacy_notice,
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": ProvidedIdentity.hash_value("test@email.com"),
            "encrypted_value": {"value": "test@email.com"},
        }
        fides_user_provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "fides_user_device_id",
            "hashed_value": ProvidedIdentity.hash_value(
                "test_fides_user_device_id_1234567"
            ),
            "encrypted_value": {"value": "test_fides_user_device_id_1234567"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        fides_user_provided_identity = ProvidedIdentity.create(
            db, data=fides_user_provided_identity_data
        )

        privacy_notice_history = privacy_notice.histories[0]

        email, hashed_email = extract_identity_from_provided_identity(
            provided_identity, ProvidedIdentityType.email
        )
        phone_number, hashed_phone_number = extract_identity_from_provided_identity(
            provided_identity, ProvidedIdentityType.phone_number
        )
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        (
            preference_history_record,
            current_record,
        ) = PrivacyPreferenceHistory.create_history_and_upsert_current_preference(
            db=db,
            data={
                "email": email,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": hashed_email,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": hashed_phone_number,
                "phone_number": phone_number,
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

        assert current_record == preference_history_record.current_privacy_preference

    def test_cache_system_status(self, privacy_preference_history, db):
        assert privacy_preference_history.affected_system_status == {}

        privacy_preference_history.cache_system_status(
            db, "test_system_key", ExecutionLogStatus.pending
        )
        assert privacy_preference_history.affected_system_status == {
            "test_system_key": ExecutionLogStatus.pending.value
        }

        privacy_preference_history.cache_system_status(
            db, "test_system_key", ExecutionLogStatus.complete
        )
        assert privacy_preference_history.affected_system_status == {
            "test_system_key": ExecutionLogStatus.complete.value
        }

    def test_update_secondary_user_ids(self, privacy_preference_history, db):
        assert privacy_preference_history.secondary_user_ids is None

        privacy_preference_history.update_secondary_user_ids(
            db, {"email": "test@example.com"}
        )
        assert privacy_preference_history.secondary_user_ids == {
            "email": "test@example.com"
        }

        privacy_preference_history.update_secondary_user_ids(
            db, {"ljt_readerID": "customer-123"}
        )
        assert privacy_preference_history.secondary_user_ids == {
            "email": "test@example.com",
            "ljt_readerID": "customer-123",
        }

        privacy_preference_history.update_secondary_user_ids(
            db, {"email": "hello@example.com"}
        )
        assert privacy_preference_history.secondary_user_ids == {
            "email": "hello@example.com",
            "ljt_readerID": "customer-123",
        }

    def test_consolidate_current_privacy_preferences(self, db, privacy_notice):
        """We might have privacy preferences saved just under a fides user device id in an overlay,
        and then later, have privacy preferences saved both under an email and that same fides user device id

        We should consider these preferences as being for the same individual, and consolidate
        them for our "current privacy preferences"
        """

        # Let's first just save a privacy preference under a fides user device id
        fides_user_provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "fides_user_device_id",
            "hashed_value": ProvidedIdentity.hash_value(
                "test_fides_user_device_id_1234567"
            ),
            "encrypted_value": {"value": "test_fides_user_device_id_1234567"},
        }
        fides_user_provided_identity = ProvidedIdentity.create(
            db, data=fides_user_provided_identity_data
        )

        privacy_notice_history = privacy_notice.histories[0]
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        preference_history_record_for_device = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": None,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": None,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": None,
                "phone_number": None,
                "preference": "opt_out",
                "privacy_notice_history_id": privacy_notice_history.id,
                "provided_identity_id": None,
                "request_origin": "privacy_center",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "us_ca",
                "url_recorded": "example.com/privacy_center",
            },
            check_name=False,
        )

        # Assert a CurrentPrivacyPreference record was created when the PrivacyPreferenceHistory was created
        fides_user_device_current_preference = (
            preference_history_record_for_device.current_privacy_preference
        )
        assert fides_user_device_current_preference.created_at is not None
        assert fides_user_device_current_preference.updated_at is not None
        assert (
            fides_user_device_current_preference.preference
            == UserConsentPreference.opt_out
        )
        assert fides_user_device_current_preference.provided_identity_id is None
        assert (
            fides_user_device_current_preference.fides_user_device_provided_identity_id
            == fides_user_provided_identity.id
        )
        assert (
            fides_user_device_current_preference.privacy_notice_id == privacy_notice.id
        )
        assert (
            fides_user_device_current_preference.privacy_notice_history_id
            == privacy_notice_history.id
        )
        assert (
            fides_user_device_current_preference.privacy_preference_history_id
            == preference_history_record_for_device.id
        )

        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": ProvidedIdentity.hash_value("test@email.com"),
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        email, hashed_email = extract_identity_from_provided_identity(
            provided_identity, ProvidedIdentityType.email
        )

        preference_history_record_for_email = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": email,
                "fides_user_device": None,
                "fides_user_device_provided_identity_id": None,
                "hashed_email": hashed_email,
                "hashed_fides_user_device": None,
                "hashed_phone_number": None,
                "phone_number": None,
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

        # Assert a new CurrentPrivacyPreference record was created when the PrivacyPreferenceHistory was created with email
        email_current_preference = (
            preference_history_record_for_email.current_privacy_preference
        )
        assert email_current_preference.created_at is not None
        assert email_current_preference.updated_at is not None
        assert email_current_preference.preference == UserConsentPreference.opt_in
        assert email_current_preference.provided_identity_id == provided_identity.id
        assert email_current_preference.fides_user_device_provided_identity_id is None
        assert email_current_preference.privacy_notice_id == privacy_notice.id
        assert (
            email_current_preference.privacy_notice_history_id
            == privacy_notice_history.id
        )
        assert (
            email_current_preference.privacy_preference_history_id
            == preference_history_record_for_email.id
        )

        # Now user saves a preference from the privacy center with verified email that also has their device id
        preference_history_saved_with_both_email_and_device_id = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": email,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": hashed_email,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": None,
                "phone_number": None,
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

        # Assert existing CurrentPrivacyPreference record was updated when the PrivacyPreferenceHistory was created
        # and consolidated preferences for the email and the user device. The preferences for device only was deleted
        current_preference = (
            preference_history_saved_with_both_email_and_device_id.current_privacy_preference
        )
        assert current_preference.created_at is not None
        assert current_preference.updated_at is not None
        assert current_preference.preference == UserConsentPreference.opt_in
        assert current_preference.provided_identity_id == provided_identity.id
        assert (
            current_preference.fides_user_device_provided_identity_id
            == fides_user_provided_identity.id
        )
        assert current_preference.privacy_notice_id == privacy_notice.id
        assert current_preference.privacy_notice_history_id == privacy_notice_history.id
        assert (
            current_preference.privacy_preference_history_id
            == preference_history_saved_with_both_email_and_device_id.id
        )

        assert (
            current_preference
            == email_current_preference
            != fides_user_device_current_preference
        )
        with pytest.raises(InvalidRequestError):
            # Can't refresh because this preference has been deleted, and consolidated with the other
            db.refresh(fides_user_device_current_preference)

    def test_update_current_privacy_preferences_fides_id_only(
        self, db, privacy_notice, fides_user_provided_identity
    ):
        """Assert that if we save privacy preferences for a fides user device id and current preferences
        already exists, the current preference is updated correctly."
        """

        privacy_notice_history = privacy_notice.histories[0]
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        preference_history_record_for_device = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": None,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": None,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": None,
                "phone_number": None,
                "preference": "opt_out",
                "privacy_notice_history_id": privacy_notice_history.id,
                "provided_identity_id": None,
                "request_origin": "privacy_center",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "us_ca",
                "url_recorded": "example.com/privacy_center",
            },
            check_name=False,
        )

        # Assert a CurrentPrivacyPreference record was created when the PrivacyPreferenceHistory was created
        fides_user_device_current_preference = (
            preference_history_record_for_device.current_privacy_preference
        )
        assert (
            fides_user_device_current_preference.preference
            == UserConsentPreference.opt_out
        )
        created_at = fides_user_device_current_preference.created_at
        updated_at = fides_user_device_current_preference.updated_at

        # Save a preference but change the preference from opt out to opt in
        new_preference_history_record_for_device = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "email": None,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": None,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": None,
                "phone_number": None,
                "preference": "opt_in",
                "privacy_notice_history_id": privacy_notice_history.id,
                "provided_identity_id": None,
                "request_origin": "privacy_center",
                "secondary_user_ids": {"ga_client_id": "test"},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "us_ca",
                "url_recorded": "example.com/privacy_center",
            },
            check_name=False,
        )

        # Assert a new CurrentPrivacyPreference record was created when the PrivacyPreferenceHistory was created with email
        db.refresh(fides_user_device_current_preference)
        assert (
            fides_user_device_current_preference.preference
            == UserConsentPreference.opt_in
        )
        assert fides_user_device_current_preference.created_at == created_at
        assert fides_user_device_current_preference.updated_at > updated_at

        new_preference_history_record_for_device.delete(db)
        preference_history_record_for_device.delete(db)


class TestCurrentPrivacyPreference:
    def test_get_preference_by_notice_and_fides_user_device(
        self,
        db,
        empty_provided_identity,
        privacy_preference_history_us_ca_provide_for_fides_user,
        privacy_notice,
        privacy_notice_us_ca_provide,
        fides_user_provided_identity,
    ):
        pref = CurrentPrivacyPreference.get_preference_by_type_and_fides_user_device(
            db=db,
            fides_user_provided_identity=fides_user_provided_identity,
            preference_type=PreferenceType.privacy_notice_id,
            preference_value=privacy_notice_us_ca_provide.id,
        )
        assert (
            pref
            == privacy_preference_history_us_ca_provide_for_fides_user.current_privacy_preference
        )

        assert (
            CurrentPrivacyPreference.get_preference_by_type_and_fides_user_device(
                db=db,
                fides_user_provided_identity=empty_provided_identity,
                preference_type=PreferenceType.privacy_notice_id,
                preference_value=privacy_notice.id,
            )
            is None
        )

        assert (
            CurrentPrivacyPreference.get_preference_by_type_and_fides_user_device(
                db=db,
                fides_user_provided_identity=fides_user_provided_identity,
                preference_type=PreferenceType.privacy_notice_id,
                preference_value=privacy_notice.id,
            )
            is None
        )

    def test_get_preference_by_purpose_and_fides_user_device(
        self,
        db,
        empty_provided_identity,
        privacy_preference_history_for_tcf_purpose,
        fides_user_provided_identity,
    ):
        pref = CurrentPrivacyPreference.get_preference_by_type_and_fides_user_device(
            db=db,
            fides_user_provided_identity=fides_user_provided_identity,
            preference_type=PreferenceType.purpose,
            preference_value=8,
        )
        assert (
            pref
            == privacy_preference_history_for_tcf_purpose.current_privacy_preference
        )

        assert (
            CurrentPrivacyPreference.get_preference_by_type_and_fides_user_device(
                db=db,
                fides_user_provided_identity=empty_provided_identity,
                preference_type=PreferenceType.purpose,
                preference_value=8,
            )
            is None
        )

        assert (
            CurrentPrivacyPreference.get_preference_by_type_and_fides_user_device(
                db=db,
                fides_user_provided_identity=fides_user_provided_identity,
                preference_type=PreferenceType.purpose,
                preference_value=500,
            )
            is None
        )


class TestAnonymizeIpAddress:
    def test_anonymize_ip_address_empty_string(self):
        assert anonymize_ip_address("") is None

    def test_anonymize_ip_address_none(self):
        assert anonymize_ip_address(None) is None

    def test_anonymize_bad_ip_address(self):
        assert anonymize_ip_address("bad_address") is None

    def test_anonymize_ip_address_list(self):
        assert anonymize_ip_address("[]") is None

    def test_anonymize_ipv4(self):
        assert anonymize_ip_address("12.214.31.144") == "12.214.31.0"

    def test_anonymize_ipv6(self):
        assert (
            anonymize_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
            == "2001:0db8:85a3:0000:0000:0000:0000:0000"
        )


class TestServedNoticeHistory:
    def test_created_record_of_notice_served_and_upsert_last_served_notice(
        self,
        db,
        privacy_notice,
        privacy_experience_privacy_center,
        experience_config_privacy_center,
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": ProvidedIdentity.hash_value("ethyca@email.com"),
            "encrypted_value": {"value": "ethyca@email.com"},
        }
        fides_user_provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "fides_user_device_id",
            "hashed_value": ProvidedIdentity.hash_value(
                "test_fides_user_device_id_abcdefg"
            ),
            "encrypted_value": {"value": "test_fides_user_device_id_abcdefg"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        fides_user_provided_identity = ProvidedIdentity.create(
            db, data=fides_user_provided_identity_data
        )

        privacy_notice_history = privacy_notice.histories[0]

        email, hashed_email = extract_identity_from_provided_identity(
            provided_identity, ProvidedIdentityType.email
        )
        phone_number, hashed_phone_number = extract_identity_from_provided_identity(
            provided_identity, ProvidedIdentityType.phone_number
        )
        (
            fides_user_device_id,
            hashed_device_id,
        ) = extract_identity_from_provided_identity(
            fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
        )

        served_notice_history_record = ServedNoticeHistory.create(
            db=db,
            data={
                "anonymized_ip_address": "12.214.31.0",
                "email": email,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id,
                "hashed_email": hashed_email,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": hashed_phone_number,
                "phone_number": phone_number,
                "privacy_notice_history_id": privacy_notice_history.id,
                "provided_identity_id": provided_identity.id,
                "request_origin": "privacy_center",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
                "user_geography": "us_co",
                "url_recorded": "example.com/privacy_center",
                "acknowledge_mode": False,
                "serving_component": ServingComponent.privacy_center,
                "privacy_experience_id": privacy_experience_privacy_center.id,
                "privacy_experience_config_history_id": experience_config_privacy_center.histories[
                    0
                ].id,
            },
            check_name=False,
        )
        assert served_notice_history_record.email == "ethyca@email.com"
        assert (
            served_notice_history_record.hashed_email
            == provided_identity.hashed_value
            is not None
        )
        assert (
            served_notice_history_record.fides_user_device
            == fides_user_device_id
            is not None
        )
        assert (
            served_notice_history_record.hashed_fides_user_device
            == hashed_device_id
            is not None
        )
        assert (
            served_notice_history_record.fides_user_device_provided_identity
            == fides_user_provided_identity
        )

        assert served_notice_history_record.phone_number is None
        assert served_notice_history_record.hashed_phone_number is None
        assert (
            served_notice_history_record.privacy_notice_history
            == privacy_notice_history
        )
        assert served_notice_history_record.provided_identity == provided_identity
        assert (
            served_notice_history_record.request_origin == RequestOrigin.privacy_center
        )
        assert (
            served_notice_history_record.user_agent
            == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
        )
        assert served_notice_history_record.user_geography == "us_co"
        assert served_notice_history_record.url_recorded == "example.com/privacy_center"

        # Assert ServedNoticeHistory record upserted
        last_served_notice = served_notice_history_record.last_served_record
        assert last_served_notice.privacy_notice_history == privacy_notice_history
        assert last_served_notice.privacy_notice_id == privacy_notice.id
        assert last_served_notice.provided_identity_id == provided_identity.id
        assert (
            last_served_notice.fides_user_device_provided_identity_id
            == fides_user_provided_identity.id
        )
        assert (
            last_served_notice.served_notice_history_id
            == served_notice_history_record.id
        )

        served_notice_history_record.delete(db)
        last_served_notice.delete(db)


class TestLastServedNotice:
    def test_served_latest_version(
        self,
        db,
        served_notice_history_us_ca_provide_for_fides_user,
        privacy_notice_us_ca_provide,
    ):
        last_served = (
            served_notice_history_us_ca_provide_for_fides_user.last_served_record
        )
        assert last_served.record_matches_latest_version is True

        privacy_notice_us_ca_provide.update(db, data={"description": "new_description"})
        assert privacy_notice_us_ca_provide.version == 2.0
        assert privacy_notice_us_ca_provide.description == "new_description"

        assert last_served.record_matches_latest_version is False

    def test_get_last_served_for_notice_and_fides_user_device(
        self,
        db,
        fides_user_provided_identity,
        served_notice_history_us_ca_provide_for_fides_user,
        privacy_notice_us_ca_provide,
        empty_provided_identity,
        privacy_notice,
    ):
        retrieved_record = (
            LastServedNotice.get_last_served_for_preference_type_and_fides_user_device(
                db,
                fides_user_provided_identity=fides_user_provided_identity,
                tcf_preference_type=PreferenceType.privacy_notice_id,
                preference_value=privacy_notice_us_ca_provide.id,
            )
        )
        assert (
            retrieved_record
            == served_notice_history_us_ca_provide_for_fides_user.last_served_record
        )

        assert (
            LastServedNotice.get_last_served_for_preference_type_and_fides_user_device(
                db,
                fides_user_provided_identity=empty_provided_identity,
                tcf_preference_type=PreferenceType.privacy_notice_id,
                preference_value=privacy_notice_us_ca_provide.id,
            )
            is None
        )
        assert (
            LastServedNotice.get_last_served_for_preference_type_and_fides_user_device(
                db,
                fides_user_provided_identity=fides_user_provided_identity,
                tcf_preference_type=PreferenceType.privacy_notice_id,
                preference_value=privacy_notice.id,
            )
            is None
        )

    def test_get_last_served_for_purpose_and_fides_user_device(
        self,
        db,
        fides_user_provided_identity,
        empty_provided_identity,
        served_notice_history_for_tcf_purpose,
    ):
        retrieved_record = (
            LastServedNotice.get_last_served_for_preference_type_and_fides_user_device(
                db,
                fides_user_provided_identity=fides_user_provided_identity,
                tcf_preference_type=PreferenceType.purpose,
                preference_value=8,
            )
        )
        assert (
            retrieved_record == served_notice_history_for_tcf_purpose.last_served_record
        )

        assert (
            LastServedNotice.get_last_served_for_preference_type_and_fides_user_device(
                db,
                fides_user_provided_identity=empty_provided_identity,
                tcf_preference_type=PreferenceType.purpose,
                preference_value=8,
            )
            is None
        )
        assert (
            LastServedNotice.get_last_served_for_preference_type_and_fides_user_device(
                db,
                fides_user_provided_identity=fides_user_provided_identity,
                tcf_preference_type=PreferenceType.purpose,
                preference_value=200,
            )
            is None
        )
