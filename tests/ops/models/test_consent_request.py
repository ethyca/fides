from unittest import mock

from fides.api.ctl.database.seed import DEFAULT_CONSENT_POLICY
from fides.api.api.v1.endpoints.consent_request_endpoints import (
    queue_privacy_request_to_propagate_consent_old_workflow,
)
from fides.api.graph.config import CollectionAddress
from fides.api.models.privacy_request import (
    Consent,
    ConsentRequest,
    PrivacyRequestStatus,
    ProvidedIdentity,
)
from fides.api.schemas.policy import PolicyResponse
from fides.api.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    ConsentPreferences,
    ConsentWithExecutableStatus,
    PrivacyRequestResponse,
)
from fides.api.schemas.redis_cache import Identity

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
        "data_use": "user.browsing_history",
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
        "data_use": "user.browsing_history",
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
    @mock.patch(
        "fides.api.api.v1.endpoints.consent_request_endpoints.create_privacy_request_func"
    )
    def test_queue_privacy_request_to_propagate_consent(
        self, mock_create_privacy_request, db, consent_policy
    ):
        mock_create_privacy_request.return_value = BulkPostPrivacyRequests(
            succeeded=[
                PrivacyRequestResponse(
                    id="fake_privacy_request_id",
                    status=PrivacyRequestStatus.pending,
                    policy=PolicyResponse.from_orm(consent_policy),
                )
            ],
            failed=[],
        )
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        consent_preferences = ConsentPreferences(
            consent=[{"data_use": "advertising", "opt_in": False}]
        )
        executable_consents = [
            ConsentWithExecutableStatus(data_use="advertising", executable=True)
        ]

        queue_privacy_request_to_propagate_consent_old_workflow(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            executable_consents=executable_consents,
        )
        assert mock_create_privacy_request.called

        call_kwargs = mock_create_privacy_request.call_args[1]
        assert call_kwargs["db"] == db
        assert call_kwargs["data"][0].identity.email == "test@email.com"
        assert len(call_kwargs["data"][0].consent_preferences) == 1
        assert call_kwargs["data"][0].consent_preferences[0].data_use == "advertising"
        assert call_kwargs["data"][0].consent_preferences[0].opt_in is False
        assert (
            call_kwargs["authenticated"] is True
        ), "We already validated identity with a verification code earlier in the request"

        provided_identity.delete(db)

    @mock.patch(
        "fides.api.api.v1.endpoints.consent_request_endpoints.create_privacy_request_func"
    )
    def test_do_not_queue_privacy_request_if_no_executable_preferences(
        self, mock_create_privacy_request, db, consent_policy
    ):
        mock_create_privacy_request.return_value = BulkPostPrivacyRequests(
            succeeded=[
                PrivacyRequestResponse(
                    id="fake_privacy_request_id",
                    status=PrivacyRequestStatus.pending,
                    policy=PolicyResponse.from_orm(consent_policy),
                )
            ],
            failed=[],
        )
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        consent_preferences = ConsentPreferences(
            consent=[{"data_use": "advertising", "opt_in": False}]
        )

        queue_privacy_request_to_propagate_consent_old_workflow(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            executable_consents=[
                ConsentWithExecutableStatus(data_use="advertising", executable=False)
            ],
        )

        assert not mock_create_privacy_request.called

    @mock.patch(
        "fides.api.api.v1.endpoints.consent_request_endpoints.create_privacy_request_func"
    )
    def test_merge_in_browser_identity_with_provided_identity(
        self, mock_create_privacy_request, db, consent_policy
    ):
        mock_create_privacy_request.return_value = BulkPostPrivacyRequests(
            succeeded=[
                PrivacyRequestResponse(
                    id="fake_privacy_request_id",
                    status=PrivacyRequestStatus.pending,
                    policy=PolicyResponse.from_orm(consent_policy),
                )
            ],
            failed=[],
        )
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        browser_identity = Identity(ga_client_id="user_id_from_browser")

        consent_preferences = ConsentPreferences(
            consent=[{"data_use": "advertising", "opt_in": False}]
        )

        queue_privacy_request_to_propagate_consent_old_workflow(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            executable_consents=[
                ConsentWithExecutableStatus(data_use="advertising", executable=True)
            ],
            browser_identity=browser_identity,
        )

        assert mock_create_privacy_request.called
        call_kwargs = mock_create_privacy_request.call_args[1]
        identity_of_privacy_request = call_kwargs["data"][0].identity
        assert identity_of_privacy_request.email == "test@email.com"
        assert identity_of_privacy_request.ga_client_id == browser_identity.ga_client_id

        provided_identity.delete(db)
