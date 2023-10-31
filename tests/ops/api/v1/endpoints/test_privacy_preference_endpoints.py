from datetime import timedelta

import pytest
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.models.privacy_request import ExecutionLogStatus
from fides.common.api.scope_registry import (
    CONSENT_READ,
    CURRENT_PRIVACY_PREFERENCE_READ,
    PRIVACY_PREFERENCE_HISTORY_READ,
)
from fides.common.api.v1.urn_registry import (
    CURRENT_PRIVACY_PREFERENCES_REPORT,
    HISTORICAL_PRIVACY_PREFERENCES_REPORT,
    V1_URL_PREFIX,
)


class TestHistoricalPreferences:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + HISTORICAL_PRIVACY_PREFERENCES_REPORT

    def test_get_historical_preferences_not_authenticated(
        self, api_client: TestClient, url
    ) -> None:
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_historical_preferences_incorrect_scope(
        self, api_client: TestClient, url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONSENT_READ])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_403_FORBIDDEN),
            ("viewer", HTTP_403_FORBIDDEN),
            ("approver", HTTP_403_FORBIDDEN),
        ],
    )
    def test_get_historical_preferences_roles(
        self, role, expected_status, api_client: TestClient, url, generate_role_header
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == expected_status

    def test_get_historical_preferences(
        self,
        db,
        api_client: TestClient,
        url,
        user,
        generate_auth_header,
        privacy_preference_history,
        privacy_request_with_consent_policy,
        served_notice_history,
        system,
        privacy_experience_privacy_center,
    ) -> None:
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.relevant_systems = privacy_preference_history.privacy_notice_history.calculate_relevant_systems(
            db
        )
        privacy_preference_history.save(db)

        privacy_preference_history.update_secondary_user_ids(
            db, {"ljt_readerID": "preference_history_test"}
        )
        privacy_preference_history.cache_system_status(
            db, system=system.fides_key, status=ExecutionLogStatus.complete
        )

        privacy_request_with_consent_policy.reviewed_by = user.id
        privacy_request_with_consent_policy.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_PREFERENCE_HISTORY_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["total"] == 1
        assert response.json()["page"] == 1
        assert response.json()["pages"] == 1
        assert response.json()["size"] == 50

        response_body = response.json()["items"][0]

        assert response_body["id"] == privacy_preference_history.id
        assert (
            response_body["privacy_request_id"]
            == privacy_request_with_consent_policy.id
        )
        assert response_body["email"] == "test@email.com"
        assert response_body["phone_number"] is None
        assert response_body["fides_user_device_id"] is None
        assert response_body["secondary_user_ids"] == {
            "ljt_readerID": "preference_history_test"
        }
        assert response_body["request_timestamp"] is not None
        assert response_body["request_origin"] == "privacy_center"
        assert response_body["request_status"] == "in_processing"
        assert response_body["request_type"] == "consent"
        assert response_body["approver_id"] == "test_fidesops_user"
        assert (
            response_body["privacy_notice_history_id"]
            == privacy_preference_history.privacy_notice_history_id
        )
        assert response_body["privacy_notice_history_id"] is not None
        assert response_body["preference"] == "opt_out"
        assert response_body["tcf_version"] is None
        assert response_body["user_geography"] == "us_ca"
        assert response_body["relevant_systems"] == [system.fides_key]
        assert response_body["affected_system_status"] == {system.fides_key: "complete"}
        assert response_body["url_recorded"] == "https://example.com/privacy_center"
        assert (
            response_body["user_agent"]
            == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
        )
        assert response_body["method"] == "button"
        assert response_body["truncated_ip_address"] == "92.158.1.0"
        assert (
            response_body["experience_config_history_id"]
            == privacy_experience_privacy_center.experience_config.experience_config_history_id
        )
        assert (
            response_body["privacy_experience_id"]
            == privacy_experience_privacy_center.id
        )
        assert response_body["served_notice_history_id"] == served_notice_history.id

    def test_get_historical_preferences_tcf(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_preference_history_for_tcf_purpose_consent,
        served_notice_history_for_tcf_purpose,
        privacy_experience_france_overlay,
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_PREFERENCE_HISTORY_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["total"] == 1
        assert response.json()["page"] == 1
        assert response.json()["size"] == 50

        response_body = response.json()["items"][0]

        assert (
            response_body["id"] == privacy_preference_history_for_tcf_purpose_consent.id
        )
        assert response_body["privacy_request_id"] is None
        assert response_body["email"] == "test@email.com"
        assert response_body["phone_number"] is None
        assert (
            response_body["fides_user_device_id"]
            == "051b219f-20e4-45df-82f7-5eb68a00889f"
        )
        assert response_body["purpose_consent"] == 8
        assert response_body["purpose_legitimate_interests"] is None
        assert response_body["special_purpose"] is None
        assert response_body["vendor_consent"] is None
        assert response_body["vendor_legitimate_interests"] is None
        assert response_body["system_consent"] is None
        assert response_body["system_legitimate_interests"] is None
        assert response_body["feature"] is None
        assert response_body["special_feature"] is None
        assert response_body["tcf_version"] == "2.0"

        assert response_body["request_timestamp"] is not None
        assert response_body["request_origin"] == "tcf_overlay"
        assert response_body["request_status"] is None
        assert response_body["request_type"] == "consent"
        assert response_body["approver_id"] is None
        assert response_body["privacy_notice_history_id"] is None
        assert response_body["preference"] == "opt_out"
        assert response_body["user_geography"] == "fr_idg"
        assert response_body["relevant_systems"] == []
        assert response_body["affected_system_status"] == {}
        assert response_body["url_recorded"] == "example.com/"
        assert (
            response_body["user_agent"]
            == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
        )
        assert response_body["method"] == "button"
        assert response_body["truncated_ip_address"] == "92.158.1.0"
        assert response_body["experience_config_history_id"] is None
        assert (
            response_body["privacy_experience_id"]
            == privacy_experience_france_overlay.id
        )
        assert (
            response_body["served_notice_history_id"]
            == served_notice_history_for_tcf_purpose.id
        )

    def test_get_historical_preferences_saved_for_system(
        self,
        generate_auth_header,
        api_client,
        url,
        privacy_preference_history_for_system,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_PREFERENCE_HISTORY_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert (
            response.json()["items"][0]["system_consent"]
            == privacy_preference_history_for_system.system_consent
        )
        assert (
            response.json()["items"][0]["preference"]
            == privacy_preference_history_for_system.preference.value
        )

    def test_get_historical_preferences_user_geography_unsupported(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_preference_history_fr_provide_service_frontend_only,
    ) -> None:
        """Just verifying it's fine if the user geography is not an official privacy notice region"""

        auth_header = generate_auth_header(scopes=[PRIVACY_PREFERENCE_HISTORY_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["total"] == 1
        assert response.json()["page"] == 1
        assert response.json()["pages"] == 1
        assert response.json()["size"] == 50

        response_body = response.json()["items"][0]

        assert (
            response_body["id"]
            == privacy_preference_history_fr_provide_service_frontend_only.id
        )
        assert response_body["user_geography"] == "fr_idg"

    def test_get_historical_preferences_ordering(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
        privacy_preference_history_fr_provide_service_frontend_only,
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_PREFERENCE_HISTORY_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 3
        assert response.json()["total"] == 3
        assert response.json()["page"] == 1
        assert response.json()["pages"] == 1
        assert response.json()["size"] == 50

        response_body = response.json()["items"]

        # Records ordered most recently created first
        assert (
            response_body[0]["id"]
            == privacy_preference_history_fr_provide_service_frontend_only.id
        )
        assert response_body[1]["id"] == privacy_preference_history_us_ca_provide.id
        assert response_body[2]["id"] == privacy_preference_history.id

    def test_get_historical_preferences_date_filtering(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
        privacy_preference_history_fr_provide_service_frontend_only,
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_PREFERENCE_HISTORY_READ])

        # Filter for everything created before the first preference
        response = api_client.get(
            url
            + f"?request_timestamp_lt={privacy_preference_history.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["items"] == []

        # Filter for everything created before the last preference plus an hour
        response = api_client.get(
            url
            + f"?request_timestamp_lt={(privacy_preference_history_fr_provide_service_frontend_only.created_at + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 3

        assert (
            response.json()["items"][0]["id"]
            == privacy_preference_history_fr_provide_service_frontend_only.id
        )
        assert (
            response.json()["items"][1]["id"]
            == privacy_preference_history_us_ca_provide.id
        )
        assert response.json()["items"][2]["id"] == privacy_preference_history.id

        # Filter for everything created after the first preference
        response = api_client.get(
            url
            + f"?request_timestamp_gt={privacy_preference_history.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert (
            response.json()["items"][0]["id"]
            == privacy_preference_history_fr_provide_service_frontend_only.id
        )
        assert (
            response.json()["items"][1]["id"]
            == privacy_preference_history_us_ca_provide.id
        )

        # Invalid filter
        response = api_client.get(
            url
            + f"?request_timestamp_lt={privacy_preference_history.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}&request_timestamp_gt={privacy_preference_history_fr_provide_service_frontend_only.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 400
        assert "Value specified for request_timestamp_lt" in response.json()["detail"]
        assert "must be after request_timestamp_gt" in response.json()["detail"]


class TestCurrentPrivacyPreferences:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + CURRENT_PRIVACY_PREFERENCES_REPORT

    def test_get_current_preferences_not_authenticated(
        self, api_client: TestClient, url
    ) -> None:
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_current_preferences_incorrect_scope(
        self, api_client: TestClient, url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONSENT_READ])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_current_preferences_report_with_tcf(
        self,
        generate_auth_header,
        privacy_preference_history_for_tcf_purpose_consent,
        api_client,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CURRENT_PRIVACY_PREFERENCE_READ])

        response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        data = response.json()["items"][0]
        assert (
            data["preference"]
            == privacy_preference_history_for_tcf_purpose_consent.preference.value
        )
        assert data["purpose_consent"] == 8
        assert (
            data["id"]
            == privacy_preference_history_for_tcf_purpose_consent.current_privacy_preference.id
        )

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_403_FORBIDDEN),
            ("viewer", HTTP_403_FORBIDDEN),
            ("approver", HTTP_403_FORBIDDEN),
        ],
    )
    def test_get_current_preferences_roles(
        self, role, expected_status, api_client: TestClient, url, generate_role_header
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == expected_status

    def test_get_current_preferences(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_preference_history,
    ) -> None:
        current_preference = privacy_preference_history.current_privacy_preference

        auth_header = generate_auth_header(scopes=[CURRENT_PRIVACY_PREFERENCE_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["total"] == 1
        assert response.json()["page"] == 1
        assert response.json()["pages"] == 1
        assert response.json()["size"] == 50

        response_body = response.json()["items"][0]

        assert response_body["id"] == current_preference.id
        assert response_body["preference"] == current_preference.preference.value
        assert (
            response_body["privacy_notice_history_id"]
            == current_preference.privacy_notice_history.id
        )
        assert (
            response_body["provided_identity_id"]
            == privacy_preference_history.provided_identity.id
        )
        assert response_body["created_at"] is not None

    def test_get_current_preference_ordering(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
        privacy_preference_history_fr_provide_service_frontend_only,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CURRENT_PRIVACY_PREFERENCE_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 3
        assert response.json()["total"] == 3
        assert response.json()["page"] == 1
        assert response.json()["pages"] == 1
        assert response.json()["size"] == 50

        response_body = response.json()["items"]

        # Records ordered most recently created first
        assert (
            response_body[0]["id"]
            == privacy_preference_history_fr_provide_service_frontend_only.current_privacy_preference.id
        )
        assert (
            response_body[1]["id"]
            == privacy_preference_history_us_ca_provide.current_privacy_preference.id
        )
        assert (
            response_body[2]["id"]
            == privacy_preference_history.current_privacy_preference.id
        )

    def test_get_current_preferences_date_filtering(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
        privacy_preference_history_fr_provide_service_frontend_only,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CURRENT_PRIVACY_PREFERENCE_READ])

        # Filter for everything updated before the first preference
        response = api_client.get(
            url
            + f"?updated_lt={privacy_preference_history.current_privacy_preference.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["items"] == []

        # Filter for everything updated before the last preference plus an hour
        response = api_client.get(
            url
            + f"?updated_lt={(privacy_preference_history_fr_provide_service_frontend_only.current_privacy_preference.updated_at + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 3

        assert (
            response.json()["items"][0]["id"]
            == privacy_preference_history_fr_provide_service_frontend_only.current_privacy_preference.id
        )
        assert (
            response.json()["items"][1]["id"]
            == privacy_preference_history_us_ca_provide.current_privacy_preference.id
        )
        assert (
            response.json()["items"][2]["id"]
            == privacy_preference_history.current_privacy_preference.id
        )

        # Filter for everything updated after the first preference
        response = api_client.get(
            url
            + f"?updated_gt={privacy_preference_history.current_privacy_preference.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert (
            response.json()["items"][0]["id"]
            == privacy_preference_history_fr_provide_service_frontend_only.current_privacy_preference.id
        )
        assert (
            response.json()["items"][1]["id"]
            == privacy_preference_history_us_ca_provide.current_privacy_preference.id
        )

        # Invalid filter
        response = api_client.get(
            url
            + f"?updated_lt={privacy_preference_history.current_privacy_preference.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}&updated_gt={privacy_preference_history_fr_provide_service_frontend_only.current_privacy_preference.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f')}",
            headers=auth_header,
        )
        assert response.status_code == 400
        assert "Value specified for updated_lt" in response.json()["detail"]
        assert "must be after updated_gt" in response.json()["detail"]
