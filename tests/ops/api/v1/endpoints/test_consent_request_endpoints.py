from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from requests import Session

from fides.api.ops.api.v1.scope_registry import CONNECTION_READ, CONSENT_READ
from fides.api.ops.api.v1.urn_registry import (
    CONSENT_REQUEST,
    CONSENT_REQUEST_PREFERENCES,
    CONSENT_REQUEST_PREFERENCES_WITH_ID,
    CONSENT_REQUEST_VERIFY,
    V1_URL_PREFIX,
)
from fides.api.ops.models.application_config import ApplicationConfig
from fides.api.ops.models.privacy_request import (
    Consent,
    ConsentRequest,
    PrivacyRequestStatus,
    ProvidedIdentity,
)
from fides.api.ops.schemas.messaging.messaging import MessagingServiceType
from fides.core.config import CONFIG


@pytest.fixture(scope="function")
def provided_identity_and_consent_request(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "hashed_value": ProvidedIdentity.hash_value("test@email.com"),
        "encrypted_value": {"value": "test@email.com"},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    consent_request_data = {
        "provided_identity_id": provided_identity.id,
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    yield provided_identity, consent_request
    provided_identity.delete(db=db)
    consent_request.delete(db=db)


@pytest.fixture
def disable_redis():
    current = CONFIG.redis.enabled
    CONFIG.redis.enabled = False
    yield
    CONFIG.redis.enabled = current


class TestConsentRequest:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return f"{V1_URL_PREFIX}{CONSENT_REQUEST}"

    @pytest.fixture(scope="function")
    def set_notification_service_type_to_none(self, db):
        """Overrides autouse fixture to remove default notification service type"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = None
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture(scope="function")
    def set_notification_service_type_to_twilio_sms(self, db):
        """Overrides autouse fixture to set notification service type to twilio sms"""
        original_value = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = (
            MessagingServiceType.TWILIO_TEXT.value
        )
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.notification_service_type = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.usefixtures(
        "messaging_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.service._verification.dispatch_message")
    def test_consent_request(self, mock_dispatch_message, api_client, url):
        data = {"email": "test@example.com"}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert mock_dispatch_message.called

    @pytest.mark.usefixtures(
        "messaging_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.service._verification.dispatch_message")
    def test_consent_request_identity_present(
        self,
        mock_dispatch_message,
        provided_identity_and_consent_request,
        api_client,
        url,
    ):
        provided_identity, _ = provided_identity_and_consent_request
        data = {"email": provided_identity.encrypted_value["value"]}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert mock_dispatch_message.called

    @pytest.mark.usefixtures(
        "messaging_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
        "disable_redis",
    )
    def test_consent_request_redis_disabled(self, api_client, url):
        data = {"email": "test@example.com"}
        response = api_client.post(url, json=data)
        assert response.status_code == 500
        assert "redis cache required" in response.json()["message"]

    @pytest.mark.usefixtures(
        "messaging_config",
        "email_connection_config",
        "email_dataset_config",
    )
    @patch("fides.api.ops.service._verification.dispatch_message")
    def test_consent_request_subject_verification_disabled_no_email(
        self, mock_dispatch_message, api_client, url
    ):
        data = {"email": "test@example.com"}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert not mock_dispatch_message.called

    @pytest.mark.usefixtures(
        "messaging_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.service._verification.dispatch_message")
    def test_consent_request_phone_number(self, mock_dispatch_message, api_client, url):
        data = {"phone_number": "+3368675309"}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert mock_dispatch_message.called

    @pytest.mark.usefixtures(
        "messaging_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.service._verification.dispatch_message")
    def test_consent_request_email_and_phone_use_config(
        self,
        mock_dispatch_message,
        set_notification_service_type_to_twilio_sms,
        api_client,
        db,
        url,
    ):
        data = {"email": "test@example.com", "phone_number": "+235624563"}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert mock_dispatch_message.called
        provided_identity = ProvidedIdentity.filter(
            db=db,
            conditions=(
                ProvidedIdentity.hashed_value
                == ProvidedIdentity.hash_value("+235624563")
            ),
        ).first()
        assert provided_identity

    @pytest.mark.usefixtures(
        "messaging_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.service._verification.dispatch_message")
    def test_consent_request_email_and_phone_default_to_email(
        self,
        mock_dispatch_message,
        set_notification_service_type_to_none,
        api_client,
        db,
        url,
    ):
        data = {"email": "testing_123@example.com", "phone_number": "+3368675309"}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert mock_dispatch_message.called
        provided_identity = ProvidedIdentity.filter(
            db=db,
            conditions=(
                ProvidedIdentity.hashed_value
                == ProvidedIdentity.hash_value("testing_123@example.com")
            ),
        ).first()
        assert provided_identity is not None


class TestConsentVerify:
    @pytest.fixture(scope="function")
    def verification_code(self) -> str:
        return "abcd"

    def test_consent_verify_no_consent_request_id(
        self,
        api_client,
    ):
        data = {"code": "12345"}

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id='non_existent_consent_id')}",
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
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id=consent_request.id)}",
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
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": "1234"},
        )
        assert response.status_code == 403
        assert "Incorrect identification" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_verify_no_email_provided(
        self, mock_verify_identity: MagicMock, db, api_client, verification_code
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
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )

        assert response.status_code == 404
        mock_verify_identity.assert_called_with(verification_code)
        assert "missing" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_verify_no_consent_present(
        self,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        mock_verify_identity.assert_called_with(verification_code)
        assert response.json()["consent"] is None

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_verify_consent_preferences(
        self,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
            },
        ]

        for data in deepcopy(consent_data):
            data["provided_identity_id"] = provided_identity.id
            Consent.create(db, data=data)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        mock_verify_identity.assert_called_with(verification_code)
        expected_consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
                "has_gpc_flag": False,
                "conflicts_with_gpc": False,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
                "has_gpc_flag": False,
                "conflicts_with_gpc": False,
            },
        ]
        assert response.json()["consent"] == expected_consent_data


class TestGetConsentUnverified:
    def test_consent_unverified_no_consent_request_id(self, api_client):
        data = {"code": "12345"}

        response = api_client.get(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id='non_existent_consent_id')}",
            json=data,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_consent_unverified_verification_error(self, api_client):
        data = {"code": "12345"}

        response = api_client.get(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id='non_existent_consent_id')}",
            json=data,
        )
        assert response.status_code == 400
        assert "turned off" in response.json()["detail"]

    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_unverified_no_email_provided(
        self, mock_verify_identity: MagicMock, db, api_client
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

        response = api_client.get(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
        )

        assert response.status_code == 404
        assert not mock_verify_identity.called
        assert "missing" in response.json()["detail"]

    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_unverified_no_consent_present(
        self,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        api_client,
    ):
        _, consent_request = provided_identity_and_consent_request

        response = api_client.get(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}"
        )
        assert response.status_code == 200
        assert not mock_verify_identity.called
        assert response.json()["consent"] is None

    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_consent_unverified_consent_preferences(
        self,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request

        consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
            },
        ]

        for data in deepcopy(consent_data):
            data["provided_identity_id"] = provided_identity.id
            Consent.create(db, data=data)

        response = api_client.get(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}"
        )
        assert response.status_code == 200
        assert not mock_verify_identity.called
        expected_consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
                "has_gpc_flag": False,
                "conflicts_with_gpc": False,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
                "has_gpc_flag": False,
                "conflicts_with_gpc": False,
            },
        ]
        assert response.json()["consent"] == expected_consent_data


class TestSaveConsent:
    @pytest.fixture(scope="function")
    def verification_code(self) -> str:
        return "abcd"

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_consent_preferences_no_consent_request_id(self, api_client):
        data = {
            "code": "12345",
            "identity": {"email": "test@email.com"},
            "consent": [{"data_use": "email", "opt_in": True}],
        }

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id='non_existent_consent_id')}",
            json=data,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_consent_preferences_no_consent_code(
        self, provided_identity_and_consent_request, api_client
    ):
        _, consent_request = provided_identity_and_consent_request

        data = {
            "code": "12345",
            "identity": {"email": "test@email.com"},
            "consent": [{"data_use": "email", "opt_in": True}],
        }

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )
        assert response.status_code == 400
        assert "code expired" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_consent_preferences_invalid_code(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        data = {
            "code": "12345",
            "identity": {"email": "test@email.com"},
            "consent": [{"data_use": "email", "opt_in": True}],
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )
        assert response.status_code == 403
        assert "Incorrect identification" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_verify_then_set_consent_preferences(
        self,
        run_privacy_request_mock,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
        db: Session,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        # Assert no existing consent preferences exist for this identity
        assert response.json() == {"consent": None}

        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json={
                "code": verification_code,
                "identity": {"email": "test@email.com"},
                "consent": [{"data_use": "email", "opt_in": True}],
            },
        )
        assert response.status_code == 200
        assert response.json()["consent"][0]["data_use"] == "email"
        assert response.json()["consent"][0]["opt_in"] is True
        assert not run_privacy_request_mock.called, "date_use: email is not executable"

        db.refresh(consent_request)
        assert (
            not consent_request.privacy_request_id
        ), "No PrivacyRequest queued because none of the consent options are executable"

        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_VERIFY.format(consent_request_id=consent_request.id)}",
            json={"code": verification_code},
        )
        assert response.status_code == 200
        # Assert the code verification endpoint also returns existing consent preferences
        assert response.json()["consent"][0]["data_use"] == "email"
        assert response.json()["consent"][0]["opt_in"] is True
        assert response.json()["consent"][0]["has_gpc_flag"] is False
        assert response.json()["consent"][0]["conflicts_with_gpc"] is False

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_consent_preferences_invalid_code_respects_attempt_count(
        self,
        provided_identity_and_consent_request,
        api_client,
        verification_code,
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        data = {
            "code": "12345",
            "identity": {"email": "test@email.com"},
            "consent": [{"data_use": "email", "opt_in": True}],
        }
        for _ in range(0, CONFIG.security.identity_verification_attempt_limit):
            response = api_client.patch(
                f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
                json=data,
            )
            assert response.status_code == 403
            assert "Incorrect identification" in response.json()["detail"]

        assert (
            consent_request._get_cached_verification_code_attempt_count()
            == CONFIG.security.identity_verification_attempt_limit
        )

        data["code"] = verification_code
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
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
    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_set_consent_preferences_no_email_provided(
        self, mock_verify_identity: MagicMock, db, api_client, verification_code
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

        data = {
            "code": verification_code,
            "identity": {"email": "test@email.com"},
            "consent": [{"data_use": "email", "opt_in": True}],
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )

        assert response.status_code == 404
        assert mock_verify_identity.called
        assert "missing" in response.json()["detail"]

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    def test_set_consent_preferences_no_consent_present(
        self, provided_identity_and_consent_request, api_client, verification_code
    ):
        _, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        data = {
            "code": verification_code,
            "identity": {"email": "test@email.com"},
            "consent": None,
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )
        assert response.status_code == 422

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_set_consent_consent_preferences(
        self,
        mock_run_privacy_request: MagicMock,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
        consent_policy,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        consent_data: list[dict[str, Any]] = [
            {
                "data_use": "advertising",
                "data_use_description": None,
                "opt_in": True,
                "has_gpc_flag": True,
                "conflicts_with_gpc": False,
            },
            {
                "data_use": "improve",
                "data_use_description": None,
                "opt_in": True,
            },
        ]

        for data in deepcopy(consent_data):
            data["provided_identity_id"] = provided_identity.id
            Consent.create(db, data=data)

        consent_data[1]["opt_in"] = False

        data = {
            "code": verification_code,
            "identity": {"email": "test@email.com"},
            "consent": consent_data,
            "policy_key": consent_policy.key,  # Optional policy_key supplied,
            "executable_options": [
                {"data_use": "advertising", "executable": True},
                {"data_use": "improve", "executable": False},
            ],
            "browser_identity": {"ga_client_id": "test_ga_client_id"},
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )

        assert response.status_code == 200
        expected_consent_data: list[dict[str, Any]] = [
            {
                "data_use": "advertising",
                "data_use_description": None,
                "opt_in": True,
                "has_gpc_flag": True,
                "conflicts_with_gpc": False,
            },
            {
                "data_use": "improve",
                "data_use_description": None,
                "opt_in": False,
                "has_gpc_flag": False,
                "conflicts_with_gpc": False,
            },
        ]
        assert response.json()["consent"] == expected_consent_data
        mock_verify_identity.assert_called_with(verification_code)

        db.refresh(consent_request)
        assert (
            consent_request.privacy_request_id is not None
        ), "PrivacyRequest queued to propagate consent preferences cached on ConsentRequest"

        identity = consent_request.privacy_request.get_persisted_identity()
        assert identity.email == "test@email.com", (
            "Identity pulled from Consent Provided Identity and used to "
            "create a Privacy Request provided identity "
        )
        assert identity.phone_number is None
        assert identity.ga_client_id == "test_ga_client_id", (
            "Browser identity pulled from Consent Provided Identity and persisted "
            "to a Privacy Request provided identity"
        )
        assert consent_request.privacy_request.consent_preferences == [
            {
                "conflicts_with_gpc": False,
                "opt_in": True,
                "data_use": "advertising",
                "has_gpc_flag": True,
                "data_use_description": None,
            },
        ], "Only executable consent preferences stored"

        assert mock_run_privacy_request.called

    @pytest.mark.usefixtures(
        "subject_identity_verification_required", "require_manual_request_approval"
    )
    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    @mock.patch(
        "fides.api.ops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_set_consent_preferences_privacy_request_pending_when_id_verification_required(
        self,
        mock_run_privacy_request: MagicMock,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
        verification_code,
        consent_policy,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request
        consent_request.cache_identity_verification_code(verification_code)

        consent_data: list[dict[str, Any]] = [
            {
                "data_use": "advertising",
                "data_use_description": None,
                "opt_in": True,
                "has_gpc_flag": True,
                "conflicts_with_gpc": False,
            }
        ]

        for data in deepcopy(consent_data):
            data["provided_identity_id"] = provided_identity.id
            Consent.create(db, data=data)

        data = {
            "code": verification_code,
            "identity": {"email": "test@email.com"},
            "consent": consent_data,
            "policy_key": consent_policy.key,  # Optional policy_key supplied,
            "executable_options": [
                {"data_use": "advertising", "executable": True},
                {"data_use": "improve", "executable": False},
            ],
            "browser_identity": {"ga_client_id": "test_ga_client_id"},
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )

        assert response.status_code == 200

        mock_verify_identity.assert_called_with(verification_code)
        db.refresh(consent_request)
        assert consent_request.privacy_request.status == PrivacyRequestStatus.pending
        assert not mock_run_privacy_request.called

    @patch("fides.api.ops.models.privacy_request.ConsentRequest.verify_identity")
    def test_set_consent_consent_preferences_without_verification(
        self,
        mock_verify_identity: MagicMock,
        provided_identity_and_consent_request,
        db,
        api_client,
    ):
        provided_identity, consent_request = provided_identity_and_consent_request

        consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
            },
        ]

        for data in deepcopy(consent_data):
            data["provided_identity_id"] = provided_identity.id
            Consent.create(db, data=data)

        consent_data[1]["opt_in"] = False

        data = {
            "identity": {"email": "test@email.com"},
            "consent": consent_data,
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )
        assert response.status_code == 200
        expected_consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
                "conflicts_with_gpc": False,
                "has_gpc_flag": False,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
                "conflicts_with_gpc": False,
                "has_gpc_flag": False,
            },
        ]
        assert response.json()["consent"] == expected_consent_data
        assert not mock_verify_identity.called


class TestGetConsentPreferences:
    def test_get_consent_preferences_wrong_scope(
        self, generate_auth_header, api_client
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES}",
            headers=auth_header,
            json={"email": "test@user.com"},
        )

        assert response.status_code == 403

    def test_get_consent_preferences_no_identity_data(
        self, generate_auth_header, api_client
    ):
        auth_header = generate_auth_header(scopes=[CONSENT_READ])
        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES}",
            headers=auth_header,
            json={"email": None},
        )

        assert response.status_code == 400
        assert "No identity information" in response.json()["detail"]

    def test_get_consent_preferences_identity_not_found(
        self, generate_auth_header, api_client
    ):
        auth_header = generate_auth_header(scopes=[CONSENT_READ])
        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES}",
            headers=auth_header,
            json={"email": "test@email.com"},
        )

        assert response.status_code == 404
        assert "Identity not found" in response.json()["detail"]

    def test_get_consent_preferences(
        self,
        provided_identity_and_consent_request,
        db,
        generate_auth_header,
        api_client,
    ):
        provided_identity, _ = provided_identity_and_consent_request

        consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
            },
        ]

        for data in deepcopy(consent_data):
            data["provided_identity_id"] = provided_identity.id
            Consent.create(db, data=data)

        auth_header = generate_auth_header(scopes=[CONSENT_READ])
        response = api_client.post(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES}",
            headers=auth_header,
            json={"email": provided_identity.encrypted_value["value"]},
        )

        assert response.status_code == 200
        expected_consent_data: list[dict[str, Any]] = [
            {
                "data_use": "email",
                "data_use_description": None,
                "opt_in": True,
                "conflicts_with_gpc": False,
                "has_gpc_flag": False,
            },
            {
                "data_use": "location",
                "data_use_description": "Location data",
                "opt_in": False,
                "conflicts_with_gpc": False,
                "has_gpc_flag": False,
            },
        ]
        assert response.json()["consent"] == expected_consent_data
