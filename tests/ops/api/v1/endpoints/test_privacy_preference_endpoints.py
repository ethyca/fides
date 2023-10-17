from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.models.privacy_preference import (
    CURRENT_TCF_VERSION,
    ConsentMethod,
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    RequestOrigin,
    UserConsentPreference,
)
from fides.api.models.privacy_request import (
    ConsentRequest,
    ExecutionLogStatus,
    PrivacyRequestStatus,
    ProvidedIdentity,
)
from fides.api.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.util.tcf.tcf_experience_contents import ConsentRecordType
from fides.common.api.scope_registry import (
    CONSENT_READ,
    CURRENT_PRIVACY_PREFERENCE_READ,
    PRIVACY_PREFERENCE_HISTORY_READ,
)
from fides.common.api.v1.urn_registry import (
    CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY,
    CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID,
    CURRENT_PRIVACY_PREFERENCES_REPORT,
    HISTORICAL_PRIVACY_PREFERENCES_REPORT,
    PRIVACY_PREFERENCES,
    V1_URL_PREFIX,
)
from fides.config import CONFIG


class TestSavePrivacyPreferencesPrivacyCenter:
    @pytest.fixture(scope="function")
    def verification_code(self) -> str:
        return "abcd"

    @pytest.fixture(scope="function")
    def request_body(
        self, privacy_notice, verification_code, consent_policy, served_notice_history
    ):
        return {
            "browser_identity": {"ga_client_id": "test"},
            "code": verification_code,
            "preferences": [
                {
                    "privacy_notice_history_id": privacy_notice.histories[0].id,
                    "preference": "opt_out",
                    "served_notice_history_id": served_notice_history.id,
                }
            ],
            "policy_key": consent_policy.key,
            "user_geography": "us_ca",
        }

    @pytest.fixture(scope="function")
    def tcf_request_body(self, privacy_notice, verification_code, consent_policy):
        return {
            "browser_identity": {"ga_client_id": "test"},
            "code": verification_code,
            "feature_preferences": [
                {
                    "id": 1,
                    "preference": "opt_out",
                }
            ],
            "policy_key": consent_policy.key,
            "user_geography": "fr",
        }

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_privacy_preferences_no_consent_request_id(
        self, api_client, request_body
    ):
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id='non_existent_consent_id')}",
            json=request_body,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_privacy_preferences_no_consent_code(
        self, provided_identity_and_consent_request, api_client, privacy_notice
    ):
        _, consent_request = provided_identity_and_consent_request

        data = {
            "browser_identity": {"ga_client_id": "test_ga_client_id"},
            "code": "12345",
            "preferences": [
                {
                    "privacy_notice_history_id": privacy_notice.histories[0].id,
                    "preference": "opt_out",
                }
            ],
            "user_geography": "us_ca",
        }

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )
        assert response.status_code == 400
        assert "code expired" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_privacy_preferences_invalid_code(
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
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 403
        assert "Incorrect identification" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required", "automatically_approved", "system"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
    )
    def test_verify_then_set_privacy_preferences(
        self,
        mock_anonymize,
        run_privacy_request_mock,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        db: Session,
        request_body,
        privacy_notice,
    ):
        """Verify code, save, and then return privacy preferences
        Privacy request also queued because a notice has system wide enforcement
        """
        masked_ip = "12.214.31.0"  # Mocking because hostname for FastAPI TestClient is "testclient"
        mock_anonymize.return_value = masked_ip

        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        # Assert no existing privacy preferences exist for this identity
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "pages": 0,
            "size": 50,
        }

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 200
        assert len(response.json()["preferences"]) == 1
        assert response.json()["fides_mobile_data"] is None

        response_json = response.json()["preferences"][0]
        created_privacy_preference_history_id = response_json[
            "privacy_preference_history_id"
        ]
        privacy_preference_history = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id == created_privacy_preference_history_id
            )
            .first()
        )
        assert response_json["preference"] == "opt_out"

        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )
        db.refresh(consent_request)
        assert consent_request.privacy_request_id

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        response_json = response.json()["items"][0]
        assert response_json["id"] is not None
        assert response_json["preference"] == "opt_out"
        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )

        assert privacy_preference_history.privacy_request_id is not None
        assert run_privacy_request_mock.called

        privacy_preference_history.delete(db=db)

    @pytest.mark.usefixtures(
        "subject_identity_verification_required", "automatically_approved", "system"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
    )
    def test_verify_then_set_privacy_preferences_but_no_privacy_request_created(
        self,
        mock_anonymize,
        run_privacy_request_mock,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        db: Session,
        privacy_notice_fr_provide_service_frontend_only,
        privacy_experience_france_overlay,
        consent_policy,
    ):
        """Verify code, save, and then return privacy preferences
        Privacy request not queued because no notice has system wide enforcement
        """
        masked_ip = "12.214.31.0"  # Mocking because hostname for FastAPI TestClient is "testclient"
        mock_anonymize.return_value = masked_ip

        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        # Assert no existing privacy preferences exist for this identity
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "pages": 0,
            "size": 50,
        }

        request_body = {
            "browser_identity": {"ga_client_id": "test"},
            "code": verification_code,
            "preferences": [
                {
                    "privacy_notice_history_id": privacy_notice_fr_provide_service_frontend_only.histories[
                        0
                    ].id,
                    "preference": "opt_out",
                }
            ],
            "policy_key": consent_policy.key,
            "user_geography": "fr_idg",
            "privacy_experience_id": privacy_experience_france_overlay.id,
            "method": "button",
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 200
        assert len(response.json()["preferences"]) == 1
        assert response.json()["fides_mobile_data"] is None

        response_json = response.json()["preferences"][0]
        created_privacy_preference_history_id = response_json[
            "privacy_preference_history_id"
        ]
        privacy_preference_history = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id == created_privacy_preference_history_id
            )
            .first()
        )
        assert response_json["preference"] == "opt_out"

        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(
                privacy_notice_fr_provide_service_frontend_only.histories[0]
            ).dict()
        )
        db.refresh(consent_request)
        # No privacy request created here
        assert not consent_request.privacy_request_id

        # Privacy request not created or queued
        assert privacy_preference_history.privacy_request_id is None
        assert not run_privacy_request_mock.called

        assert privacy_preference_history.user_geography == "fr_idg"

        privacy_preference_history.delete(db=db)

    @pytest.mark.usefixtures(
        "subject_identity_verification_not_required", "automatically_approved"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
    )
    def test_set_privacy_preferences_privacy_center_fides_user_device_id_only(
        self,
        mock_anonymize,
        run_privacy_request_mock,
        fides_user_provided_identity_and_consent_request,
        api_client,
        verification_code,
        db: Session,
        request_body,
        privacy_notice,
    ):
        """Test the workflow where consent preferences were saved in the privacy center against
        a fides user device id only - no email or phone number.  This ProvidedIdentity needs to be
        saved as the PrivacyPreferenceHistory.fides_user_device_provided_identity_id record.

        Also asserts these same preferences can be retrieved via the consent request verify endpoint
        """
        masked_ip = "12.214.31.0"
        mock_anonymize.return_value = masked_ip

        (
            fides_user_provided_identity,
            consent_request,
        ) = fides_user_provided_identity_and_consent_request

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 200
        assert len(response.json()["preferences"]) == 1
        assert response.json()["fides_mobile_data"] is None

        response_json = response.json()["preferences"][0]
        created_privacy_preference_history_id = response_json[
            "privacy_preference_history_id"
        ]
        privacy_preference_history = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id == created_privacy_preference_history_id
            )
            .first()
        )
        assert privacy_preference_history.email is None
        assert (
            privacy_preference_history.fides_user_device
            == fides_user_provided_identity.encrypted_value["value"]
        )
        assert privacy_preference_history.provided_identity is None
        assert (
            privacy_preference_history.fides_user_device_provided_identity
            == fides_user_provided_identity,
            "Assert fides user device provided identity ",
        )
        assert privacy_preference_history.phone_number is None
        assert privacy_preference_history.preference == UserConsentPreference.opt_out

        assert response_json["preference"] == "opt_out"

        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )
        db.refresh(consent_request)
        assert consent_request.privacy_request_id

        # Assert preferences can be retrieved under fides user device id only
        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        response_json = response.json()["items"][0]
        assert response_json["id"] is not None
        assert response_json["preference"] == "opt_out"
        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )

        # Test no experience specified, so no request origin
        assert privacy_preference_history.request_origin is None
        assert privacy_preference_history.user_agent == "testclient"
        assert privacy_preference_history.privacy_experience_config_history_id is None
        assert privacy_preference_history.privacy_experience_id is None
        assert mock_anonymize.call_args.args[0] == "testclient"
        assert privacy_preference_history.anonymized_ip_address == masked_ip
        assert privacy_preference_history.url_recorded is None

        # Fetch current privacy preference
        current_preference = CurrentPrivacyPreference.get(
            db, object_id=response_json["id"]
        )
        assert current_preference.preference == UserConsentPreference.opt_out
        assert (
            current_preference.privacy_notice_history_id
            == privacy_notice.histories[0].id
        )

        privacy_preference_history.delete(db=db)
        assert run_privacy_request_mock.called

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_privacy_preferences_invalid_code_respects_attempt_count(
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
                f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
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
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
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
    def test_set_privacy_preferences_no_email_provided(
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
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )

        assert response.status_code == 404
        assert mock_verify_identity.called
        assert "missing" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_privacy_preferences_no_privacy_preferences_present(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["preferences"] = None

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 422

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_privacy_preferences_invalid_privacy_notice_history_id(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["preferences"][0]["privacy_notice_history_id"] = "bad_id"

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert (
            response.status_code == 400
        ), "Gets picked up by the duplicate privacy notice check"

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_duplicate_preferences_for_the_same_notice_in_one_request(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
        privacy_notice,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["preferences"].append(
            {
                "privacy_notice_history_id": privacy_notice.histories[0].id,
                "preference": "opt_in",
            }
        )

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert (
            response.status_code == 400
        ), "Gets picked up by the duplicate privacy notice check"

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_save_preferences_invalid_served_notice_history_id(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        request_body,
        privacy_notice,
        served_notice_history_us_ca_provide_for_fides_user,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["preferences"][0][
            "served_notice_history_id"
        ] = served_notice_history_us_ca_provide_for_fides_user.id

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == f"The ServedNoticeHistory record '{served_notice_history_us_ca_provide_for_fides_user.id}' did not serve the privacy notice history '{privacy_notice.histories[0].id}'."
        )

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
        "automatically_approved",
        "consent_policy",
        "system",
    )
    @patch("fides.api.models.privacy_request.ConsentRequest.verify_identity")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_set_privacy_preferences(
        self,
        mock_run_privacy_request: MagicMock,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
        request_body,
        privacy_notice,
        privacy_notice_us_ca_provide,
        served_notice_history,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["preferences"].append(
            {
                "privacy_notice_history_id": privacy_notice_us_ca_provide.histories[
                    0
                ].id,
                "preference": "opt_in",
            }
        )

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )

        assert response.status_code == 200
        assert len(response.json()["preferences"]) == 2
        assert response.json()["fides_mobile_data"] is None

        response_json = response.json()["preferences"]

        first_privacy_preference_history_created = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id
                == response_json[0]["privacy_preference_history_id"]
            )
            .first()
        )
        assert response_json[0]["preference"] == "opt_out"

        assert (
            response_json[0]["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )

        second_privacy_preference_history_created = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id
                == response_json[1]["privacy_preference_history_id"]
            )
            .first()
        )
        assert response_json[1]["preference"] == "opt_in"
        assert (
            response_json[1]["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(
                privacy_notice_us_ca_provide.histories[0]
            ).dict()
        )
        assert verification_code in mock_verify_identity.call_args_list[0].args

        db.refresh(first_privacy_preference_history_created)
        db.refresh(second_privacy_preference_history_created)

        assert (
            first_privacy_preference_history_created.served_notice_history_id
            == served_notice_history.id
        )
        assert (
            second_privacy_preference_history_created.served_notice_history_id is None
        )

        assert first_privacy_preference_history_created.privacy_request_id is not None
        assert second_privacy_preference_history_created.privacy_request_id is not None

        identity = (
            first_privacy_preference_history_created.privacy_request.get_persisted_identity()
        )
        assert identity.email == "test@email.com", (
            "Identity pulled from Privacy Request Provided Identity and used to "
            "create a Privacy Request provided identity "
        )
        assert identity.phone_number is None
        assert identity.ga_client_id == "test", (
            "Browser identity pulled from Privacy Request Provided Identity and persisted "
            "to a Privacy Request provided identity"
        )

        privacy_request = first_privacy_preference_history_created.privacy_request
        assert privacy_request.status == PrivacyRequestStatus.pending
        assert privacy_request.privacy_preferences == [
            first_privacy_preference_history_created,
            second_privacy_preference_history_created,
        ], "Same privacy request created to propagate both preferences"

        db.refresh(consent_request)
        assert (
            consent_request.privacy_request_id == privacy_request.id
        ), "Privacy request id also saved on Consent request for record keeping"
        assert mock_run_privacy_request.called

        current_privacy_preference_one = (
            first_privacy_preference_history_created.current_privacy_preference
        )
        current_privacy_preference_two = (
            second_privacy_preference_history_created.current_privacy_preference
        )
        assert (
            current_privacy_preference_one.preference == UserConsentPreference.opt_out
        ), "History preferences saved to latest preferences"
        assert (
            current_privacy_preference_two.preference == UserConsentPreference.opt_in
        ), "History preferences saved to latest preferences"

        first_privacy_preference_history_created.delete(db)
        second_privacy_preference_history_created.delete(db)

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
        "automatically_approved",
        "consent_policy",
        "system",
        "enable_tcf",
    )
    @patch("fides.api.models.privacy_request.ConsentRequest.verify_identity")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_set_privacy_preferences_tcf(
        self,
        mock_run_privacy_request: MagicMock,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
        tcf_request_body,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=tcf_request_body,
        )

        assert response.status_code == 200
        assert response.json()["fides_mobile_data"] is None
        assert len(response.json()["preferences"]) == 0
        assert len(response.json()["feature_preferences"]) == 1

        response_json = response.json()["feature_preferences"]

        first_privacy_preference_history_created = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id
                == response_json[0]["privacy_preference_history_id"]
            )
            .first()
        )
        assert response_json[0]["preference"] == "opt_out"
        assert response_json[0]["feature"] == 1

        assert first_privacy_preference_history_created.feature == 1
        assert (
            first_privacy_preference_history_created.preference
            == UserConsentPreference.opt_out
        )
        assert (
            first_privacy_preference_history_created.consent_record_type
            == ConsentRecordType.feature
        )

        current_preference = (
            first_privacy_preference_history_created.current_privacy_preference
        )

        assert current_preference.feature == 1
        assert current_preference.preference == UserConsentPreference.opt_out

        assert verification_code in mock_verify_identity.call_args_list[0].args

        current_preference.delete(db)
        first_privacy_preference_history_created.delete(db)

        assert not mock_run_privacy_request.called

    @pytest.mark.usefixtures(
        "subject_identity_verification_required", "automatically_approved"
    )
    @patch("fides.api.models.privacy_request.ConsentRequest.verify_identity")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_set_privacy_preferences_bad_policy_key(
        self,
        mock_run_privacy_request: MagicMock,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
        request_body,
        privacy_notice,
    ):
        """Even though privacy request creation fails, privacy preferences are still saved"""
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        request_body["policy_key"] = "bad_policy_key"

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"] == "Policy with key bad_policy_key does not exist"
        )

        privacy_preference_history_created = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.privacy_notice_history_id
                == privacy_notice.privacy_notice_history_id
            )
            .first()
        )
        assert (
            privacy_preference_history_created.preference
            == UserConsentPreference.opt_out
        )

        assert verification_code in mock_verify_identity.call_args_list[0].args
        assert privacy_preference_history_created.privacy_request_id is None
        db.refresh(consent_request)
        assert consent_request.privacy_request_id is None
        assert not mock_run_privacy_request.called

        current_privacy_preference_one = (
            privacy_preference_history_created.current_privacy_preference
        )

        assert (
            current_privacy_preference_one.preference == UserConsentPreference.opt_out
        ), "Historical preferences upserted to latest consent preferences"

        privacy_preference_history_created.delete(db)

    @pytest.mark.usefixtures("automatically_approved", "system")
    @patch("fides.api.models.privacy_request.ConsentRequest.verify_identity")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_set_privacy_preferences_without_verification_required(
        self,
        run_privacy_request_mock,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
        privacy_notice,
        request_body,
        verification_code,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 200
        assert len(response.json()["preferences"]) == 1

        response_json = response.json()["preferences"][0]
        created_privacy_preference_history_id = response_json[
            "privacy_preference_history_id"
        ]
        privacy_preference_history = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id == created_privacy_preference_history_id
            )
            .first()
        )
        assert response_json["preference"] == "opt_out"

        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )

        db.refresh(consent_request)
        assert consent_request.privacy_request_id

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        response_json = response.json()["items"][0]
        assert response_json["id"] is not None
        assert response_json["preference"] == "opt_out"
        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )

        privacy_preference_history.delete(db=db)
        assert not mock_verify_identity.called
        assert run_privacy_request_mock.called

    @pytest.mark.usefixtures(
        "subject_identity_verification_required", "automatically_approved", "system"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_verify_then_set_privacy_preferences_with_additional_fides_user_device_id(
        self,
        run_privacy_request_mock,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        db: Session,
        request_body,
        privacy_notice,
    ):
        """Verify code and then return privacy preferences

        Besides having a verified identity, we also have the fides_user_device_id from the browser
        """
        test_device_id = "2da1690a-65b6-447b-879b-d33089c04ba5"
        request_body["browser_identity"]["fides_user_device_id"] = test_device_id
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        # Assert no existing privacy preferences exist for this identity
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "pages": 0,
            "size": 50,
        }

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=request_body,
        )
        assert response.status_code == 200
        assert len(response.json()["preferences"]) == 1
        assert response.json()["fides_mobile_data"] is None

        response_json = response.json()["preferences"][0]
        created_privacy_preference_history_id = response_json[
            "privacy_preference_history_id"
        ]
        privacy_preference_history = (
            db.query(PrivacyPreferenceHistory)
            .filter(
                PrivacyPreferenceHistory.id == created_privacy_preference_history_id
            )
            .first()
        )
        assert response_json["preference"] == "opt_out"

        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )
        db.refresh(consent_request)
        assert consent_request.privacy_request_id

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        response_json = response.json()["items"][0]
        assert response_json["id"] is not None
        assert response_json["preference"] == "opt_out"
        assert (
            response_json["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(privacy_notice.histories[0]).dict()
        )
        assert privacy_preference_history.fides_user_device == test_device_id
        assert (
            privacy_preference_history.hashed_fides_user_device
            == ProvidedIdentity.hash_value(test_device_id)
        )
        assert (
            privacy_preference_history.fides_user_device_provided_identity_id
            is not None
        )
        fides_user_device_provided_identity = (
            privacy_preference_history.fides_user_device_provided_identity
        )
        assert (
            fides_user_device_provided_identity
            != privacy_preference_history.provided_identity
        )
        assert (
            fides_user_device_provided_identity.encrypted_value["value"]
            == test_device_id
        )
        assert (
            fides_user_device_provided_identity.hashed_value
            == ProvidedIdentity.hash_value(test_device_id)
        )

        privacy_preference_history.delete(db=db)
        assert run_privacy_request_mock.called


class TestPrivacyPreferenceVerify:
    @pytest.fixture(scope="function")
    def verification_code(self) -> str:
        return "abcd"

    def test_consent_verify_no_consent_request_id(
        self,
        api_client,
    ):
        data = {"code": "12345"}

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id='non_existent_consent_id')}",
            json=data,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_consent_verify_no_consent_code(
        self, provided_identity_and_consent_request, api_client
    ):
        data = {"code": "12345"}

        _, consent_request = provided_identity_and_consent_request
        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json=data,
        )
        assert response.status_code == 400
        assert "code expired" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_consent_verify_invalid_code(
        self, provided_identity_and_consent_request, api_client
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code("abcd")

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": "1234"},
        )
        assert response.status_code == 403
        assert "Incorrect identification" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @patch("fides.api.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_verify_no_email_provided(
        self,
        mock_verify_identity: MagicMock,
        db,
        api_client,
        verification_code,
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

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )

        assert response.status_code == 404
        assert verification_code in mock_verify_identity.call_args_list[0].args
        assert "missing" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @patch("fides.api.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_verify_no_privacy_preferences_present(
        self,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert verification_code in mock_verify_identity.call_args_list[0].args
        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "pages": 0,
            "size": 50,
        }

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_consent_verify_consent_preferences(
        self,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
        privacy_preference_history,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

        # Getting current preferences returns the latest CurrentPrivacyPreferences, not the PrivacyPreferenceHistory records
        current_preference_record = (
            privacy_preference_history.current_privacy_preference
        )
        data = response.json()["items"][0]
        assert data["id"] == current_preference_record.id
        assert (
            data["preference"]
            == "opt_out"
            == privacy_preference_history.preference.value
        )
        assert (
            data["privacy_notice_history"]
            == PrivacyNoticeHistorySchema.from_orm(
                privacy_preference_history.privacy_notice_history
            ).dict()
        )
        db.refresh(consent_request)
        assert consent_request.identity_verified_at is not None

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
        "privacy_preference_history_for_tcf_special_purpose",
    )
    def test_consent_verify_tcf_consent_preferences_tcf_disabled(
        self, provided_identity_and_consent_request, api_client, verification_code
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 0

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
        "enable_tcf",
    )
    def test_consent_verify_tcf_consent_preferences(
        self,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
        privacy_preference_history_for_tcf_special_purpose,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

        current_preference_record = (
            privacy_preference_history_for_tcf_special_purpose.current_privacy_preference
        )
        data = response.json()["items"][0]
        assert data["id"] == current_preference_record.id
        assert (
            data["preference"]
            == "opt_in"
            == privacy_preference_history_for_tcf_special_purpose.preference.value
        )
        assert data["special_purpose"] == 1
        db.refresh(consent_request)
        assert consent_request.identity_verified_at is not None


class TestSavePrivacyPreferencesForFidesDeviceId:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_PREFERENCES

    @pytest.fixture(scope="function")
    def request_body(
        self,
        privacy_notice,
        consent_policy,
        privacy_experience_overlay,
        served_notice_history,
    ):
        return {
            "browser_identity": {
                "ga_client_id": "test",
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "preferences": [
                {
                    "privacy_notice_history_id": privacy_notice.histories[0].id,
                    "preference": "opt_out",
                    "served_notice_history_id": served_notice_history.id,
                }
            ],
            "policy_key": consent_policy.key,
            "user_geography": "us_ca",
            "privacy_experience_id": privacy_experience_overlay.id,
            "method": "button",
        }

    @pytest.fixture(scope="function")
    def tcf_request_body(
        self,
        privacy_notice,
        consent_policy,
        privacy_experience_france_tcf_overlay,
        served_notice_history_for_tcf_purpose,
        system,
    ):
        return {
            "browser_identity": {
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "purpose_consent_preferences": [
                {
                    "id": 8,
                    "preference": "opt_out",
                    "served_notice_history_id": served_notice_history_for_tcf_purpose.id,
                }
            ],
            "vendor_consent_preferences": [
                {
                    "id": "amplitude",
                    "preference": "opt_in",
                }
            ],
            "feature_preferences": [{"id": 1, "preference": "opt_out"}],
            "special_feature_preferences": [{"id": 2, "preference": "opt_in"}],
            "system_legitimate_interests_preferences": [
                {"id": system.id, "preference": "opt_out"}
            ],
            "user_geography": "fr",
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
        }

    @pytest.mark.usefixtures(
        "privacy_notice",
    )
    def test_no_fides_user_device_id_supplied(self, api_client, url, request_body):
        del request_body["browser_identity"]["fides_user_device_id"]
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 422

    @pytest.mark.usefixtures(
        "privacy_notice",
    )
    def test_bad_fides_user_device_id_supplied(self, api_client, url, request_body):
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

    @pytest.mark.usefixtures(
        "privacy_notice",
    )
    def test_save_privacy_preferences_with_bad_notice(
        self, api_client, url, request_body
    ):
        request_body["preferences"][0]["privacy_notice_history_id"] = "bad_history"
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 400

    @pytest.mark.usefixtures(
        "privacy_notice",
    )
    def test_save_privacy_preferences_with_invalid_served_notice_history(
        self,
        api_client,
        url,
        request_body,
        served_notice_history_us_ca_provide_for_fides_user,
    ):
        request_body["preferences"][0][
            "served_notice_history_id"
        ] = served_notice_history_us_ca_provide_for_fides_user.id
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422

    @pytest.mark.usefixtures(
        "privacy_notice",
    )
    def test_save_privacy_preferences_with_served_notice_history_not_found(
        self, api_client, url, request_body
    ):
        request_body["preferences"][0][
            "served_notice_history_id"
        ] = "bad_served_notice_history_id"
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 404

    def test_save_privacy_preferences_bad_experience_id(
        self,
        api_client,
        url,
        request_body,
    ):
        """Privacy experiences need to be valid when setting preferences"""
        request_body["privacy_experience_id"] = "bad_id"
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == f"Privacy Experience 'bad_id' not found."

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_save_privacy_preferences_with_respect_to_fides_user_device_id(
        self,
        run_privacy_request_mock,
        mock_anonymize,
        db,
        api_client,
        url,
        request_body,
        privacy_notice,
        privacy_experience_overlay,
        served_notice_history,
    ):
        """Assert CurrentPrivacyPreference records were updated and PrivacyPreferenceHistory records were created
        for recordkeeping with respect to the fides user device id in the request
        """
        test_device_id = "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11"
        masked_ip = "12.214.31.0"
        mock_anonymize.return_value = masked_ip
        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        assert response.json()["fides_mobile_data"] is None
        response_json = response.json()["preferences"][0]
        assert response_json["preference"] == "opt_out"
        assert (
            response_json["privacy_notice_history"]["id"]
            == privacy_notice.histories[0].id
        )

        privacy_preference_history_id = response_json["privacy_preference_history_id"]

        # Fetch current privacy preference that was updated
        current_preference = CurrentPrivacyPreference.get(
            db, object_id=response_json["id"]
        )
        # Get corresponding historical preference that was just created
        privacy_preference_history = current_preference.privacy_preference_history
        assert privacy_preference_history.id == privacy_preference_history_id

        fides_user_device_provided_identity = (
            privacy_preference_history.fides_user_device_provided_identity
        )
        # Same fides user device identity added to both the historical and current record
        assert (
            current_preference.fides_user_device_provided_identity
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
        # Values also cached on the historical record for reporting
        assert (
            privacy_preference_history.hashed_fides_user_device
            == ProvidedIdentity.hash_value(test_device_id)
        )  # Cached here for reporting
        assert (
            privacy_preference_history.fides_user_device == test_device_id
        )  # Cached here for reporting

        # Test items that are pulled from request headers or client
        assert (
            privacy_preference_history.request_origin == RequestOrigin.overlay
        )  # Retrieved from privacy experience history
        assert (
            privacy_preference_history.user_agent == "testclient"
        )  # Retrieved from request headers
        assert (
            privacy_preference_history.privacy_experience_config_history_id
            == privacy_experience_overlay.experience_config.experience_config_history_id
        )
        assert (
            privacy_preference_history.privacy_experience_id
            == privacy_experience_overlay.id
        )
        assert privacy_preference_history.anonymized_ip_address == masked_ip
        assert privacy_preference_history.url_recorded is None
        assert privacy_preference_history.method == ConsentMethod.button
        assert (
            privacy_preference_history.served_notice_history_id
            == served_notice_history.id
        )

        # Privacy request created and queued because a privacy notice has system wide enforcement
        assert privacy_preference_history.privacy_request_id is not None
        assert run_privacy_request_mock.called

        current_preference.delete(db)
        privacy_preference_history.delete(db)

    def test_invalid_tcf_purpose_in_request_body(
        self,
        api_client,
        url,
        privacy_experience_france_tcf_overlay,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "purpose_consent_preferences": [
                {
                    "id": 1000,
                    "preference": "opt_out",
                }
            ],
            "user_geography": "fr",
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Cannot save preferences against invalid purpose id: '1000'"
        )

    def test_invalid_tcf_special_purpose_in_request_body(
        self,
        api_client,
        url,
        privacy_experience_france_tcf_overlay,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "special_purpose_preferences": [
                {
                    "id": 3,
                    "preference": "opt_out",
                }
            ],
            "user_geography": "fr",
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Cannot save preferences against invalid special purpose id: '3'"
        )

    def test_invalid_tcf_feature_in_request_body(
        self,
        api_client,
        url,
        privacy_experience_france_tcf_overlay,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "feature_preferences": [
                {
                    "id": 4,
                    "preference": "opt_out",
                }
            ],
            "user_geography": "fr",
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Cannot save preferences against invalid feature id: '4'"
        )

    def test_invalid_tcf_special_feature_in_request_body(
        self,
        api_client,
        url,
        privacy_experience_france_tcf_overlay,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "special_feature_preferences": [
                {
                    "id": 3,
                    "preference": "opt_out",
                }
            ],
            "user_geography": "fr",
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Cannot save preferences against invalid special feature id: '3'"
        )

    @pytest.mark.usefixtures(
        "enable_tcf",
    )
    def test_invalid_system_in_request_body(
        self, api_client, url, db, privacy_experience_france_tcf_overlay
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "system_consent_preferences": [
                {
                    "id": "bad_system",
                    "preference": "opt_out",
                }
            ],
            "user_geography": "fr",
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Can't save consent against invalid system id 'bad_system'."
        )

    def test_duplicate_tcf_preferences_in_request_body(
        self,
        api_client,
        url,
        privacy_experience_france_tcf_overlay,
    ):
        request_body = {
            "browser_identity": {
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "special_purpose_preferences": [
                {
                    "id": 2,
                    "preference": "opt_out",
                },
                {
                    "id": 2,
                    "preference": "opt_in",
                },
            ],
            "user_geography": "fr",
            "privacy_experience_id": privacy_experience_france_tcf_overlay.id,
        }
        response = api_client.patch(url, json=request_body)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Duplicate preferences saved against TCF component: 'special_purpose_preferences'"
        )

    @pytest.mark.usefixtures(
        "enable_tcf",
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_save_tcf_privacy_preferences(
        self,
        run_privacy_request_mock,
        mock_anonymize,
        db,
        api_client,
        url,
        tcf_request_body,
        privacy_experience_france_tcf_overlay,
        served_notice_history_for_tcf_purpose,
        experience_config_tcf_overlay,
        system,
    ):
        """Assert CurrentPrivacyPreference records were updated and PrivacyPreferenceHistory records were created
        for recordkeeping with respect to the fides user device id in the request
        """
        test_device_id = "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11"
        masked_ip = "12.214.31.0"
        mock_anonymize.return_value = masked_ip
        response = api_client.patch(
            url, json=tcf_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        assert len(response.json()["purpose_consent_preferences"]) == 1
        assert len(response.json()["preferences"]) == 0
        assert len(response.json()["purpose_legitimate_interests_preferences"]) == 0
        assert len(response.json()["special_purpose_preferences"]) == 0
        assert len(response.json()["vendor_consent_preferences"]) == 1
        assert len(response.json()["feature_preferences"]) == 1
        assert len(response.json()["special_feature_preferences"]) == 1
        assert len(response.json()["system_consent_preferences"]) == 0
        assert len(response.json()["system_legitimate_interests_preferences"]) == 1
        assert response.json()["fides_mobile_data"] is None

        purpose_response = response.json()["purpose_consent_preferences"][0]
        assert purpose_response["preference"] == "opt_out"
        assert purpose_response["purpose_consent"] == 8
        purpose_privacy_preference_history_id = purpose_response[
            "privacy_preference_history_id"
        ]
        current_purpose_preference = CurrentPrivacyPreference.get(
            db, object_id=purpose_response["id"]
        )
        # Assert details saved with respect to data use
        purpose_privacy_preference_history = (
            current_purpose_preference.privacy_preference_history
        )
        assert (
            purpose_privacy_preference_history.id
            == purpose_privacy_preference_history_id
        )
        assert purpose_privacy_preference_history.vendor_consent is None
        assert purpose_privacy_preference_history.vendor_legitimate_interests is None

        assert purpose_privacy_preference_history.privacy_notice_history_id is None
        assert purpose_privacy_preference_history.feature is None
        fides_user_device_provided_identity = (
            purpose_privacy_preference_history.fides_user_device_provided_identity
        )
        assert (
            current_purpose_preference.fides_user_device_provided_identity
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
            purpose_privacy_preference_history.hashed_fides_user_device
            == ProvidedIdentity.hash_value(test_device_id)
        )
        assert purpose_privacy_preference_history.fides_user_device == test_device_id
        assert (
            purpose_privacy_preference_history.purpose_consent
            == purpose_response["purpose_consent"]
        )
        assert purpose_privacy_preference_history.purpose_legitimate_interests is None

        assert (
            purpose_privacy_preference_history.request_origin
            == RequestOrigin.tcf_overlay
        )
        assert purpose_privacy_preference_history.user_agent == "testclient"
        assert (
            purpose_privacy_preference_history.privacy_experience_config_history_id
            == experience_config_tcf_overlay.experience_config_history_id
        )
        assert (
            purpose_privacy_preference_history.privacy_experience_id
            == privacy_experience_france_tcf_overlay.id
        )
        assert purpose_privacy_preference_history.anonymized_ip_address == masked_ip
        assert purpose_privacy_preference_history.url_recorded is None
        assert (
            purpose_privacy_preference_history.served_notice_history_id
            == served_notice_history_for_tcf_purpose.id
        )

        # Assert details saved w.r.t vendor

        vendor_consent_response = response.json()["vendor_consent_preferences"][0]
        assert vendor_consent_response["preference"] == "opt_in"
        assert vendor_consent_response["vendor_consent"] == "amplitude"

        current_vendor_preference = CurrentPrivacyPreference.get(
            db, object_id=vendor_consent_response["id"]
        )
        vendor_privacy_preference_history = (
            current_vendor_preference.privacy_preference_history
        )
        assert vendor_privacy_preference_history.purpose_consent is None
        assert vendor_privacy_preference_history.privacy_notice_history_id is None
        assert vendor_privacy_preference_history.feature is None

        fides_user_device_provided_identity = (
            vendor_privacy_preference_history.fides_user_device_provided_identity
        )
        assert (
            current_purpose_preference.fides_user_device_provided_identity
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
            vendor_privacy_preference_history.hashed_fides_user_device
            == ProvidedIdentity.hash_value(test_device_id)
        )
        assert vendor_privacy_preference_history.fides_user_device == test_device_id
        assert (
            vendor_privacy_preference_history.vendor_consent
            == vendor_consent_response["vendor_consent"]
        )

        assert (
            vendor_privacy_preference_history.request_origin
            == RequestOrigin.tcf_overlay
        )
        assert vendor_privacy_preference_history.user_agent == "testclient"
        assert (
            vendor_privacy_preference_history.privacy_experience_config_history_id
            == experience_config_tcf_overlay.experience_config_history_id
        )
        assert (
            vendor_privacy_preference_history.privacy_experience_id
            == privacy_experience_france_tcf_overlay.id
        )
        assert vendor_privacy_preference_history.anonymized_ip_address == masked_ip
        assert vendor_privacy_preference_history.url_recorded is None
        assert vendor_privacy_preference_history.served_notice_history_id is None

        # Privacy request not created for TCF
        assert purpose_privacy_preference_history.privacy_request_id is None
        assert vendor_privacy_preference_history.privacy_request_id is None
        assert not run_privacy_request_mock.called

        # Assert feature portion of the response
        feature_response = response.json()["feature_preferences"][0]
        assert feature_response["preference"] == "opt_out"
        assert feature_response["feature"] == 1
        assert feature_response["special_feature"] is None
        current_feature_preference = CurrentPrivacyPreference.get(
            db, object_id=feature_response["id"]
        )
        feature_privacy_preference_history = (
            current_feature_preference.privacy_preference_history
        )
        assert current_feature_preference.feature == 1
        assert feature_privacy_preference_history.feature == 1

        # Assert special feature portion of the response
        special_feature_response = response.json()["special_feature_preferences"][0]
        assert special_feature_response["preference"] == "opt_in"
        assert special_feature_response["special_feature"] == 2
        assert special_feature_response["feature"] is None
        current_special_feature_preference = CurrentPrivacyPreference.get(
            db, object_id=special_feature_response["id"]
        )
        special_feature_privacy_preference_history = (
            current_special_feature_preference.privacy_preference_history
        )
        assert current_special_feature_preference.special_feature == 2
        assert special_feature_privacy_preference_history.special_feature == 2

        # Assert system portion of the response
        system_response = response.json()["system_legitimate_interests_preferences"][0]
        assert system_response["preference"] == "opt_out"
        assert system_response["system_legitimate_interests"] == system.id
        current_system_preference = CurrentPrivacyPreference.get(
            db, object_id=system_response["id"]
        )
        system_privacy_preference_history = (
            current_system_preference.privacy_preference_history
        )
        assert current_system_preference.system_legitimate_interests == system.id
        assert (
            system_privacy_preference_history.system_legitimate_interests == system.id
        )

        current_system_preference.delete(db)
        system_privacy_preference_history.delete(db)
        current_special_feature_preference.delete(db)
        special_feature_privacy_preference_history.delete(db)
        current_feature_preference.delete(db)
        feature_privacy_preference_history.delete(db)
        current_purpose_preference.delete(db)
        purpose_privacy_preference_history.delete(db)
        current_vendor_preference.delete(db)
        vendor_privacy_preference_history.delete(db)

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_preference_endpoints.anonymize_ip_address"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_save_privacy_preferences_for_fides_user_device_id_no_notice_has_system_wide_enforcement(
        self,
        run_privacy_request_mock,
        mock_anonymize,
        db,
        api_client,
        url,
        consent_policy,
        privacy_notice_fr_provide_service_frontend_only,
        privacy_experience_france_overlay,
    ):
        """PrivacyPreferences and CurrentPrivacyPreferences saved for the given fides user device id
        but no privacy request created to propagate preferences, because all privacy notices
        have frontend only enforcement
        """
        masked_ip = "12.214.31.0"
        mock_anonymize.return_value = masked_ip

        request_body = {
            "browser_identity": {
                "ga_client_id": "test",
                "fides_user_device_id": "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11",
            },
            "preferences": [
                {
                    "privacy_notice_history_id": privacy_notice_fr_provide_service_frontend_only.histories[
                        0
                    ].id,
                    "preference": "opt_out",
                }
            ],
            "policy_key": consent_policy.key,
            "user_geography": "us_ca",
            "privacy_experience_id": privacy_experience_france_overlay.id,
            "method": "button",
        }

        response = api_client.patch(
            url, json=request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        response_json = response.json()["preferences"][0]
        assert response_json["preference"] == "opt_out"
        assert (
            response_json["privacy_notice_history"]["id"]
            == privacy_notice_fr_provide_service_frontend_only.histories[0].id
        )

        # Fetch current privacy preference that was updated
        current_preference = CurrentPrivacyPreference.get(
            db, object_id=response_json["id"]
        )
        # Get corresponding historical preference that was just created
        privacy_preference_history = current_preference.privacy_preference_history

        assert (
            privacy_preference_history.privacy_request_id is None
        )  # Privacy request not created
        assert not run_privacy_request_mock.called  # Privacy Request is not queued

        current_preference.delete(db)
        privacy_preference_history.delete(db)


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
        assert response_body["url_recorded"] == "example.com/privacy_center"
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
        assert response_body["tcf_version"] == CURRENT_TCF_VERSION

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


class TestSavePrivacyPreferencesTCStringOnly:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_PREFERENCES

    @pytest.mark.usefixtures("enable_tcf")
    def test_save_privacy_preferences_tc_string_section_overlaps_request_body_section(
        self, api_client, url
    ):
        tc_string: str = "CPzEX8APzEX8AAMABBENAUEEAPLAAAAAAAAAABEAAAAA.IABE"
        fides_user_device_id = "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11"

        minimal_request_body = {
            "browser_identity": {
                "fides_user_device_id": fides_user_device_id,
            },
            "fides_string": tc_string,
            "purpose_consent_preferences": [{"id": 1, "preference": "opt_out"}],
        }
        response = api_client.patch(
            url, json=minimal_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Cannot supply value for 'purpose_consent_preferences' and 'fides_string' simultaneously when saving privacy preferences."
        )

    def test_save_privacy_preferences_bad_tc_string(self, api_client, url):
        tc_string: str = "bad_string"
        fides_user_device_id = "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11"

        minimal_request_body = {
            "browser_identity": {
                "fides_user_device_id": fides_user_device_id,
            },
            "fides_string": tc_string,
        }
        response = api_client.patch(
            url, json=minimal_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid base64-encoded TC string"

    @pytest.mark.usefixtures("enable_tcf")
    def test_save_privacy_preferences_with_tc_string_when_datamap_empty(
        self, api_client, url
    ):
        tc_string: str = "CPzEX8APzEX8AAMABBENAUEEAPLAAAAAAAAAABEAAAAA.IABE"
        fides_user_device_id = "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11"

        minimal_request_body = {
            "browser_identity": {
                "fides_user_device_id": fides_user_device_id,
            },
            "fides_string": tc_string,
        }
        response = api_client.patch(
            url, json=minimal_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        response_body = response.json()["preferences"]

        # Nothing in the datamap so we didn't save anything here.
        assert len(response_body) == 0

    def test_save_privacy_preferences_when_tcf_disabled(self, api_client, url):
        tc_string: str = "CPzEX8APzEX8AAMABBENAUEEAPLAAAAAAAAAABEAAAAA.IABE"
        fides_user_device_id = "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11"

        minimal_request_body = {
            "browser_identity": {
                "fides_user_device_id": fides_user_device_id,
            },
            "fides_string": tc_string,
        }
        response = api_client.patch(
            url, json=minimal_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        response_body = response.json()["preferences"]

        # Nothing saved because TCF is disabled
        assert len(response_body) == 0

    @pytest.mark.usefixtures(
        "skimbit_system", "emerse_system", "captify_technologies_system", "enable_tcf"
    )
    def test_save_privacy_preferences_with_tc_string(self, api_client, url, db):
        tc_string: str = "CPzEX8APzEX8AAMABBENAUEEAPLAAAAAAAAAABEAAAAA.IABE"
        fides_user_device_id = "e4e573ba-d806-4e54-bdd8-3d2ff11d4f11"

        minimal_request_body = {
            "browser_identity": {
                "fides_user_device_id": fides_user_device_id,
            },
            "fides_string": tc_string,
        }
        response = api_client.patch(
            url, json=minimal_request_body, headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        response_body = response.json()

        assert len(response_body["preferences"]) == 0
        assert len(response_body["purpose_consent_preferences"]) == 7
        assert len(response_body["purpose_legitimate_interests_preferences"]) == 5
        assert len(response_body["special_purpose_preferences"]) == 0
        assert len(response_body["vendor_consent_preferences"]) == 2
        assert len(response_body["vendor_legitimate_interests_preferences"]) == 2
        assert len(response_body["feature_preferences"]) == 0
        assert len(response_body["special_feature_preferences"]) == 1
        assert len(response_body["system_consent_preferences"]) == 0
        assert len(response_body["system_legitimate_interests_preferences"]) == 0

        first_purpose_consent_record = response_body["purpose_consent_preferences"][0]
        assert first_purpose_consent_record["purpose_consent"] == 1
        assert first_purpose_consent_record["preference"] == "opt_in"
        saved_current_privacy_preference_record = db.query(
            CurrentPrivacyPreference
        ).get(first_purpose_consent_record["id"])
        assert saved_current_privacy_preference_record.purpose_consent == 1
        assert (
            saved_current_privacy_preference_record.preference
            == UserConsentPreference.opt_in
        )

        privacy_preference_history_record = db.query(PrivacyPreferenceHistory).get(
            first_purpose_consent_record["privacy_preference_history_id"]
        )
        assert (
            privacy_preference_history_record.current_privacy_preference
            == saved_current_privacy_preference_record
        )

        assert (
            privacy_preference_history_record.fides_user_device == fides_user_device_id
        )
        assert (
            privacy_preference_history_record.fides_user_device_provided_identity
            is not None
        )
        assert (
            privacy_preference_history_record.fides_user_device_provided_identity
            == saved_current_privacy_preference_record.fides_user_device_provided_identity
        )

        assert (
            privacy_preference_history_record.privacy_experience_id is None
        )  # Not required in request body
        assert (
            privacy_preference_history_record.privacy_experience_config_history_id
            is None
        )

        # There were no purpose legitimate interests in the string, but purpose 2 was disclosed
        # to the user in the experience.  We opt out here.
        first_purpose_li_record = response_body[
            "purpose_legitimate_interests_preferences"
        ][0]
        assert first_purpose_li_record["purpose_legitimate_interests"] == 2
        assert first_purpose_li_record["preference"] == "opt_out"
        saved_current_privacy_preference_record = db.query(
            CurrentPrivacyPreference
        ).get(first_purpose_li_record["id"])
        assert saved_current_privacy_preference_record.purpose_legitimate_interests == 2
        assert (
            saved_current_privacy_preference_record.preference
            == UserConsentPreference.opt_out
        )

        # Vendor 2 was in the vendor consents section
        first_vendor_consent_record = response_body["vendor_consent_preferences"][0]
        assert first_vendor_consent_record["vendor_consent"] == "gvl.2"
        assert first_vendor_consent_record["preference"] == "opt_in"
        saved_current_privacy_preference_record = db.query(
            CurrentPrivacyPreference
        ).get(first_vendor_consent_record["id"])
        assert saved_current_privacy_preference_record.vendor_consent == "gvl.2"
        assert (
            saved_current_privacy_preference_record.preference
            == UserConsentPreference.opt_in
        )

        # Vendor 8 was not opted in in the vendor consents section, but was disclosed to the
        # customer in the vendor consents section, so we opt out.
        second_vendor_consent_record = response_body["vendor_consent_preferences"][1]
        assert second_vendor_consent_record["vendor_consent"] == "gvl.8"
        assert second_vendor_consent_record["preference"] == "opt_out"
        saved_current_privacy_preference_record = db.query(
            CurrentPrivacyPreference
        ).get(second_vendor_consent_record["id"])
        assert saved_current_privacy_preference_record.vendor_consent == "gvl.8"
        assert (
            saved_current_privacy_preference_record.preference
            == UserConsentPreference.opt_out
        )

        special_feature_record = response_body["special_feature_preferences"][0]
        assert special_feature_record["special_feature"] == 2
        assert special_feature_record["preference"] == "opt_in"
        saved_current_privacy_preference_record = db.query(
            CurrentPrivacyPreference
        ).get(special_feature_record["id"])
        assert saved_current_privacy_preference_record.special_feature == 2
        assert (
            saved_current_privacy_preference_record.preference
            == UserConsentPreference.opt_in
        )

        mobile_data = response.json()["fides_mobile_data"]
        assert mobile_data == {
            "IABTCF_CmpSdkID": 12,
            "IABTCF_CmpSdkVersion": 1,
            "IABTCF_PolicyVersion": 4,
            "IABTCF_gdprApplies": 1,
            "IABTCF_PublisherCC": "AA",
            "IABTCF_PurposeOneTreatment": 0,
            "IABTCF_UseNonStandardTexts": 0,
            "IABTCF_TCString": "CPzEX8APzEX8AAMABBENAUEEAPLAAAAAAAAAABEAAAAA.IABE",
            "IABTCF_VendorConsents": "01",
            "IABTCF_VendorLegitimateInterests": "",
            "IABTCF_PurposeConsents": "111100101100000000000000",
            "IABTCF_PurposeLegitimateInterests": "000000000000000000000000",
            "IABTCF_SpecialFeaturesOptIns": "010000000000",
            "IABTCF_PublisherConsent": None,
            "IABTCF_PublisherLegitimateInterests": None,
            "IABTCF_PublisherCustomPurposesConsents": None,
            "IABTCF_PublisherCustomPurposesLegitimateInterests": None,
            "IABTCF_AddtlConsent": None,
        }
