from unittest import mock

from fides.api.ctl.database.seed import DEFAULT_CONSENT_POLICY
from fides.api.ops.api.v1.endpoints.consent_request_endpoints import (
    queue_privacy_request_to_propagate_consent,
)
from fides.api.ops.models.privacy_request import (
    Consent,
    ConsentRequest,
    PrivacyRequestStatus,
    ProvidedIdentity,
)
from fides.api.ops.schemas.policy import PolicyResponse
from fides.api.ops.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    ConsentPreferences,
    ConsentWithExecutableStatus,
    PrivacyRequestResponse,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.core.config import CONFIG


class TestConsent:
    def test_consent_with_data_uses(self, db):
        """
        Note saving consent with respect to "data uses" is slated for deprecation
        in favor of saving with respect to "privacy notices"
        """
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

        for consent in [consent_1, consent_2]:
            assert consent.privacy_notice_id is None
            assert consent.privacy_notice_history_id is None
            assert consent.data_use is not None
            assert consent.data_use_description is None
            assert consent.provided_identity_id == provided_identity.id
            assert consent.has_gpc_flag is False
            assert consent.conflicts_with_gpc is False
            assert consent.privacy_notice_version is None

    def test_consent_with_gpc(self, db):
        """
        Note saving consent with respect to "data uses" is slated for deprecation
        in favor of saving with respect to "privacy notices"
        """
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

    def test_save_consent_with_respect_to_privacy_notices(self, db, privacy_notice):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        history = privacy_notice.histories[0]
        consent = Consent.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
                "data_use": None,
                "data_use_description": None,
                "opt_in": True,
                "has_gpc_flag": None,
                "conflicts_with_gpc": False,
                "privacy_notice_id": privacy_notice.id,
                "privacy_notice_history_id": history.id,
                "privacy_notice_version": 1,
                "user_geography": "us_ca",
            },
        )

        assert consent.privacy_notice == privacy_notice
        assert consent.privacy_notice_history == history
        assert consent.data_use is None
        assert consent.data_use_description is None
        assert consent.provided_identity == provided_identity
        assert consent.has_gpc_flag is False
        assert consent.conflicts_with_gpc is False
        assert consent.privacy_notice_version == 1

        consent.delete(db)

    def test_get_current_consent_preferences(
        self, db, privacy_notice, privacy_notice_us_ca_provide
    ):
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
        assert (
            Consent.get_current_consent_preferences(db, provided_identity) == []
        ), "No Consent Preferences Saved"

        consent_data_1 = {
            "provided_identity_id": provided_identity.id,
            "data_use": "user.biometric_health",
            "opt_in": True,
            "has_gpc_flag": True,
            "conflicts_with_gpc": True,
        }
        old_consent_1 = Consent.create(db, data=consent_data_1)
        assert Consent.get_current_consent_preferences(db, provided_identity) == [
            old_consent_1
        ]

        new_consent_1 = Consent.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
                "data_use": None,
                "data_use_description": None,
                "opt_in": True,
                "has_gpc_flag": None,
                "conflicts_with_gpc": False,
                "privacy_notice_id": privacy_notice.id,
                "privacy_notice_history_id": privacy_notice.histories[0].id,
                "privacy_notice_version": 1,
                "user_geography": "us_ca",
            },
        )

        assert Consent.get_current_consent_preferences(db, provided_identity) == [
            old_consent_1,
            new_consent_1,
        ]

        new_consent_2 = Consent.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
                "data_use": None,
                "data_use_description": None,
                "opt_in": False,
                "has_gpc_flag": None,
                "conflicts_with_gpc": False,
                "privacy_notice_id": privacy_notice_us_ca_provide.id,
                "privacy_notice_history_id": privacy_notice_us_ca_provide.histories[
                    0
                ].id,
                "privacy_notice_version": 1,
                "user_geography": "us_ca",
            },
        )

        assert Consent.get_current_consent_preferences(db, provided_identity) == [
            old_consent_1,
            new_consent_1,
            new_consent_2,
        ]

        updated_privacy_notice = privacy_notice.update(db, data={"name": "New Name"})
        new_consent_3 = Consent.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
                "data_use": None,
                "data_use_description": None,
                "opt_in": False,
                "has_gpc_flag": None,
                "conflicts_with_gpc": False,
                "privacy_notice_id": updated_privacy_notice.id,
                "privacy_notice_history_id": updated_privacy_notice.histories[1].id,
                "privacy_notice_version": 2,
                "user_geography": "us_ca",
            },
        )
        import pdb

        pdb.set_trace()
        assert Consent.get_current_consent_preferences(db, provided_identity) == [
            old_consent_1,
            new_consent_2,
            new_consent_3,
        ]


class TestQueuePrivacyRequestToPropagateConsentHelper:
    @mock.patch(
        "fides.api.ops.api.v1.endpoints.consent_request_endpoints.create_privacy_request_func"
    )
    def test_queue_privacy_request_to_propagate_consent_saved_for_data_uses(
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

        queue_privacy_request_to_propagate_consent(
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
        "fides.api.ops.api.v1.endpoints.consent_request_endpoints.create_privacy_request_func"
    )
    def test_queue_privacy_request_to_propagate_consent_saved_for_privacy_notices(
        self, mock_create_privacy_request, db, consent_policy, privacy_notice
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
        privacy_notice_history = privacy_notice.histories[0]

        consent = Consent.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
                "data_use": None,
                "data_use_description": None,
                "opt_in": False,
                "has_gpc_flag": None,
                "conflicts_with_gpc": False,
                "privacy_notice_id": privacy_notice.id,
                "privacy_notice_history_id": privacy_notice_history.id,
                "privacy_notice_version": 1,
                "user_geography": "us_ca",
            },
        )

        consent_preferences = ConsentPreferences(consent=[consent])

        queue_privacy_request_to_propagate_consent(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            executable_consents=[],  # Not relevant for this workflow, to be deprecated
        )

        assert mock_create_privacy_request.called
        call_kwargs = mock_create_privacy_request.call_args[1]
        assert call_kwargs["db"] == db
        assert call_kwargs["data"][0].identity.email == "test@email.com"
        assert len(call_kwargs["data"][0].consent_preferences) == 1
        assert (
            call_kwargs["data"][0].consent_preferences[0].privacy_notice_history
            == consent_preferences.consent[0].privacy_notice_history
        )
        assert call_kwargs["data"][0].consent_preferences[0].opt_in is False
        assert (
            call_kwargs["authenticated"] is True
        ), "We already validated identity with a verification code earlier in the request"

        provided_identity.delete(db)
        consent.delete(db)

    @mock.patch(
        "fides.api.ops.api.v1.endpoints.consent_request_endpoints.create_privacy_request_func"
    )
    def test_queue_privacy_request_even_if_no_executable_preferences(
        self, mock_create_privacy_request, db, consent_policy
    ):
        """Slated to be deprecated"""
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

        queue_privacy_request_to_propagate_consent(
            db=db,
            provided_identity=provided_identity,
            policy=DEFAULT_CONSENT_POLICY,
            consent_preferences=consent_preferences,
            executable_consents=[
                ConsentWithExecutableStatus(data_use="advertising", executable=False)
            ],
        )

        assert mock_create_privacy_request.called

    @mock.patch(
        "fides.api.ops.api.v1.endpoints.consent_request_endpoints.create_privacy_request_func"
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

        queue_privacy_request_to_propagate_consent(
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
