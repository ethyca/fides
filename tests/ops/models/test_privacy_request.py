from datetime import datetime, timedelta, timezone
from typing import List
from uuid import uuid4

import pytest
import requests_mock
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fidesops.ops.common_exceptions import (
    ClientUnsuccessfulException,
    NoCachedManualWebhookEntry,
    PrivacyRequestPaused,
)
from fidesops.ops.graph.config import CollectionAddress
from fidesops.ops.models.policy import CurrentStep, Policy
from fidesops.ops.models.privacy_request import (
    CheckpointActionRequired,
    Consent,
    ConsentRequest,
    PrivacyRequest,
    PrivacyRequestStatus,
    ProvidedIdentity,
    can_run_checkpoint,
)
from fidesops.ops.schemas.redis_cache import Identity
from fidesops.ops.service.connectors.manual_connector import ManualAction
from fidesops.ops.util.cache import FidesopsRedis, get_identity_cache_key
from fidesops.ops.util.constants import API_DATE_FORMAT

paused_location = CollectionAddress("test_dataset", "test_collection")


def test_privacy_request(
    db: Session, policy: Policy, privacy_request: PrivacyRequest
) -> None:
    from_db = PrivacyRequest.get(db=db, object_id=privacy_request.id)
    assert from_db is not None
    assert from_db.id is not None
    assert from_db.policy.id == policy.id
    assert from_db.client_id == policy.client_id


def test_create_privacy_request_sets_requested_at(
    db: Session,
    policy: Policy,
) -> None:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": "pending",
        },
    )
    assert pr.requested_at is not None
    pr.delete(db)

    pr = PrivacyRequest.create(
        db=db,
        data={
            "policy_id": policy.id,
            "status": "pending",
        },
    )
    assert pr.requested_at is not None
    pr.delete(db)

    requested_at = datetime.now(timezone.utc)
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": requested_at,
            "policy_id": policy.id,
            "status": "pending",
        },
    )
    assert pr.requested_at == requested_at
    pr.delete(db)


def test_create_privacy_request_sets_due_date(
    db: Session,
    policy: Policy,
) -> None:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "policy_id": policy.id,
            "status": "pending",
        },
    )
    assert pr.due_date is not None
    pr.delete(db)

    requested_at = datetime.now(timezone.utc)
    due_date = timedelta(days=policy.execution_timeframe) + requested_at
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": requested_at,
            "policy_id": policy.id,
            "status": "pending",
        },
    )
    assert pr.due_date == due_date
    pr.delete(db)

    requested_at_str = "2021-08-30T16:09:37.359Z"
    requested_at = datetime.strptime(requested_at_str, API_DATE_FORMAT).replace(
        tzinfo=timezone.utc
    )
    due_date = timedelta(days=policy.execution_timeframe) + requested_at
    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": requested_at_str,
            "policy_id": policy.id,
            "status": "pending",
        },
    )
    assert pr.due_date == due_date
    pr.delete(db)


def test_update_privacy_requests(db: Session, privacy_requests: PrivacyRequest) -> None:
    privacy_request = privacy_requests[0]
    EXTERNAL_ID_TO_UPDATE = privacy_request.external_id
    NEW_EXTERNAL_ID = str(uuid4())
    updated = PrivacyRequest.update_with_class(
        db=db,
        conditions=(PrivacyRequest.external_id == EXTERNAL_ID_TO_UPDATE),
        values={
            "external_id": NEW_EXTERNAL_ID,
        },
    )
    assert updated == 1
    from_db = PrivacyRequest.get(db, object_id=privacy_request.id)
    assert from_db.external_id == NEW_EXTERNAL_ID


def test_get_all_privacy_requests(
    db: Session, privacy_requests: List[PrivacyRequest]
) -> None:
    assert len(PrivacyRequest.all(db=db)) == len(privacy_requests)


def test_filter_privacy_requests(
    db: Session, privacy_requests: List[PrivacyRequest]
) -> None:
    ids = [pr.id for pr in privacy_requests]
    filtered = PrivacyRequest.filter(
        db=db,
        conditions=(PrivacyRequest.status == PrivacyRequestStatus.in_processing),
    ).filter(PrivacyRequest.id.in_(ids))

    assert filtered.count() == 3
    filtered = PrivacyRequest.filter(
        db=db,
        conditions=(PrivacyRequest.requested_at <= datetime.utcnow()),
    ).filter(PrivacyRequest.id.in_(ids))
    assert filtered.count() == 3
    filtered = PrivacyRequest.filter(
        db=db,
        conditions=(PrivacyRequest.external_id == "this does not exist"),
    ).filter(PrivacyRequest.id.in_(ids))
    assert filtered.count() == 0
    filtered = PrivacyRequest.filter(
        db=db,
        conditions=(PrivacyRequest.external_id == privacy_requests[0].external_id),
    ).filter(PrivacyRequest.id.in_(ids))
    assert filtered.count() == 1


def test_save_privacy_request(db: Session, privacy_request: PrivacyRequest) -> None:
    EXTERNAL_ID = "testing"
    privacy_request.external_id = EXTERNAL_ID
    privacy_request.save(db)
    from_db = PrivacyRequest.get(db=db, object_id=privacy_request.id)
    assert from_db.external_id == EXTERNAL_ID


def test_delete_privacy_request(db: Session, policy: Policy) -> None:
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": str(uuid4()),
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.in_processing,
            "origin": f"https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    privacy_request.delete(db)
    from_db = PrivacyRequest.get(db=db, object_id=privacy_request.id)
    assert from_db is None


def test_delete_privacy_request_removes_cached_data(
    cache: FidesopsRedis,
    db: Session,
    policy: Policy,
) -> None:
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": str(uuid4()),
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.in_processing,
            "origin": f"https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    identity_attribute = "email"
    identity_value = "test@example.com"
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)
    key = get_identity_cache_key(
        privacy_request_id=privacy_request.id,
        identity_attribute=identity_attribute,
    )
    assert cache.get(key) == identity_value
    privacy_request.delete(db)
    from_db = PrivacyRequest.get(db=db, object_id=privacy_request.id)
    assert from_db is None
    assert cache.get(key) is None


class TestPrivacyRequestTriggerWebhooks:
    def test_trigger_one_way_policy_webhook(
        self,
        https_connection_config,
        db,
        privacy_request,
        policy,
        policy_pre_execution_webhooks,
    ):
        webhook = policy_pre_execution_webhooks[0]
        identity = Identity(email="customer-1@example.com")
        privacy_request.cache_identity(identity)

        with requests_mock.Mocker() as mock_response:
            # One-way requests ignore any responses returned
            mock_response.post(
                https_connection_config.secrets["url"],
                json={
                    "privacy_request_id": privacy_request.id,
                    "direction": webhook.direction.value,
                    "callback_type": webhook.prefix,
                    "identity": identity.dict(),
                },
                status_code=500,
            )
            privacy_request.trigger_policy_webhook(webhook)
            db.refresh(privacy_request)
            assert privacy_request.status == PrivacyRequestStatus.in_processing

    def test_trigger_two_way_policy_webhook_with_error(
        self,
        db,
        https_connection_config,
        privacy_request,
        policy,
        policy_pre_execution_webhooks,
    ):
        webhook = policy_pre_execution_webhooks[1]
        identity = Identity(email="customer-1@example.com")
        privacy_request.cache_identity(identity)

        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                https_connection_config.secrets["url"],
                json={
                    "privacy_request_id": privacy_request.id,
                    "direction": webhook.direction.value,
                    "callback_type": webhook.prefix,
                    "identity": identity.dict(),
                },
                status_code=500,
            )
            with pytest.raises(ClientUnsuccessfulException):
                privacy_request.trigger_policy_webhook(webhook)

    def test_trigger_two_way_policy_webhook_200_proceed(
        self,
        db,
        https_connection_config,
        privacy_request,
        policy,
        policy_pre_execution_webhooks,
    ):
        webhook = policy_pre_execution_webhooks[1]
        identity = Identity(email="customer-1@example.com")
        privacy_request.cache_identity(identity)

        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                https_connection_config.secrets["url"],
                json={
                    "privacy_request_id": privacy_request.id,
                    "direction": webhook.direction.value,
                    "callback_type": webhook.prefix,
                    "identity": identity.dict(),
                    "halt": False,
                },
                status_code=200,
            )
            privacy_request.trigger_policy_webhook(webhook)
            db.refresh(privacy_request)
            assert privacy_request.status == PrivacyRequestStatus.in_processing

    def test_trigger_two_way_policy_webhook_200_pause(
        self,
        db,
        https_connection_config,
        privacy_request,
        policy,
        policy_pre_execution_webhooks,
    ):
        webhook = policy_pre_execution_webhooks[1]
        identity = Identity(email="customer-1@example.com")
        privacy_request.cache_identity(identity)

        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                https_connection_config.secrets["url"],
                json={
                    "privacy_request_id": privacy_request.id,
                    "direction": webhook.direction.value,
                    "callback_type": webhook.prefix,
                    "identity": identity.dict(),
                    "halt": True,
                },
                status_code=200,
            )

            with pytest.raises(PrivacyRequestPaused):
                privacy_request.trigger_policy_webhook(webhook)

    def test_trigger_two_way_policy_webhook_add_derived_identity(
        self,
        db,
        https_connection_config,
        privacy_request,
        policy,
        policy_pre_execution_webhooks,
    ):
        webhook = policy_pre_execution_webhooks[1]
        identity = Identity(email="customer-1@example.com")
        privacy_request.cache_identity(identity)

        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                https_connection_config.secrets["url"],
                json={
                    "privacy_request_id": privacy_request.id,
                    "direction": webhook.direction.value,
                    "callback_type": webhook.prefix,
                    "identity": identity.dict(),
                    "derived_identity": {"phone_number": "555-555-5555"},
                    "halt": False,
                },
                status_code=200,
            )
            privacy_request.trigger_policy_webhook(webhook)
            db.refresh(privacy_request)
            assert privacy_request.status == PrivacyRequestStatus.in_processing
            assert privacy_request.get_cached_identity_data() == {
                "email": "customer-1@example.com",
                "phone_number": "555-555-5555",
            }

    def test_two_way_validation_issues(
        self,
        db,
        https_connection_config,
        privacy_request,
        policy,
        policy_pre_execution_webhooks,
    ):
        webhook = policy_pre_execution_webhooks[1]
        identity = Identity(email="customer-1@example.com")
        privacy_request.cache_identity(identity)

        # halt not included
        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                https_connection_config.secrets["url"],
                json={
                    "privacy_request_id": privacy_request.id,
                    "direction": webhook.direction.value,
                    "callback_type": webhook.prefix,
                    "identity": identity.dict(),
                },
                status_code=200,
            )
            with pytest.raises(ValidationError):
                privacy_request.trigger_policy_webhook(webhook)

        # Derived identity invalid
        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                https_connection_config.secrets["url"],
                json={
                    "privacy_request_id": privacy_request.id,
                    "direction": webhook.direction.value,
                    "callback_type": webhook.prefix,
                    "identity": identity.dict(),
                    "derived_identity": {"unsupported_identity": "1200 Fides Road"},
                    "halt": True,
                },
                status_code=200,
            )
            with pytest.raises(ValidationError):
                privacy_request.trigger_policy_webhook(webhook)


class TestCachePausedLocation:
    def test_privacy_request_cache_paused_location(self, privacy_request):
        assert privacy_request.get_paused_collection_details() is None

        paused_step = CurrentStep.erasure
        privacy_request.cache_paused_collection_details(
            step=paused_step,
            collection=paused_location,
            action_needed=[
                ManualAction(
                    locators={"email": "customer-1@example.com"},
                    get=["box_id", "associated_data"],
                    update=None,
                )
            ],
        )

        paused_details = privacy_request.get_paused_collection_details()
        assert paused_details.step == paused_step
        assert paused_details.collection == paused_location
        assert paused_details.action_needed == [
            ManualAction(
                locators={"email": "customer-1@example.com"},
                get=["box_id", "associated_data"],
                update=None,
            )
        ]

    def test_privacy_request_unpause(self, privacy_request):
        privacy_request.cache_paused_collection_details()

        assert privacy_request.get_paused_collection_details() is None


class TestCacheManualInput:
    def test_cache_manual_input(self, privacy_request):
        manual_data = [{"id": 1, "name": "Jane"}, {"id": 2, "name": "Hank"}]

        privacy_request.cache_manual_input(paused_location, manual_data)
        assert (
            privacy_request.get_manual_input(
                paused_location,
            )
            == manual_data
        )

    def test_cache_empty_manual_input(self, privacy_request):
        manual_data = []
        privacy_request.cache_manual_input(paused_location, manual_data)

        assert (
            privacy_request.get_manual_input(
                paused_location,
            )
            == []
        )

    def test_no_manual_data_in_cache(self, privacy_request):
        assert (
            privacy_request.get_manual_input(
                paused_location,
            )
            is None
        )


class TestCacheManualErasureCount:
    def test_cache_manual_erasure_count(self, privacy_request):
        privacy_request.cache_manual_erasure_count(paused_location, 5)

        cached_data = privacy_request.get_manual_erasure_count(paused_location)
        assert cached_data == 5

    def test_no_erasure_data_cached(self, privacy_request):
        cached_data = privacy_request.get_manual_erasure_count(paused_location)
        assert cached_data is None

    def test_zero_cached(self, privacy_request):
        privacy_request.cache_manual_erasure_count(paused_location, 0)
        cached_data = privacy_request.get_manual_erasure_count(paused_location)
        assert cached_data == 0


class TestPrivacyRequestCacheFailedStep:
    def test_cache_failed_step_and_collection(self, privacy_request):

        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.erasure, collection=paused_location
        )

        cached_data = privacy_request.get_failed_checkpoint_details()
        assert cached_data.step == CurrentStep.erasure
        assert cached_data.collection == paused_location
        assert cached_data.action_needed is None

    def test_cache_null_step_and_location(self, privacy_request):
        privacy_request.cache_failed_checkpoint_details()

        cached_data = privacy_request.get_failed_checkpoint_details()
        assert cached_data is None


class TestCacheIdentityVerificationCode:
    def test_cache_code(self, privacy_request):
        assert not privacy_request.get_cached_verification_code()

        privacy_request.cache_identity_verification_code("123456")

        assert privacy_request.get_cached_verification_code() == "123456"


class TestCacheEmailConnectorTemplateContents:
    def test_cache_template_contents(self, privacy_request):
        assert (
            privacy_request.get_email_connector_template_contents_by_dataset(
                CurrentStep.erasure, "email_dataset"
            )
            == []
        )

        privacy_request.cache_email_connector_template_contents(
            step=CurrentStep.erasure,
            collection=CollectionAddress("email_dataset", "test_collection"),
            action_needed=[
                ManualAction(
                    locators={"email": "test@example.com"},
                    get=None,
                    update={"phone": "null_rewrite"},
                )
            ],
        )

        assert privacy_request.get_email_connector_template_contents_by_dataset(
            CurrentStep.erasure, "email_dataset"
        ) == [
            CheckpointActionRequired(
                step=CurrentStep.erasure,
                collection=CollectionAddress("email_dataset", "test_collection"),
                action_needed=[
                    ManualAction(
                        locators={"email": "test@example.com"},
                        get=None,
                        update={"phone": "null_rewrite"},
                    )
                ],
            )
        ]


class TestCacheManualWebhookInput:
    def test_cache_manual_webhook_input(self, privacy_request, access_manual_webhook):
        with pytest.raises(NoCachedManualWebhookEntry):
            privacy_request.get_manual_webhook_input(access_manual_webhook)

        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={"email": "customer-1@example.com", "last_name": "Customer"},
        )

        assert privacy_request.get_manual_webhook_input(access_manual_webhook) == {
            "email": "customer-1@example.com",
            "last_name": "Customer",
        }

    def test_cache_no_fields(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={},
        )

        assert privacy_request.get_manual_webhook_input(access_manual_webhook) == {
            "email": None,
            "last_name": None,
        }

    def test_cache_field_missing(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={
                "email": "customer-1@example.com",
            },
        )

        assert privacy_request.get_manual_webhook_input(access_manual_webhook) == {
            "email": "customer-1@example.com",
            "last_name": None,
        }

    def test_cache_extra_fields_not_in_webhook_specs(
        self, privacy_request, access_manual_webhook
    ):
        with pytest.raises(ValidationError):
            privacy_request.cache_manual_webhook_input(
                manual_webhook=access_manual_webhook,
                input_data={
                    "email": "customer-1@example.com",
                    "bad_field": "not_specified",
                },
            )

    def test_cache_manual_webhook_no_fields_defined(
        self, db, privacy_request, access_manual_webhook
    ):
        access_manual_webhook.fields = (
            None  # Specifically testing the None case to cover our bases
        )
        access_manual_webhook.save(db)

        with pytest.raises(ValidationError):
            privacy_request.cache_manual_webhook_input(
                manual_webhook=access_manual_webhook,
                input_data={"email": "customer-1@example.com", "last_name": "Customer"},
            )


class TestCanRunFromCheckpoint:
    def test_can_run_from_checkpoint(self):
        assert (
            can_run_checkpoint(
                request_checkpoint=CurrentStep.erasure_email_post_send,
                from_checkpoint=CurrentStep.erasure,
            )
            is True
        )

    def test_can_run_from_equivalent_checkpoint(self):
        assert (
            can_run_checkpoint(
                request_checkpoint=CurrentStep.erasure,
                from_checkpoint=CurrentStep.erasure,
            )
            is True
        )

    def test_cannot_run_from_completed_checkpoint(self):
        assert (
            can_run_checkpoint(
                request_checkpoint=CurrentStep.access,
                from_checkpoint=CurrentStep.erasure,
            )
            is False
        )

    def test_can_run_if_no_saved_checkpoint(self):
        assert (
            can_run_checkpoint(
                request_checkpoint=CurrentStep.access,
            )
            is True
        )


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
