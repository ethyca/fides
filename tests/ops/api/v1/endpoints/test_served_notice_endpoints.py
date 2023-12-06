from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.api.v1.endpoints.privacy_preference_endpoints import anonymize_ip_address
from fides.api.models.privacy_preference import RequestOrigin, ServingComponent
from fides.api.models.privacy_preference_v2 import (
    ConsentIdentitiesMixin,
    LastServedNoticeV2,
    ServedNoticeHistoryV2,
    get_consent_records_by_device_id,
    get_consent_records_by_email,
)
from fides.api.models.privacy_request import ConsentRequest, ProvidedIdentity
from fides.common.api.v1.urn_registry import (
    CONSENT_REQUEST_NOTICES_SERVED,
    NOTICES_SERVED,
    V1_URL_PREFIX,
)
from fides.config import CONFIG


class TestSaveNoticesServedForFidesDeviceId:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + NOTICES_SERVED

    @pytest.fixture(scope="function")
    def request_body(self, privacy_notice, privacy_experience_overlay):
        return {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "privacy_notice_history_ids": [privacy_notice.histories[0].id],
            "privacy_experience_id": privacy_experience_overlay.id,
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.banner.value,
        }

    @pytest.fixture(scope="function")
    def tcf_request_body(
        self, privacy_notice, privacy_experience_france_tcf_overlay, system
    ):
        return {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_purpose_consents": [5],
            "tcf_vendor_consents": ["gvl.42"],
            "tcf_special_features": [2],
            "tcf_system_legitimate_interests": [system.id],
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
            "user_geography": "fr",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }

    @pytest.mark.usefixtures(
        "privacy_notice",
    )
    def test_no_fides_user_device_id_supplied(self, api_client, url, request_body):
        """We need a fides user device id in the request body to save that consent was served"""
        del request_body["browser_identity"]["fides_user_device_id"]
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 422

    @pytest.mark.usefixtures(
        "privacy_notice",
    )
    def test_bad_fides_user_device_id_supplied(self, api_client, url, request_body):
        """Testing validation that fides user device id must be in expected uuid format"""
        request_body["browser_identity"][
            "fides_user_device_id"
        ] = "bad_fides_user_device_id"
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "badly formed hexadecimal UUID string"
        )

    def test_record_notices_served_with_bad_notice(self, api_client, url, request_body):
        """Every notice history in request body needs to be valid"""
        request_body["privacy_notice_history_ids"] = ["bad_history"]
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 400

    def test_record_notices_served_bad_experience_id(
        self,
        api_client,
        url,
        request_body,
    ):
        """Privacy experiences need to be valid when recording notices served"""
        request_body["privacy_experience_id"] = "bad_id"
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == f"Privacy Experience 'bad_id' not found."

    @mock.patch(
        "fides.api.api.v1.endpoints.served_notice_endpoints_v2.anonymize_ip_address"
    )
    def test_record_notices_served_with_respect_to_fides_user_device_id(
        self,
        mock_anonymize,
        db,
        api_client,
        url,
        request_body,
        privacy_notice,
        privacy_experience_overlay,
    ):
        """Test recording that a notice was served to the given user with this fides user device id

        We create a ServedNoticeHistory record for every single time a notice is served.
        Separately, we upsert a LastServedNotice record whose intent is to capture the last saved
        notice across versions and across time, consolidating known user identities

        """
        test_device_id = "f7e54703-cd57-495e-866d-042e67c81734"
        hashed_device = ConsentIdentitiesMixin.hash_value(test_device_id)
        masked_ip = "12.214.31.0"
        mock_anonymize.return_value = masked_ip
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        resp = response.json()
        served_id = resp.pop("served_notice_history_id")

        assert resp == {
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
        }
        assert served_id.startswith("ser_")

        last_served_notice = get_consent_records_by_device_id(
            db, LastServedNoticeV2, test_device_id
        ).first()
        assert last_served_notice.served == resp
        assert last_served_notice.created_at is not None
        assert last_served_notice.updated_at is not None

        served_notice_history = (
            db.query(ServedNoticeHistoryV2)
            .filter(ServedNoticeHistoryV2.served_notice_history_id == served_id)
            .first()
        )
        assert (
            served_notice_history.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )
        assert served_notice_history.created_at is not None
        assert served_notice_history.updated_at is not None
        assert served_notice_history.anonymized_ip_address == masked_ip

        assert (
            served_notice_history.fides_user_device == test_device_id
        )  # Cached here for reporting
        assert served_notice_history.hashed_email is None
        assert (
            served_notice_history.hashed_fides_user_device == hashed_device
        )  # Cached here for reporting
        assert served_notice_history.hashed_phone_number is None
        assert served_notice_history.phone_number is None
        assert (
            served_notice_history.request_origin == RequestOrigin.overlay
        )  # Retrieved from privacy experience history
        assert served_notice_history.url_recorded is None
        assert (
            served_notice_history.user_agent == "testclient"
        )  # Retrieved from request headers
        assert served_notice_history.user_geography == "us_ca"
        assert served_notice_history.acknowledge_mode is False
        assert served_notice_history.serving_component == ServingComponent.banner

        assert (
            served_notice_history.privacy_experience_config_history_id
            == privacy_experience_overlay.experience_config.experience_config_history_id
        )
        assert (
            served_notice_history.privacy_experience_id == privacy_experience_overlay.id
        )

        last_served_notice.delete(db)
        served_notice_history.delete(db)

    def test_record_notices_served_x_forwarded_for(
        self,
        db,
        api_client,
        url,
        request_body,
    ):
        """Assert IP Address is pulled off of x-forwarded-for if it exists"""
        response = api_client.patch(
            url,
            json=request_body,
            headers={
                "Origin": "http://localhost:8080",
                "X-Forwarded-For": "22.104.237.248,0.142.88.40,90.247.24.85",
            },
        )
        assert response.status_code == 200
        use_served_history = ServedNoticeHistoryV2.get_by_served_id(
            db, response.json()["served_notice_history_id"]
        ).first()

        assert use_served_history.anonymized_ip_address == "22.104.237.0"

        last_served_record = get_consent_records_by_device_id(
            db,
            record_type=LastServedNoticeV2,
            value=request_body["browser_identity"]["fides_user_device_id"],
        ).first()
        last_served_record.delete(db)
        use_served_history.delete(db)

    def test_record_notices_served_client_ip(
        self,
        db,
        api_client,
        url,
        request_body,
    ):
        """Assert falls back to client ip if no x-forwarded-for
        In this case, we're using the testclient, whose host is testclient, so IP address
        falls back to None
        """
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        use_served_history = ServedNoticeHistoryV2.get_by_served_id(
            db, response.json()["served_notice_history_id"]
        ).first()
        assert use_served_history.anonymized_ip_address is None
        last_served_record = get_consent_records_by_device_id(
            db,
            LastServedNoticeV2,
            request_body["browser_identity"]["fides_user_device_id"],
        ).first()
        last_served_record.delete(db)
        use_served_history.delete(db)

    def test_duplicate_tcf_special_purpose_served(
        self,
        api_client,
        url,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_special_purposes": [1, 1],
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Duplicate served records saved against TCF component: 'tcf_special_purposes'"
        )

    def test_duplicate_tcf_feature_served(
        self,
        api_client,
        url,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_features": [1, 1],
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Duplicate served records saved against TCF component: 'tcf_features'"
        )

    def test_invalid_tcf_consent_purpose_served(
        self,
        api_client,
        url,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_purpose_consents": [1000],
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Invalid values for tcf_purpose_consents served."
        )

    def test_invalid_tcf_special_purpose_served(
        self,
        api_client,
        url,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_special_purposes": [3],
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Invalid values for tcf_special_purposes served."
        )

    def test_invalid_tcf_features_served(
        self,
        api_client,
        url,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_features": [4],
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Invalid values for tcf_features served."
        )

    def test_invalid_tcf_special_features_served(
        self,
        api_client,
        url,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_special_features": [3],
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Invalid values for tcf_special_features served."
        )

    def test_invalid_system_served(self, api_client, url, db):
        """No longer verifying that system ids exist.  Max number of systems can be very high - just save as-is"""
        device_id = "f7e54703-cd57-495e-866d-042e67c81734"

        request_body = {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "tcf_system_consents": ["bad_system"],
            "user_geography": "us_ca",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 200
        history = ServedNoticeHistoryV2.get_by_served_id(
            db, response.json()["served_notice_history_id"]
        ).first()
        assert history.tcf_served["tcf_system_consents"] == ["bad_system"]

        last_served = get_consent_records_by_device_id(
            db, LastServedNoticeV2, device_id
        ).first()
        assert last_served.served["tcf_system_consents"] == ["bad_system"]

    @mock.patch(
        "fides.api.api.v1.endpoints.served_notice_endpoints_v2.anonymize_ip_address"
    )
    def test_record_tcf_items_served_with_respect_to_fides_user_device_id(
        self,
        mock_anonymize,
        db,
        api_client,
        url,
        tcf_request_body,
        system,
        privacy_experience_france_tcf_overlay,
    ):
        """
        Test saving TCF served for fides user device id

        """
        masked_ip = "12.214.31.0"
        fides_device = "f7e54703-cd57-495e-866d-042e67c81734"
        mock_anonymize.return_value = masked_ip
        response = api_client.patch(
            url, json=tcf_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        resp = response.json()
        served_history_id = resp.pop("served_notice_history_id")

        served_data = {
            "privacy_notice_history_ids": [],
            "tcf_purpose_consents": [5],
            "tcf_purpose_legitimate_interests": [],
            "tcf_special_purposes": [],
            "tcf_vendor_consents": ["gvl.42"],
            "tcf_vendor_legitimate_interests": [],
            "tcf_features": [],
            "tcf_special_features": [2],
            "tcf_system_consents": [],
            "tcf_system_legitimate_interests": [system.id],
        }
        assert resp == served_data

        last_served_record = get_consent_records_by_device_id(
            db, LastServedNoticeV2, fides_device
        ).first()

        assert last_served_record.served == served_data
        assert last_served_record.fides_user_device == fides_device

        served_notice_history = ServedNoticeHistoryV2.get_by_served_id(
            db, served_history_id
        ).first()
        assert served_notice_history.privacy_notice_history_id is None
        assert served_notice_history.created_at is not None
        assert served_notice_history.updated_at is not None
        assert served_notice_history.anonymized_ip_address == masked_ip

        assert (
            served_notice_history.fides_user_device == fides_device
        )  # Cached here for reporting
        assert served_notice_history.hashed_email is None
        assert (
            served_notice_history.hashed_fides_user_device
            == ConsentIdentitiesMixin.hash_value(fides_device)
        )  # Cached here for reporting
        assert served_notice_history.hashed_phone_number is None
        assert served_notice_history.phone_number is None
        assert (
            served_notice_history.request_origin == RequestOrigin.tcf_overlay
        )  # Retrieved from privacy experience history
        assert served_notice_history.url_recorded is None
        assert (
            served_notice_history.user_agent == "testclient"
        )  # Retrieved from request headers
        assert served_notice_history.user_geography == "fr"
        assert served_notice_history.acknowledge_mode is False
        assert served_notice_history.serving_component == ServingComponent.tcf_overlay

        assert (
            served_notice_history.privacy_experience_config_history_id
            == privacy_experience_france_tcf_overlay.experience_config.experience_config_history_id
        )
        assert (
            served_notice_history.privacy_experience_id
            == privacy_experience_france_tcf_overlay.id
        )
        assert served_notice_history.notice_name == "TCF"

        last_served_record.delete(db)
        served_notice_history.delete(db)


class TestSaveNoticesServedPrivacyCenter:
    @pytest.fixture(scope="function")
    def verification_code(self) -> str:
        return "abcd"

    @pytest.fixture(scope="function")
    def request_body(
        self, privacy_notice, verification_code, privacy_experience_privacy_center
    ):
        return {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734"
            },
            "code": verification_code,
            "privacy_notice_history_ids": [privacy_notice.histories[0].id],
            "privacy_experience_id": privacy_experience_privacy_center.id,
            "user_geography": "us_co",
            "serving_component": ServingComponent.privacy_center.value,
        }

    @pytest.fixture(scope="function")
    def tcf_request_body(
        self,
        privacy_notice,
        privacy_experience_france_tcf_overlay,
        system,
        verification_code,
    ):
        return {
            "browser_identity": {
                "fides_user_device_id": "f7e54703-cd57-495e-866d-042e67c81734",
            },
            "code": verification_code,
            "tcf_purpose_consents": [5],
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
            "user_geography": "fr",
            "acknowledge_mode": False,
            "serving_component": ServingComponent.tcf_overlay.value,
        }

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_notices_served_no_matching_consent_request_id(
        self, api_client, request_body
    ):
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id='non_existent_consent_id')}",
            json=request_body,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_notices_served_code_expired(
        self, provided_identity_and_consent_request, api_client, request_body
    ):
        _, consent_request = provided_identity_and_consent_request

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 400
        assert "code expired" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_notices_served_invalid_code(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["code"] = "non_matching_code"
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 403
        assert "Incorrect identification" in response.json()["detail"]

    @pytest.mark.usefixtures("subject_identity_verification_required", "system")
    @mock.patch(
        "fides.api.api.v1.endpoints.served_notice_endpoints_v2.anonymize_ip_address"
    )
    def test_save_notices_served(
        self,
        mock_anonymize,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        db: Session,
        request_body,
        privacy_notice,
        provided_identity_value,
        privacy_experience_privacy_center,
    ):
        """Verify code, save notices served with two identities via privacy center - email and fides device.

        Record is created to capture notices served for these user identities, and a task queued to save
        more data for served reporting.

        """
        masked_ip = "12.214.31.0"  # Mocking because hostname for FastAPI TestClient is "testclient"
        mock_anonymize.return_value = masked_ip

        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        test_device_id = "f7e54703-cd57-495e-866d-042e67c81734"

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 200

        resp = response.json()
        served_id = resp.pop("served_notice_history_id")

        assert resp == {
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
        }

        # Fetch last served notice record that was upserted
        last_served_notice = get_consent_records_by_email(
            db, record_type=LastServedNoticeV2, value=provided_identity_value
        ).first()
        assert last_served_notice.created_at is not None
        assert last_served_notice.updated_at is not None
        assert last_served_notice.email == "test@email.com"
        assert last_served_notice.hashed_email == ConsentIdentitiesMixin.hash_value(
            last_served_notice.email
        )
        assert last_served_notice.fides_user_device == test_device_id
        assert (
            last_served_notice.hashed_fides_user_device
            == ConsentIdentitiesMixin.hash_value(test_device_id)
        )
        assert last_served_notice.served == resp

        # Get corresponding historical record that was created in Background task
        served_notice_history = ServedNoticeHistoryV2.get_by_served_id(db, served_id)
        assert served_notice_history.count() == 1
        served_notice_history = served_notice_history.first()

        assert served_notice_history.served_notice_history_id == served_id
        assert served_notice_history.updated_at is not None
        assert served_notice_history.anonymized_ip_address == masked_ip
        assert served_notice_history.created_at is not None
        assert (
            served_notice_history.fides_user_device == test_device_id
        )  # Cached here for reporting
        assert served_notice_history.hashed_email == ProvidedIdentity.hash_value(
            "test@email.com"
        )

        assert served_notice_history.fides_user_device == test_device_id
        assert (
            served_notice_history.hashed_fides_user_device
            == ConsentIdentitiesMixin.hash_value(test_device_id)
        )  # Cached here for reporting
        assert served_notice_history.hashed_phone_number is None
        assert served_notice_history.phone_number is None
        assert (
            served_notice_history.request_origin == RequestOrigin.privacy_center
        )  # Retrieved from privacy experience history
        assert served_notice_history.url_recorded is None
        assert (
            served_notice_history.user_agent == "testclient"
        )  # Retrieved from request headers
        assert served_notice_history.user_geography == "us_co"
        assert served_notice_history.acknowledge_mode is False
        assert (
            served_notice_history.serving_component == ServingComponent.privacy_center
        )

        assert (
            served_notice_history.privacy_experience_config_history_id
            == privacy_experience_privacy_center.experience_config.experience_config_history_id
        )
        assert (
            served_notice_history.privacy_experience_id
            == privacy_experience_privacy_center.id
        )
        assert (
            served_notice_history.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )

        last_served_notice.delete(db)
        served_notice_history.delete(db)

    @pytest.mark.usefixtures("subject_identity_verification_required", "system")
    def test_save_notices_served_tcf(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        tcf_request_body,
        provided_identity_value,
        db,
    ):
        """Verify code, save purpose served, and return."""
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=tcf_request_body,
        )
        assert response.status_code == 200

        resp = response.json()
        served_id = resp.pop("served_notice_history_id")

        assert resp == {
            "privacy_notice_history_ids": [],
            "tcf_purpose_consents": [5],
            "tcf_purpose_legitimate_interests": [],
            "tcf_special_purposes": [],
            "tcf_vendor_consents": [],
            "tcf_vendor_legitimate_interests": [],
            "tcf_features": [],
            "tcf_special_features": [],
            "tcf_system_consents": [],
            "tcf_system_legitimate_interests": [],
        }

        last_served_notices = get_consent_records_by_email(
            db, record_type=LastServedNoticeV2, value=provided_identity_value
        )
        assert last_served_notices.count() == 1
        last_served_notice = last_served_notices.first()

        assert last_served_notice.created_at is not None
        assert last_served_notice.updated_at is not None
        assert last_served_notice.email == "test@email.com"
        assert last_served_notice.hashed_email == ConsentIdentitiesMixin.hash_value(
            last_served_notice.email
        )
        assert last_served_notice.served == resp

        served_notice_history = db.query(ServedNoticeHistoryV2).filter(
            ServedNoticeHistoryV2.served_notice_history_id == served_id
        )
        assert served_notice_history.count() == 1
        served_notice_history = served_notice_history.first()

        resp.pop("privacy_notice_history_ids")
        assert served_notice_history.tcf_served == resp
        assert served_notice_history.notice_name == "TCF"
        assert served_notice_history.served_notice_history_id == served_id

        served_notice_history.delete(db)
        last_served_notice.delete(db)

    @pytest.mark.usefixtures("subject_identity_verification_required", "system")
    @mock.patch(
        "fides.api.api.v1.endpoints.served_notice_endpoints_v2.anonymize_ip_address"
    )
    def test_save_notices_served_device_id_only(
        self,
        mock_anonymize,
        fides_user_provided_identity_and_consent_request,
        api_client,
        verification_code,
        db: Session,
        request_body,
        privacy_notice,
        privacy_experience_privacy_center,
    ):
        """Verify code, save notices served, and return.

        This tests when someone has set up their privacy center so we're not actually collecting
        email/phone number there.  The original consent request was saved against a fides user
        device id only
        """
        masked_ip = "12.214.31.0"  # Mocking because hostname for FastAPI TestClient is "testclient"
        mock_anonymize.return_value = masked_ip

        (
            fides_user_provided_identity,
            consent_request,
        ) = fides_user_provided_identity_and_consent_request

        consent_request.cache_identity_verification_code(verification_code)

        test_device_id = "051b219f-20e4-45df-82f7-5eb68a00889f"

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 200
        response_json = response.json()

        assert len(response_json["privacy_notice_history_ids"]) == 1

        assert (
            response_json["privacy_notice_history_ids"][0]
            == privacy_notice.histories[0].id
        )

        served_notice_history_id = response_json["served_notice_history_id"]

        # Fetch last served notice record that was updated
        last_served_notice = get_consent_records_by_device_id(
            db, LastServedNoticeV2, test_device_id
        ).first()
        assert last_served_notice.created_at is not None
        assert last_served_notice.updated_at is not None
        assert last_served_notice.served["privacy_notice_history_ids"] == [
            privacy_notice.histories[0].id
        ]

        # Get corresponding historical record that was just created
        served_notice_history = ServedNoticeHistoryV2.get_by_served_id(
            db, response_json["served_notice_history_id"]
        ).first()

        assert (
            served_notice_history.served_notice_history_id == served_notice_history_id
        )
        assert served_notice_history.updated_at is not None
        assert served_notice_history.anonymized_ip_address == masked_ip
        assert served_notice_history.created_at is not None
        assert served_notice_history.email is None
        assert (
            served_notice_history.fides_user_device == test_device_id
        )  # Cached here for reporting
        assert served_notice_history.hashed_email is None
        assert (
            served_notice_history.hashed_fides_user_device
            == ConsentIdentitiesMixin.hash_value(test_device_id)
        )  # Cached here for reporting
        assert served_notice_history.hashed_phone_number is None
        assert served_notice_history.phone_number is None
        assert (
            served_notice_history.request_origin == RequestOrigin.privacy_center
        )  # Retrieved from privacy experience history
        assert served_notice_history.url_recorded is None
        assert (
            served_notice_history.user_agent == "testclient"
        )  # Retrieved from request headers
        assert served_notice_history.user_geography == "us_co"
        assert served_notice_history.acknowledge_mode is False
        assert (
            served_notice_history.serving_component == ServingComponent.privacy_center
        )

        assert (
            served_notice_history.privacy_experience_config_history_id
            == privacy_experience_privacy_center.experience_config.experience_config_history_id
        )
        assert (
            served_notice_history.privacy_experience_id
            == privacy_experience_privacy_center.id
        )
        assert (
            served_notice_history.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )

        last_served_notice.delete(db)
        served_notice_history.delete(db)

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_notices_served_invalid_code_respects_attempt_count(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["code"] = "987632"  # Bad code

        for _ in range(0, CONFIG.security.identity_verification_attempt_limit):
            response = api_client.patch(
                f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
                json=request_body,
            )
            assert response.status_code == 403
            assert "Incorrect identification" in response.json()["detail"]

        assert (
            consent_request._get_cached_verification_code_attempt_count()
            == CONFIG.security.identity_verification_attempt_limit
        )

        request_body["code"] = verification_code
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"] == f"Attempt limit hit for '{consent_request.id}'"
        )
        assert consent_request.get_cached_verification_code() is None
        assert consent_request._get_cached_verification_code_attempt_count() == 0

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @patch("fides.api.models.privacy_request.ConsentRequest.verify_identity")
    def test_save_notices_served_missing_identity_data(
        self,
        mock_verify_identity: MagicMock,
        db,
        api_client,
        verification_code,
        request_body,
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": None,
            "encrypted_value": None,
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        consent_request_data = {
            "provided_identity_id": provided_identity.id,
        }
        consent_request = ConsentRequest.create(db, data=consent_request_data)
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )

        # Used to throw a 404 - throwing error in different location now
        assert response.status_code == 400

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_privacy_notices_served_invalid_privacy_notice_history_id(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["privacy_notice_history_ids"] = ["bad_id"]

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert (
            response.status_code == 400
        ), "Gets picked up by the duplicate privacy notice check"

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_notices_viewed_for_the_same_notice_in_one_request(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
        privacy_notice,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["privacy_notice_history_ids"] = [
            privacy_notice.histories[0].id,
            privacy_notice.histories[0].id,
        ]

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_NOTICES_SERVED.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert (
            response.status_code == 400
        ), "Gets picked up by the duplicate privacy notice check"


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
