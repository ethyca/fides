from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_preference import (
    CURRENT_TCF_VERSION,
    LastServedNotice,
    RequestOrigin,
    ServedNoticeHistory,
    ServingComponent,
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
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
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
        masked_ip = "12.214.31.0"
        mock_anonymize.return_value = masked_ip
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        response_json = response.json()[0]
        assert (
            response_json["privacy_notice_history"]["id"]
            == privacy_notice.histories[0].id
        )

        served_notice_history_id = response_json["served_notice_history_id"]

        # Fetch last served notice record that was updated
        last_served_notice = LastServedNotice.get(db, object_id=response_json["id"])
        assert last_served_notice.created_at is not None
        assert last_served_notice.updated_at is not None
        assert last_served_notice.provided_identity_id is None
        assert last_served_notice.fides_user_device_provided_identity_id is not None
        assert last_served_notice.privacy_notice_id == privacy_notice.id
        assert (
            last_served_notice.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )

        # Get corresponding historical record that was just created
        served_notice_history = last_served_notice.served_notice_history

        assert served_notice_history.id == served_notice_history_id
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
            == ProvidedIdentity.hash_value(test_device_id)
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

        fides_user_device_provided_identity = (
            served_notice_history.fides_user_device_provided_identity
        )
        # Same fides user device identity added to both the historical and current record
        assert (
            last_served_notice.fides_user_device_provided_identity
            == fides_user_device_provided_identity
        )
        assert (
            fides_user_device_provided_identity.hashed_value
            == ProvidedIdentity.hash_value(test_device_id)
        )
        assert (
            fides_user_device_provided_identity.encrypted_value["value"]
            == test_device_id
        )

        assert (
            served_notice_history.privacy_experience_config_history_id
            == privacy_experience_overlay.experience_config.experience_config_history_id
        )
        assert (
            served_notice_history.privacy_experience_id == privacy_experience_overlay.id
        )
        assert (
            served_notice_history.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )
        assert served_notice_history.provided_identity_id is None

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
        assert len(response.json()) == 1
        use_served_history = ServedNoticeHistory.get(
            db, object_id=response.json()[0]["served_notice_history_id"]
        )
        assert use_served_history.anonymized_ip_address == "22.104.237.0"

        last_served_record = LastServedNotice.get(
            db, object_id=use_served_history.last_served_record.id
        )
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
        assert len(response.json()) == 1
        use_served_history = ServedNoticeHistory.get(
            db, object_id=response.json()[0]["served_notice_history_id"]
        )
        assert use_served_history.anonymized_ip_address is None
        last_served_record = LastServedNotice.get(
            db, object_id=use_served_history.last_served_record.id
        )
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

    def test_invalid_system_served(
        self,
        api_client,
        url,
    ):
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
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Can't save consent against invalid system id 'bad_system'."
        )

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
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
        """Test recording that TCF vendors and data uses were served to the given user with this fides user device id
        There was one vendor and one data use in this request body, so two ServedNoticeHistory records were created
        along with two LastServedNotice records.

        """
        masked_ip = "12.214.31.0"
        mock_anonymize.return_value = masked_ip
        response = api_client.patch(
            url, json=tcf_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 4
        purpose_served = response.json()[0]
        special_feature_served = response.json()[1]
        vendor_served = response.json()[2]
        system_served = response.json()[3]

        # Assert purpose consent served portion of response
        assert purpose_served["purpose_consent"] == 5
        assert purpose_served["purpose_legitimate_interests"] is None
        assert purpose_served["vendor_consent"] is None
        assert purpose_served["vendor_legitimate_interests"] is None
        assert purpose_served["feature"] is None
        assert purpose_served["special_feature"] is None
        assert purpose_served["special_purpose"] is None
        assert purpose_served["privacy_notice_history"] is None
        purpose_served_id = purpose_served["id"]
        purpose_served_history_id = purpose_served["served_notice_history_id"]

        # Assert special feature served portion of response
        assert special_feature_served["purpose_consent"] is None
        assert special_feature_served["purpose_legitimate_interests"] is None
        assert special_feature_served["vendor_consent"] is None
        assert special_feature_served["vendor_legitimate_interests"] is None
        assert special_feature_served["feature"] is None
        assert special_feature_served["special_purpose"] is None
        assert special_feature_served["special_feature"] == 2
        assert special_feature_served["privacy_notice_history"] is None
        last_served_special_feature = LastServedNotice.get(
            db, object_id=special_feature_served["id"]
        )

        # Assert vendor served portion of response
        assert vendor_served["purpose_consent"] is None
        assert vendor_served["purpose_legitimate_interests"] is None
        assert vendor_served["vendor_consent"] == "gvl.42"
        assert vendor_served["vendor_legitimate_interests"] is None
        assert vendor_served["feature"] is None
        assert vendor_served["special_purpose"] is None
        assert vendor_served["privacy_notice_history"] is None
        vendor_served_id = vendor_served["id"]
        vendor_served_history_id = vendor_served["served_notice_history_id"]

        # Assert system served portion of response
        assert system_served["purpose_consent"] is None
        assert system_served["purpose_legitimate_interests"] is None
        assert system_served["vendor_consent"] is None
        assert system_served["vendor_legitimate_interests"] is None
        assert system_served["feature"] is None
        assert system_served["special_feature"] is None
        assert system_served["system_consent"] is None
        assert system_served["system_legitimate_interests"] == system.id
        assert system_served["privacy_notice_history"] is None
        last_served_system = LastServedNotice.get(db, object_id=system_served["id"])

        # Assert db records created for last served and served notice history for the purpose
        last_served_use = LastServedNotice.get(db, object_id=purpose_served_id)
        assert last_served_use.purpose_consent == 5
        assert last_served_use.purpose_legitimate_interests is None
        assert last_served_use.privacy_notice_id is None
        assert last_served_use.privacy_notice_history_id is None
        assert last_served_use.vendor_consent is None
        assert last_served_use.vendor_legitimate_interests is None
        assert last_served_use.system_consent is None
        assert last_served_use.system_legitimate_interests is None
        assert last_served_use.feature is None
        assert last_served_use.created_at is not None
        assert last_served_use.updated_at is not None
        assert last_served_use.tcf_version == CURRENT_TCF_VERSION
        assert last_served_use.served_notice_history_id == purpose_served_history_id
        use_served_history = ServedNoticeHistory.get(
            db, object_id=purpose_served_history_id
        )
        assert (
            use_served_history.fides_user_device_provided_identity_id
            == last_served_use.fides_user_device_provided_identity_id
        )
        assert use_served_history.purpose_consent == 5
        assert (
            use_served_history.privacy_experience_id
            == privacy_experience_france_tcf_overlay.id
        )

        # Assert db records created for last served and served notice history for the vendor
        last_served_vendor = LastServedNotice.get(db, object_id=vendor_served_id)
        assert last_served_vendor.purpose_consent is None
        assert last_served_vendor.purpose_legitimate_interests is None
        assert last_served_vendor.privacy_notice_id is None
        assert last_served_vendor.privacy_notice_history_id is None
        assert last_served_vendor.vendor_consent == "gvl.42"
        assert last_served_vendor.vendor_legitimate_interests is None
        assert last_served_vendor.feature is None
        assert last_served_vendor.created_at is not None
        assert last_served_vendor.updated_at is not None
        assert last_served_vendor.served_notice_history_id == vendor_served_history_id
        vendor_served_history = ServedNoticeHistory.get(
            db, object_id=vendor_served_history_id
        )
        assert (
            vendor_served_history.fides_user_device_provided_identity_id
            == last_served_vendor.fides_user_device_provided_identity_id
        )
        assert vendor_served_history.vendor_consent == "gvl.42"
        assert vendor_served_history.vendor_legitimate_interests is None
        assert (
            vendor_served_history.privacy_experience_id
            == privacy_experience_france_tcf_overlay.id
        )

        # Assert special feature last served
        assert last_served_special_feature.special_feature == 2
        special_feature_served_history = ServedNoticeHistory.get(
            db, object_id=last_served_special_feature.served_notice_history_id
        )
        assert special_feature_served_history.special_feature == 2

        # Assert system last served
        assert last_served_system.system_legitimate_interests == system.id
        system_served_history = ServedNoticeHistory.get(
            db, object_id=last_served_system.served_notice_history_id
        )
        assert system_served_history.system_consent is None
        assert system_served_history.system_legitimate_interests == system.id

        last_served_system.delete(db)
        system_served_history.delete(db)

        last_served_special_feature.delete(db)
        special_feature_served_history.delete(db)

        last_served_vendor.delete(db)
        last_served_use.delete(db)


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
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
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
        privacy_experience_privacy_center,
    ):
        """Verify code, save notices served, and return.

        The fact that notices were served is saved with respect to two provided identities -
        one for the email and one for the fides user device id
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
        assert len(response.json()) == 1
        response_json = response.json()[0]

        assert (
            response_json["privacy_notice_history"]["id"]
            == privacy_notice.histories[0].id
        )

        served_notice_history_id = response_json["served_notice_history_id"]

        # Fetch last served notice record that was updated
        last_served_notice = LastServedNotice.get(db, object_id=response_json["id"])
        assert last_served_notice.created_at is not None
        assert last_served_notice.updated_at is not None
        assert last_served_notice.provided_identity_id == provided_identity.id
        assert last_served_notice.fides_user_device_provided_identity_id is not None
        assert last_served_notice.privacy_notice_id == privacy_notice.id
        assert (
            last_served_notice.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )

        # Get corresponding historical record that was just created
        served_notice_history = last_served_notice.served_notice_history

        assert served_notice_history.id == served_notice_history_id
        assert served_notice_history.updated_at is not None
        assert served_notice_history.anonymized_ip_address == masked_ip
        assert served_notice_history.created_at is not None
        assert served_notice_history.email == "test@email.com"
        assert (
            served_notice_history.fides_user_device == test_device_id
        )  # Cached here for reporting
        assert served_notice_history.hashed_email == ProvidedIdentity.hash_value(
            "test@email.com"
        )
        assert (
            served_notice_history.hashed_fides_user_device
            == ProvidedIdentity.hash_value(test_device_id)
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

        fides_user_device_provided_identity = (
            served_notice_history.fides_user_device_provided_identity
        )
        # Same fides user device identity added to both the historical and current record
        assert (
            last_served_notice.fides_user_device_provided_identity
            == fides_user_device_provided_identity
        )
        assert (
            fides_user_device_provided_identity.hashed_value
            == ProvidedIdentity.hash_value(test_device_id)
        )
        assert (
            fides_user_device_provided_identity.encrypted_value["value"]
            == test_device_id
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
        assert served_notice_history.provided_identity_id == provided_identity.id

        last_served_notice.delete(db)
        served_notice_history.delete(db)

    @pytest.mark.usefixtures("subject_identity_verification_required", "system")
    def test_save_notices_served_tcf(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        tcf_request_body,
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
        assert len(response.json()) == 1
        response_json = response.json()[0]

        assert response_json["purpose_consent"] == 5
        served_history_id = response_json["served_notice_history_id"]
        record = (
            db.query(ServedNoticeHistory)
            .filter(ServedNoticeHistory.id == served_history_id)
            .first()
        )
        assert record.purpose_consent == 5

        current = record.last_served_record

        current.delete(db)
        record.delete(db)

    @pytest.mark.usefixtures("subject_identity_verification_required", "system")
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
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
        assert len(response.json()) == 1
        response_json = response.json()[0]

        assert (
            response_json["privacy_notice_history"]["id"]
            == privacy_notice.histories[0].id
        )

        served_notice_history_id = response_json["served_notice_history_id"]

        # Fetch last served notice record that was updated
        last_served_notice = LastServedNotice.get(db, object_id=response_json["id"])
        assert last_served_notice.created_at is not None
        assert last_served_notice.updated_at is not None
        assert last_served_notice.provided_identity_id is None
        assert (
            last_served_notice.fides_user_device_provided_identity_id
            == fides_user_provided_identity.id
        )
        assert last_served_notice.privacy_notice_id == privacy_notice.id
        assert (
            last_served_notice.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )

        # Get corresponding historical record that was just created
        served_notice_history = last_served_notice.served_notice_history

        assert served_notice_history.id == served_notice_history_id
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
            == ProvidedIdentity.hash_value(test_device_id)
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

        fides_user_device_provided_identity = (
            served_notice_history.fides_user_device_provided_identity
        )
        # Same fides user device identity added to both the historical and current record
        assert (
            last_served_notice.fides_user_device_provided_identity
            == fides_user_provided_identity
            == fides_user_device_provided_identity
        )
        assert (
            fides_user_device_provided_identity.hashed_value
            == ProvidedIdentity.hash_value(test_device_id)
        )
        assert (
            fides_user_device_provided_identity.encrypted_value["value"]
            == test_device_id
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
        assert served_notice_history.provided_identity_id is None

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

        assert response.status_code == 404
        assert mock_verify_identity.called
        assert "missing" in response.json()["detail"]

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
