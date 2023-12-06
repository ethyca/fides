import uuid
from enum import Enum
from unittest import mock

import pytest
from fastapi import Request
from starlette.datastructures import Headers

from fides.api.api.v1.endpoints.served_notice_endpoints_v2 import (
    save_consent_served_task,
    save_last_served_and_prep_task_data,
)
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.privacy_preference import RequestOrigin
from fides.api.models.privacy_preference_v2 import (
    ConsentIdentitiesMixin,
    LastServedNoticeV2,
    PrivacyPreferenceHistoryV2,
    ServedNoticeHistoryV2,
    get_records_with_consent_identifiers,
)
from fides.api.schemas.privacy_preference import RecordConsentServedRequest
from fides.api.schemas.redis_cache import Identity


class TestPrivacyNoticeHistoryRelationship:
    def test_privacy_notice_history_relationship(self, db, privacy_notice):
        privacy_preference_history = PrivacyPreferenceHistoryV2.create(
            db,
            data={
                "privacy_notice_history_id": privacy_notice.histories[0].id,
                "preference": UserConsentPreference.opt_in,
            },
        )

        assert (
            privacy_preference_history.privacy_notice_history
            == privacy_notice.histories[0]
        )


mock_request = Request(
    {
        "type": "http",
        "method": "PATCH",
        "url": "/api/v1/notices-served",
        "headers": Headers(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
                "Referer": "http://www.example.com",
                "x-forwarded-for": "24.199.143.193,49.177.39.145",
            }
        ).raw,
    }
)


class TestSaveLastServedAndPrepConsentData:
    @pytest.fixture(scope="function")
    def mock_task_data_privacy_notices(
        self, privacy_notice, privacy_experience_overlay
    ):
        return {
            "acknowledge_mode": True,
            "anonymized_ip_address": "24.199.143.0",
            "email": "customer-1_9b873a2c-6eb5-4aaf-a00c-0f4a6288580d@example.com",
            "fides_user_device": "f4865476-36c3-4e9a-a60c-c39189ca9f36",
            "hashed_email": "24326224313224554572696d4e746c7345367167596632427249314475626864686f4a39765a36476561744250776861554b33506363563956765865",
            "hashed_fides_user_device": "24326224313224554572696d4e746c734536716759663242724931447551754c386f4c53434c76572e4a336f314f444a787249684778463767476e71",
            "hashed_phone_number": None,
            "phone_number": None,
            "privacy_experience_id": privacy_experience_overlay.id,
            "served": {
                "privacy_notice_history_ids": [privacy_notice.histories[0].id],
                "tcf_purpose_consents": [],
                "tcf_purpose_legitimate_interests": [],
                "tcf_special_purposes": [],
                "tcf_vendor_consents": [],
                "tcf_vendor_legitimate_interests": [],
                "tcf_features": [],
                "tcf_special_features": [],
                "tcf_system_consents": [],
                "tcf_system_legitimate_interests": [],
            },
            "served_notice_history_id": "ser_b6fb3151-807b-4c33-ac30-6b8b52ae5a96",
            "serving_component": "overlay",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "user_geography": "us_ca",
            "url_recorded": "http://www.example.com",
        }

    @pytest.fixture(scope="function")
    def mock_task_data_tcf_notices(self, privacy_experience_france_tcf_overlay, system):
        return {
            "acknowledge_mode": True,
            "anonymized_ip_address": "24.199.143.0",
            "email": "customer-1_9b873a2c-6eb5-4aaf-a00c-0f4a6288580d@example.com",
            "fides_user_device": "f4865476-36c3-4e9a-a60c-c39189ca9f36",
            "hashed_email": "24326224313224554572696d4e746c7345367167596632427249314475626864686f4a39765a36476561744250776861554b33506363563956765865",
            "hashed_fides_user_device": "24326224313224554572696d4e746c734536716759663242724931447551754c386f4c53434c76572e4a336f314f444a787249684778463767476e71",
            "hashed_phone_number": None,
            "phone_number": None,
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
            "served": {
                "privacy_notice_history_ids": [],
                "tcf_purpose_consents": [1, 2],
                "tcf_purpose_legitimate_interests": [3, 4],
                "tcf_special_purposes": [1],
                "tcf_vendor_consents": ["gvl.9", "gacp.11"],
                "tcf_vendor_legitimate_interests": ["gvl.1"],
                "tcf_features": [1],
                "tcf_special_features": [2],
                "tcf_system_consents": [system.id],
                "tcf_system_legitimate_interests": [],
            },
            "served_notice_history_id": "ser_b6fb3151-807b-4c33-ac30-6b8b52ae5a96",
            "serving_component": "tcf_overlay",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "user_geography": "fr_idg",
            "url_recorded": "http://www.example.com",
        }

    @mock.patch(
        "fides.api.api.v1.endpoints.served_notice_endpoints_v2.LastServedNoticeV2.generate_served_notice_history_id"
    )
    def test_save_consent_served_for_privacy_notices(
        self,
        mock_served_notice_history_id,
        db,
        privacy_notice,
        privacy_notice_us_ca_provide,
        privacy_notice_us_co_third_party_sharing,
    ):
        """
        Save that privacy notices were saved for the same user multiple times,
        asserting that multiple user identities are combined under the same record
        when we realize they are the same person.

        Verify the task data that is generated and queued for a more detailed consent reporting save
        """
        fides_user_device_id = str(uuid.uuid4())
        email = f"customer-1_{uuid.uuid4()}@example.com"
        mock_served_notice_history_id.return_value = (
            "ser_b6fb3151-807b-4c33-ac30-6b8b52ae5a96"
        )

        # Save a record just against the fides user device id
        fides_device_record, _ = save_last_served_and_prep_task_data(
            db=db,
            request=mock_request,
            request_data=RecordConsentServedRequest(
                acknowledge_mode=True,
                browser_identity=Identity(),
                privacy_notice_history_ids=[privacy_notice.histories[0].id],
                serving_component="overlay",
                user_geography="us_ca",
            ),
            fides_user_device=fides_user_device_id,
        )
        fides_device_record_id = fides_device_record.id

        assert fides_device_record.fides_user_device == fides_user_device_id
        assert fides_device_record.served == {
            "privacy_notice_history_ids": [privacy_notice.histories[0].id],
            "tcf_purpose_consents": [],
            "tcf_purpose_legitimate_interests": [],
            "tcf_special_purposes": [],
            "tcf_features": [],
            "tcf_special_features": [],
            "tcf_vendor_consents": [],
            "tcf_vendor_legitimate_interests": [],
            "tcf_system_consents": [],
            "tcf_system_legitimate_interests": [],
        }

        # Save a separate record against just an email
        email_record, _ = save_last_served_and_prep_task_data(
            db=db,
            request=mock_request,
            request_data=RecordConsentServedRequest(
                browser_identity=Identity(),
                privacy_notice_history_ids=[
                    privacy_notice_us_ca_provide.histories[0].id
                ],
                serving_component="overlay",
            ),
            email=email,
        )

        email_record_id = email_record.id
        assert email_record.fides_user_device is None
        assert email_record.email == email
        assert email_record.served["privacy_notice_history_ids"] == [
            privacy_notice_us_ca_provide.histories[0].id
        ]
        assert email_record.id != fides_device_record.id

        # Save again with both identities and the records combine into one
        third_record, task_data = save_last_served_and_prep_task_data(
            db=db,
            request=mock_request,
            request_data=RecordConsentServedRequest(
                browser_identity=Identity(),
                privacy_notice_history_ids=[
                    privacy_notice_us_co_third_party_sharing.histories[0].id
                ],
                serving_component="overlay",
                user_geography="us_ca",
                acknowledge_mode=True,
            ),
            fides_user_device=fides_user_device_id,
            email=email,
        )

        assert third_record.fides_user_device == fides_user_device_id
        assert third_record.email == email
        assert set(third_record.served["privacy_notice_history_ids"]) == {
            privacy_notice.histories[0].id,
            privacy_notice_us_ca_provide.histories[0].id,
            privacy_notice_us_co_third_party_sharing.histories[0].id,
        }

        assert third_record.id in [email_record_id, fides_device_record_id]

        hashed_device_value = ConsentIdentitiesMixin.hash_value(fides_user_device_id)
        hashed_email_value = ConsentIdentitiesMixin.hash_value(email)
        assert (
            get_records_with_consent_identifiers(
                db,
                LastServedNoticeV2,
                hashed_device=hashed_device_value,
                hashed_email=hashed_email_value,
            ).count()
            == 1
        )

        # Assert task data only saved the privacy notice history id in the latest request,
        # even though the "latest served record" consolidate existing notice history ids
        assert task_data == {
            "acknowledge_mode": True,
            "anonymized_ip_address": "24.199.143.0",
            "email": email,
            "fides_user_device": fides_user_device_id,
            "hashed_email": hashed_email_value,
            "hashed_fides_user_device": hashed_device_value,
            "hashed_phone_number": None,
            "phone_number": None,
            "privacy_experience_id": None,
            "served": {
                "privacy_notice_history_ids": [
                    privacy_notice_us_co_third_party_sharing.histories[0].id
                ],
                "tcf_purpose_consents": [],
                "tcf_purpose_legitimate_interests": [],
                "tcf_special_purposes": [],
                "tcf_vendor_consents": [],
                "tcf_vendor_legitimate_interests": [],
                "tcf_features": [],
                "tcf_special_features": [],
                "tcf_system_consents": [],
                "tcf_system_legitimate_interests": [],
            },
            "served_notice_history_id": mock_served_notice_history_id.return_value,
            "serving_component": "overlay",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "user_geography": "us_ca",
            "url_recorded": "http://www.example.com",
        }

    @mock.patch(
        "fides.api.api.v1.endpoints.served_notice_endpoints_v2.LastServedNoticeV2.generate_served_notice_history_id"
    )
    def test_save_consent_served_for_tcf_notices(
        self,
        mock_served_notice_history_id,
        db,
        privacy_experience_france_tcf_overlay,
        system,
    ):
        """
        Save that privacy notices were saved for the same user multiple times,
        asserting that multiple user identities are combined under the same record
        when we realize they are the same person.

        Verify the task data that is generated and queued for a more detailed consent reporting save
        """
        fides_user_device_id = str(uuid.uuid4())
        mock_served_notice_history_id.return_value = (
            "ser_b6fb3151-807b-4c33-ac30-6b8b52ae5a96"
        )
        hashed_device_value = ConsentIdentitiesMixin.hash_value(fides_user_device_id)

        # Save a record against the fides user device id
        fides_device_record, _ = save_last_served_and_prep_task_data(
            db=db,
            request=mock_request,
            request_data=RecordConsentServedRequest(
                acknowledge_mode=True,
                browser_identity=Identity(),
                privacy_notice_history_ids=[],
                tcf_purpose_consents=[1, 3, 4],
                tcf_purpose_legitimate_interests=[2, 4, 7],
                tcf_special_purposes=[1, 2],
                tcf_vendor_consents=["gvl.42"],
                tcf_vendor_legitimate_interests=["gvl.8"],
                tcf_features=[1, 2],
                tcf_special_features=[1],
                tcf_system_consents=[system.id],
                tcf_system_legitimate_interests=[],
                serving_component="tcf_overlay",
                user_geography="fr_idg",
                privacy_experience_id=privacy_experience_france_tcf_overlay.id,
            ),
            fides_user_device=fides_user_device_id,
        )
        fides_device_record_id = fides_device_record.id

        assert fides_device_record.fides_user_device == fides_user_device_id
        assert fides_device_record.served == {
            "privacy_notice_history_ids": [],
            "tcf_purpose_consents": [1, 3, 4],
            "tcf_purpose_legitimate_interests": [2, 4, 7],
            "tcf_special_purposes": [1, 2],
            "tcf_features": [1, 2],
            "tcf_special_features": [1],
            "tcf_vendor_consents": ["gvl.42"],
            "tcf_vendor_legitimate_interests": ["gvl.8"],
            "tcf_system_consents": [system.id],
            "tcf_system_legitimate_interests": [],
        }

        # Save another record against the fides user device id - data is completely replaced,
        # unlike for standard privacy notices. Record is upserted on the fides user device id
        latest_saved_record, task_data = save_last_served_and_prep_task_data(
            db=db,
            request=mock_request,
            request_data=RecordConsentServedRequest(
                acknowledge_mode=True,
                browser_identity=Identity(),
                privacy_notice_history_ids=[],
                tcf_purpose_consents=[1],
                tcf_purpose_legitimate_interests=[2],
                tcf_special_purposes=[1],
                tcf_vendor_consents=[],
                tcf_vendor_legitimate_interests=["gvl.8"],
                tcf_features=[2],
                tcf_special_features=[1],
                tcf_system_consents=[system.id],
                tcf_system_legitimate_interests=[],
                serving_component="tcf_overlay",
                user_geography="fr_idg",
                privacy_experience_id=privacy_experience_france_tcf_overlay.id,
            ),
            fides_user_device=fides_user_device_id,
        )

        assert latest_saved_record.id == fides_device_record_id
        assert latest_saved_record.served == {
            "privacy_notice_history_ids": [],
            "tcf_purpose_consents": [1],
            "tcf_purpose_legitimate_interests": [2],
            "tcf_special_purposes": [1],
            "tcf_features": [2],
            "tcf_special_features": [1],
            "tcf_vendor_consents": [],
            "tcf_vendor_legitimate_interests": ["gvl.8"],
            "tcf_system_consents": [system.id],
            "tcf_system_legitimate_interests": [],
        }

        # Test that task data that will be queued to save TCF preferences passes along
        # the latest saved TCF data
        assert task_data == {
            "acknowledge_mode": True,
            "anonymized_ip_address": "24.199.143.0",
            "email": None,
            "fides_user_device": fides_user_device_id,
            "hashed_email": None,
            "hashed_fides_user_device": hashed_device_value,
            "hashed_phone_number": None,
            "phone_number": None,
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
            "served": {
                "privacy_notice_history_ids": [],
                "tcf_purpose_consents": [1],
                "tcf_purpose_legitimate_interests": [2],
                "tcf_special_purposes": [1],
                "tcf_vendor_consents": [],
                "tcf_vendor_legitimate_interests": ["gvl.8"],
                "tcf_features": [2],
                "tcf_special_features": [1],
                "tcf_system_consents": [system.id],
                "tcf_system_legitimate_interests": [],
            },
            "served_notice_history_id": mock_served_notice_history_id.return_value,
            "serving_component": "tcf_overlay",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "user_geography": "fr_idg",
            "url_recorded": "http://www.example.com",
        }

    def test_merge_consent_across_multiple_identities(self, db, privacy_notice):
        """
        Test that when we realize identities are linked, we merge all records,
        including their identities.

        We prioritize the non-null identifers most recently-saved first.
        """
        email = f"customer-1{uuid.uuid4()}@example.com"
        hashed_email = ConsentIdentitiesMixin.hash_value(email)
        phone = "1+5558675309"
        hashed_phone = ConsentIdentitiesMixin.hash_value(phone)
        fides_user_device = str(uuid.uuid4())
        hashed_device = ConsentIdentitiesMixin.hash_value(fides_user_device)

        combined_record, _ = save_last_served_and_prep_task_data(
            db=db,
            request=mock_request,
            request_data=RecordConsentServedRequest(
                acknowledge_mode=True,
                browser_identity=Identity(),
                privacy_notice_history_ids=[privacy_notice.histories[0].id],
                serving_component="overlay",
                user_geography="us_ca",
            ),
            phone_number=phone,
            email=email,
            fides_user_device=fides_user_device,
        )

        email_record, task_data = save_last_served_and_prep_task_data(
            db=db,
            request=mock_request,
            request_data=RecordConsentServedRequest(
                acknowledge_mode=True,
                browser_identity=Identity(),
                privacy_notice_history_ids=[privacy_notice.histories[0].id],
                serving_component="overlay",
                user_geography="us_ca",
            ),
            email=email,
        )

        assert email_record.email == email
        assert email_record.phone_number == phone
        assert email_record.fides_user_device == fides_user_device

        records = get_records_with_consent_identifiers(
            db,
            LastServedNoticeV2,
            hashed_device=hashed_device,
        )

        assert records.count() == 1
        assert records[0].id == combined_record.id

        records = get_records_with_consent_identifiers(
            db,
            LastServedNoticeV2,
            hashed_email=hashed_email,
        )

        assert records.count() == 1
        assert records[0].id == combined_record.id

        records = get_records_with_consent_identifiers(
            db,
            LastServedNoticeV2,
            hashed_phone=hashed_phone,
        )

        assert records.count() == 1
        assert records[0].id == combined_record.id

        # While our "last served" data was consolidated on identifiers,
        # our consent reporting only includes the original request data
        assert task_data["email"] == email
        assert not task_data["phone_number"]
        assert not task_data["fides_user_device"]

    def test_save_consent_served_task_for_privacy_notices(
        self,
        db,
        mock_task_data_privacy_notices,
        privacy_notice,
        experience_config_overlay,
    ):
        served_consent_data = save_consent_served_task(mock_task_data_privacy_notices)

        assert len(served_consent_data) == 1
        served_notice_history = served_consent_data[0]
        for key, val in mock_task_data_privacy_notices.items():
            saved_val = getattr(served_notice_history, key)
            if isinstance(saved_val, Enum):
                assert saved_val.value == val
            else:
                assert saved_val == val

        assert (
            served_notice_history.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )
        assert (
            served_notice_history.privacy_experience_config_history_id
            == experience_config_overlay.histories[0].id
        )
        assert served_notice_history.request_origin == RequestOrigin.overlay
        assert served_notice_history.tcf_served is None

        db.delete(served_notice_history)

    def test_save_consent_served_task_for_tcf_notices(
        self,
        db,
        mock_task_data_tcf_notices,
        privacy_experience_france_tcf_overlay,
        system,
        experience_config_tcf_overlay,
    ):
        served_consent_data = save_consent_served_task(mock_task_data_tcf_notices)

        assert len(served_consent_data) == 1
        served_notice_history = served_consent_data[0]
        for key, val in mock_task_data_tcf_notices.items():
            saved_val = getattr(served_notice_history, key)
            if isinstance(saved_val, Enum):
                assert saved_val.value == val
            else:
                assert saved_val == val

        assert served_notice_history.privacy_notice_history_id is None
        assert served_notice_history.notice_name == "TCF"
        assert served_notice_history.tcf_served == {
            "tcf_features": [1],
            "tcf_system_consents": [system.id],
            "tcf_vendor_consents": ["gvl.9", "gacp.11"],
            "tcf_purpose_consents": [1, 2],
            "tcf_special_features": [2],
            "tcf_special_purposes": [1],
            "tcf_system_legitimate_interests": [],
            "tcf_vendor_legitimate_interests": ["gvl.1"],
            "tcf_purpose_legitimate_interests": [3, 4],
        }
        assert (
            served_notice_history.privacy_experience_id
            == privacy_experience_france_tcf_overlay.id
        )
        assert (
            served_notice_history.privacy_experience_config_history_id
            == experience_config_tcf_overlay.histories[0].id
        )
        assert served_notice_history.request_origin == RequestOrigin.tcf_overlay
        assert (
            served_notice_history.served_notice_history_id
            == mock_task_data_tcf_notices["served_notice_history_id"]
        )
        assert served_notice_history.anonymized_ip_address == "24.199.143.0"

        db.query(ServedNoticeHistoryV2).delete()
