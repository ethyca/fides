from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fides.api.ops.api.v1.scope_registry import CONNECTION_READ, CONSENT_READ
from fides.api.ops.api.v1.urn_registry import (
    CONSENT_REQUEST,
    CONSENT_REQUEST_PREFERENCES,
    CONSENT_REQUEST_PREFERENCES_WITH_ID,
    CONSENT_REQUEST_VERIFY,
    V1_URL_PREFIX,
)
from fides.api.ops.models.privacy_request import (
    Consent,
    ConsentRequest,
    ProvidedIdentity,
)
from fides.ctl.core.config import get_config

CONFIG = get_config()


@pytest.fixture
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

    @pytest.mark.usefixtures(
        "email_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.service._verification.dispatch_email")
    def test_consent_request(self, mock_dispatch_email, api_client, url):
        data = {"email": "test@example.com"}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert mock_dispatch_email.called

    @pytest.mark.usefixtures(
        "email_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    @patch("fides.api.ops.service._verification.dispatch_email")
    def test_consent_request_identity_present(
        self,
        mock_dispatch_email,
        provided_identity_and_consent_request,
        api_client,
        url,
    ):
        provided_identity, _ = provided_identity_and_consent_request
        data = {"email": provided_identity.encrypted_value["value"]}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert mock_dispatch_email.called

    @pytest.mark.usefixtures(
        "email_config",
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
        "email_config",
        "email_connection_config",
        "email_dataset_config",
    )
    @patch("fides.api.ops.service._verification.dispatch_email")
    def test_consent_request_subject_verification_disabled_no_email(
        self, mock_dispatch_email, api_client, url
    ):
        data = {"email": "test@example.com"}
        response = api_client.post(url, json=data)
        assert response.status_code == 200
        assert not mock_dispatch_email.called

    @pytest.mark.usefixtures(
        "email_config",
        "email_connection_config",
        "email_dataset_config",
        "subject_identity_verification_required",
    )
    def test_consent_request_no_email(self, api_client, url):
        data = {"phone_number": "336-867-5309"}
        response = api_client.post(url, json=data)
        assert response.status_code == 400
        assert "email address is required" in response.json()["detail"]


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
        assert "missing email" in response.json()["detail"]

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
        assert response.json()["consent"] == consent_data


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
        assert "missing email" in response.json()["detail"]

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
        assert response.json()["consent"] == consent_data


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
        self, provided_identity_and_consent_request, api_client, verification_code
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
        assert "missing email" in response.json()["detail"]

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
    def test_set_consent_consent_preferences(
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

        consent_data[1]["opt_in"] = False

        data = {
            "code": verification_code,
            "identity": {"email": "test@email.com"},
            "consent": consent_data,
        }
        response = api_client.patch(
            f"{V1_URL_PREFIX}{CONSENT_REQUEST_PREFERENCES_WITH_ID.format(consent_request_id=consent_request.id)}",
            json=data,
        )

        assert response.status_code == 200
        assert response.json()["consent"] == consent_data
        mock_verify_identity.assert_called_with(verification_code)

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
        assert response.json()["consent"] == consent_data
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
        assert response.json()["consent"] == consent_data
