from datetime import datetime, timedelta, timezone
from time import sleep
from typing import List
from uuid import uuid4

import pytest
import requests_mock
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ManualWebhookFieldsUnset,
    NoCachedManualWebhookEntry,
    PrivacyRequestPaused,
)
from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.models.policy import CurrentStep, Policy
from fides.api.ops.models.privacy_request import (
    CheckpointActionRequired,
    PrivacyRequest,
    PrivacyRequestError,
    PrivacyRequestNotifications,
    PrivacyRequestStatus,
    can_run_checkpoint,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.manual_connector import ManualAction
from fides.api.ops.util.cache import FidesopsRedis, get_identity_cache_key
from fides.api.ops.util.constants import API_DATE_FORMAT
from fides.core.config import CONFIG

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
                    "derived_identity": {"phone_number": "+5555555555"},
                    "halt": False,
                },
                status_code=200,
            )
            privacy_request.trigger_policy_webhook(webhook)
            db.refresh(privacy_request)
            assert privacy_request.status == PrivacyRequestStatus.in_processing
            assert privacy_request.get_cached_identity_data() == {
                "email": "customer-1@example.com",
                "phone_number": "+5555555555",
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
    @pytest.fixture(scope="function")
    def set_verification_code_ttl_to_1(self):
        """sets the `redis.identity_verification_code_ttl_seconds` property to `1`"""
        original_value = CONFIG.redis.identity_verification_code_ttl_seconds
        CONFIG.redis.identity_verification_code_ttl_seconds = 1
        yield
        CONFIG.redis.identity_verification_code_ttl_seconds = original_value

    def test_cache_code(self, privacy_request):
        assert not privacy_request.get_cached_verification_code()

        privacy_request.cache_identity_verification_code("123456")

        assert privacy_request.get_cached_verification_code() == "123456"

    @pytest.mark.usefixtures(
        "set_verification_code_ttl_to_1",
    )
    def test_verification_code_expires(self, privacy_request):
        """
        Ensure the verification code expires correctly based on appropriate app config
        """

        privacy_request.cache_identity_verification_code("123456")
        assert privacy_request.get_cached_verification_code() == "123456"
        sleep(1.1)  # sleep a bit more than 1 just to give some breathing room
        assert privacy_request.get_cached_verification_code() is None


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
            privacy_request.get_manual_webhook_input_strict(access_manual_webhook)

        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={"email": "customer-1@example.com", "last_name": "Customer"},
        )

        assert privacy_request.get_manual_webhook_input_strict(
            access_manual_webhook
        ) == {
            "email": "customer-1@example.com",
            "last_name": "Customer",
        }

    def test_cache_no_fields_supplied(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={},
        )

        assert privacy_request.get_manual_webhook_input_strict(
            access_manual_webhook
        ) == {
            "email": None,
            "last_name": None,
        }, "Missing fields persisted as None"

    def test_cache_some_fields_supplied(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={
                "email": "customer-1@example.com",
            },
        )

        assert privacy_request.get_manual_webhook_input_strict(
            access_manual_webhook
        ) == {
            "email": "customer-1@example.com",
            "last_name": None,
        }, "Missing fields saved as None"

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

    def test_fields_added_to_webhook_definition(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test the use case where new fields have been added to the webhook definition
        since the webhook data was saved to the privacy request"""
        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={"last_name": "Customer", "email": "jane@example.com"},
        )

        access_manual_webhook.fields.append(
            {"pii_field": "Phone", "dsr_package_label": "phone"}
        )
        access_manual_webhook.save(db)

        with pytest.raises(ManualWebhookFieldsUnset):
            privacy_request.get_manual_webhook_input_strict(access_manual_webhook)

    def test_fields_removed_from_webhook_definition(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test the use case where fields have been removed from the webhook definition
        since the webhook data was saved to the privacy request"""
        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={"last_name": "Customer", "email": "jane@example.com"},
        )

        access_manual_webhook.fields = [
            {"pii_field": "last_name", "dsr_package_label": "last_name"}
        ]
        access_manual_webhook.save(db)

        with pytest.raises(ValidationError):
            privacy_request.get_manual_webhook_input_strict(access_manual_webhook)

    def test_non_strict_retrieval_from_cache(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test non-strict retrieval, we ignore extra fields saved and serialize missing fields as None"""
        privacy_request.cache_manual_webhook_input(
            manual_webhook=access_manual_webhook,
            input_data={"email": "customer-1@example.com", "last_name": "Customer"},
        )

        access_manual_webhook.fields = [  # email field deleted
            {"pii_field": "First Name", "dsr_package_label": "first_name"},  # New Field
            {
                "pii_field": "Last Name",
                "dsr_package_label": "last_name",
            },  # Existing Field
            {"pii_field": "Phone", "dsr_package_label": "phone"},  # New Field
        ]
        access_manual_webhook.save(db)

        overlap_input = privacy_request.get_manual_webhook_input_non_strict(
            access_manual_webhook
        )
        assert overlap_input == {
            "first_name": None,
            "last_name": "Customer",
            "phone": None,
        }, "Ignores 'email' field saved to privacy request"


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


def test_privacy_request_error_notification(db, policy):
    PrivacyRequestNotifications.create(
        db=db,
        data={
            "email": "some@email.com, another@email.com",
            "notify_after_failures": 2,
        },
    )

    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 1, 1),
            "finished_processing_at": datetime(2021, 1, 1),
            "requested_at": datetime(2021, 1, 1),
            "status": PrivacyRequestStatus.error,
            "origin": "https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )

    privacy_request.error_processing(db)

    unsent_errors = PrivacyRequestError.filter(
        db=db, conditions=(PrivacyRequestError.message_sent.is_(False))
    ).all()

    assert len(unsent_errors) == 1
