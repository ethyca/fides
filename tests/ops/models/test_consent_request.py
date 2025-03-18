from unittest import mock
from unittest.mock import MagicMock

import pytest

from fides.api.api.v1.endpoints.consent_request_endpoints import (
    queue_privacy_request_to_propagate_consent_old_workflow,
)
from fides.api.db.seed import DEFAULT_CONSENT_POLICY
from fides.api.graph.config import CollectionAddress
from fides.api.models.privacy_request import Consent, ConsentRequest, ProvidedIdentity
from fides.api.schemas.policy import PolicyResponse
from fides.api.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    ConsentPreferences,
    ConsentWithExecutableStatus,
    PrivacyRequestResponse,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import CustomPrivacyRequestField, Identity

paused_location = CollectionAddress("test_dataset", "test_collection")


def test_consent(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "encrypted_value": {"value": "test@email.com"},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    consent_data_1 = {
        "provided_identity_id": provided_identity.id,
        "data_use": "user.biometric_health",
        "opt_in": True,
    }
    consent_1 = Consent.create(db, data=consent_data_1)

    consent_data_2 = {
        "provided_identity_id": provided_identity.id,
        "data_use": "user.behavior.browsing_history",
        "opt_in": False,
    }
    consent_2 = Consent.create(db, data=consent_data_2)
    data_uses = [x.data_use for x in provided_identity.consent]

    assert consent_data_1["data_use"] in data_uses
    assert consent_data_2["data_use"] in data_uses

    provided_identity.delete(db)

    assert Consent.get(db, object_id=consent_1.id) is None
    assert Consent.get(db, object_id=consent_2.id) is None


def test_consent_with_gpc(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "encrypted_value": {"value": "test@email.com"},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    consent_data_1 = {
        "provided_identity_id": provided_identity.id,
        "data_use": "user.biometric_health",
        "opt_in": True,
        "has_gpc_flag": True,
        "conflicts_with_gpc": True,
    }
    consent_1 = Consent.create(db, data=consent_data_1)

    consent_data_2 = {
        "provided_identity_id": provided_identity.id,
        "data_use": "user.behavior.browsing_history",
        "opt_in": False,
    }
    consent_2 = Consent.create(db, data=consent_data_2)
    data_uses = [x.data_use for x in provided_identity.consent]

    assert consent_data_1["data_use"] in data_uses
    assert consent_data_2["data_use"] in data_uses

    provided_identity.delete(db)

    assert Consent.get(db, object_id=consent_1.id) is None
    assert Consent.get(db, object_id=consent_2.id) is None


def test_consent_request(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "encrypted_value": {"value": "test@email.com"},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    consent_request_1 = {
        "provided_identity_id": provided_identity.id,
    }
    consent_1 = ConsentRequest.create(db, data=consent_request_1)

    consent_request_2 = {
        "provided_identity_id": provided_identity.id,
    }
    consent_2 = ConsentRequest.create(db, data=consent_request_2)

    assert consent_1.provided_identity_id in provided_identity.id
    assert consent_2.provided_identity_id in provided_identity.id

    provided_identity.delete(db)

    assert Consent.get(db, object_id=consent_1.id) is None
    assert Consent.get(db, object_id=consent_2.id) is None


class TestQueuePrivacyRequestToPropagateConsentHelper:

    @pytest.mark.usefixtures("allow_custom_privacy_request_field_collection_enabled")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service.PrivacyRequestService.create_bulk_privacy_requests"
    )
    def test_queue_privacy_request_to_propagate_consent(
        self, mock_create_privacy_request, db, consent_policy
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        consent_request = ConsentRequest.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
            },
        )

        custom_fields = {
            "first_name": CustomPrivacyRequestField(label="First name", value="John")
        }
        consent_request.persist_custom_privacy_request_fields(
            db=db, custom_privacy_request_fields=custom_fields
        )

        mock_create_privacy_request.return_value = BulkPostPrivacyRequests(
            succeeded=[
                PrivacyRequestResponse(
                    id="fake_privacy_request_id",
                    status=PrivacyRequestStatus.pending,
                    policy=PolicyResponse.model_validate(consent_policy),
                )
            ],
            failed=[],
        )

        consent_preferences = ConsentPreferences(
            consent=[{"data_use": "marketing.advertising", "opt_in": False}]
        )
        executable_consents = [
            ConsentWithExecutableStatus(
                data_use="marketing.advertising", executable=True
            )
        ]

        queue_privacy_request_to_propagate_consent_old_workflow(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            consent_request=consent_request,
            executable_consents=executable_consents,
        )
        assert mock_create_privacy_request.called

        call_args = mock_create_privacy_request.call_args[0][0]
        call_kwargs = mock_create_privacy_request.call_args[1]

        request_data = call_args[0]
        assert request_data.identity.email == "test@email.com"
        assert len(request_data.consent_preferences) == 1
        assert request_data.consent_preferences[0].data_use == "marketing.advertising"
        assert request_data.consent_preferences[0].opt_in is False

        assert (
            call_kwargs["authenticated"] is True
        ), "We already validated identity with a verification code earlier in the request"

        custom_fields = request_data.custom_privacy_request_fields
        if custom_fields:
            for label, value in custom_fields.items():
                custom_fields[label] = value.model_dump(mode="json")

        assert custom_fields == {"first_name": {"label": "First name", "value": "John"}}

        provided_identity.delete(db)

    @mock.patch(
        "fides.service.privacy_request.privacy_request_service.PrivacyRequestService.create_bulk_privacy_requests"
    )
    def test_do_not_queue_privacy_request_if_no_executable_preferences(
        self, mock_create_privacy_request, db, consent_policy
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        consent_request = ConsentRequest.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
            },
        )
        custom_fields = {
            "first_name": CustomPrivacyRequestField(label="First name", value="John")
        }
        consent_request.persist_custom_privacy_request_fields(
            db=db, custom_privacy_request_fields=custom_fields
        )
        consent_preferences = ConsentPreferences(
            consent=[{"data_use": "marketing.advertising", "opt_in": False}]
        )

        queue_privacy_request_to_propagate_consent_old_workflow(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            consent_request=consent_request,
            executable_consents=[
                ConsentWithExecutableStatus(
                    data_use="marketing.advertising", executable=False
                )
            ],
        )

        assert not mock_create_privacy_request.called

    @pytest.mark.usefixtures("allow_custom_privacy_request_field_collection_enabled")
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service.PrivacyRequestService.create_bulk_privacy_requests"
    )
    def test_merge_in_browser_identity_with_provided_identity(
        self, mock_create_privacy_request, db, consent_policy
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        consent_request = ConsentRequest.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
            },
        )
        custom_fields = {
            "first_name": CustomPrivacyRequestField(label="First name", value="John")
        }
        consent_request.persist_custom_privacy_request_fields(
            db=db, custom_privacy_request_fields=custom_fields
        )
        mock_create_privacy_request.return_value = BulkPostPrivacyRequests(
            succeeded=[
                PrivacyRequestResponse(
                    id="fake_privacy_request_id",
                    status=PrivacyRequestStatus.pending,
                    policy=PolicyResponse.model_validate(consent_policy),
                )
            ],
            failed=[],
        )
        browser_identity = Identity(ga_client_id="user_id_from_browser")

        consent_preferences = ConsentPreferences(
            consent=[{"data_use": "marketing.advertising", "opt_in": False}]
        )

        queue_privacy_request_to_propagate_consent_old_workflow(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            consent_request=consent_request,
            executable_consents=[
                ConsentWithExecutableStatus(
                    data_use="marketing.advertising", executable=True
                )
            ],
            browser_identity=browser_identity,
        )

        assert mock_create_privacy_request.called

        request_data = mock_create_privacy_request.call_args[0][0]
        request = request_data[0]

        identity_of_privacy_request = request.identity
        assert identity_of_privacy_request.email == "test@email.com"
        assert identity_of_privacy_request.ga_client_id == browser_identity.ga_client_id

        custom_fields = request.custom_privacy_request_fields
        if custom_fields:
            for label, value in custom_fields.items():
                custom_fields[label] = value.model_dump(mode="json")

        assert custom_fields == {"first_name": {"label": "First name", "value": "John"}}

        provided_identity.delete(db)
