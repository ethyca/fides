import warnings
from datetime import datetime, timedelta, timezone
from io import BytesIO
from time import sleep
from typing import Any, Dict, List
from uuid import uuid4

import pytest
import requests_mock
from pydantic import ValidationError
from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session, joinedload

from fides.api.common_exceptions import (
    ClientUnsuccessfulException,
    ManualWebhookFieldsUnset,
    NoCachedManualWebhookEntry,
    PrivacyRequestPaused,
)
from fides.api.graph.config import CollectionAddress
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.comment import (
    Comment,
    CommentReference,
    CommentReferenceType,
    CommentType,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestError,
    PrivacyRequestNotifications,
    can_run_checkpoint,
)
from fides.api.schemas.policy import CurrentStep
from fides.api.schemas.privacy_request import (
    CheckpointActionRequired,
    CustomPrivacyRequestField,
    ManualAction,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity, LabeledIdentity
from fides.api.util.cache import FidesopsRedis, get_cache, get_identity_cache_key
from fides.api.util.constants import API_DATE_FORMAT
from fides.config import CONFIG

paused_location = CollectionAddress("test_dataset", "test_collection")


def test_privacy_request(
    db: Session,
    policy: Policy,
    privacy_request: PrivacyRequest,
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
    assert (
        privacy_request.get_cached_identity_data()[identity_attribute] == identity_value
    )
    privacy_request.delete(db)
    from_db = PrivacyRequest.get(db=db, object_id=privacy_request.id)
    assert from_db is None
    assert cache.get(key) is None


@pytest.mark.parametrize(
    "privacy_request,expected_status",
    [
        ("privacy_request_status_approved", PrivacyRequestStatus.in_processing),
        ("privacy_request_status_pending", PrivacyRequestStatus.in_processing),
        ("privacy_request_status_canceled", PrivacyRequestStatus.canceled),
    ],
)
def test_privacy_request_moves_to_in_processing(
    db: Session, request, privacy_request, expected_status
):
    pr: PrivacyRequest = request.getfixturevalue(privacy_request)
    pr.start_processing(db)
    db.refresh(pr)
    assert pr.status == expected_status


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
                    "identity": identity.model_dump(mode="json"),
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
                    "identity": identity.model_dump(mode="json"),
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
                    "identity": identity.model_dump(mode="json"),
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
                    "identity": identity.model_dump(mode="json"),
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
                    "identity": identity.model_dump(mode="json"),
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
                    "identity": identity.model_dump(mode="json"),
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
                    "identity": identity.model_dump(mode="json"),
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


class TestPrivacyRequestCacheFailedStep:
    def test_cache_failed_step(self, privacy_request):
        privacy_request.cache_failed_checkpoint_details(step=CurrentStep.erasure)

        cached_data = privacy_request.get_failed_checkpoint_details()
        assert cached_data.step == CurrentStep.erasure
        assert cached_data.collection is None  # This is deprecated
        assert (
            cached_data.action_needed is None
        )  # This isn't applicable for failed details

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


class TestCacheManualWebhookAccessInput:
    def test_cache_manual_webhook_access_input(
        self, privacy_request, access_manual_webhook
    ):
        with pytest.raises(NoCachedManualWebhookEntry):
            privacy_request.get_manual_webhook_access_input_strict(
                access_manual_webhook
            )

        privacy_request.cache_manual_webhook_access_input(
            manual_webhook=access_manual_webhook,
            input_data={"email": "customer-1@example.com", "last_name": "Customer"},
        )

        assert privacy_request.get_manual_webhook_access_input_strict(
            access_manual_webhook
        ) == {
            "email": "customer-1@example.com",
            "last_name": "Customer",
        }

    def test_cache_no_fields_supplied(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_access_input(
            manual_webhook=access_manual_webhook,
            input_data={},
        )

        assert privacy_request.get_manual_webhook_access_input_strict(
            access_manual_webhook
        ) == {
            "email": None,
            "last_name": None,
        }, "Missing fields persisted as None"

    def test_cache_some_fields_supplied(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_access_input(
            manual_webhook=access_manual_webhook,
            input_data={
                "email": "customer-1@example.com",
            },
        )

        assert privacy_request.get_manual_webhook_access_input_strict(
            access_manual_webhook
        ) == {
            "email": "customer-1@example.com",
            "last_name": None,
        }, "Missing fields saved as None"

    def test_cache_extra_fields_not_in_webhook_specs(
        self, privacy_request, access_manual_webhook
    ):
        with pytest.raises(ValidationError):
            privacy_request.cache_manual_webhook_access_input(
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
            privacy_request.cache_manual_webhook_access_input(
                manual_webhook=access_manual_webhook,
                input_data={"email": "customer-1@example.com", "last_name": "Customer"},
            )

    def test_fields_added_to_webhook_definition(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test the use case where new fields have been added to the webhook definition
        since the webhook data was saved to the privacy request"""
        privacy_request.cache_manual_webhook_access_input(
            manual_webhook=access_manual_webhook,
            input_data={"last_name": "Customer", "email": "jane@example.com"},
        )

        access_manual_webhook.fields.append(
            {"pii_field": "Phone", "dsr_package_label": "phone"}
        )
        access_manual_webhook.save(db)

        with pytest.raises(ManualWebhookFieldsUnset):
            privacy_request.get_manual_webhook_access_input_strict(
                access_manual_webhook
            )

    def test_fields_removed_from_webhook_definition(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test the use case where fields have been removed from the webhook definition
        since the webhook data was saved to the privacy request"""
        privacy_request.cache_manual_webhook_access_input(
            manual_webhook=access_manual_webhook,
            input_data={"last_name": "Customer", "email": "jane@example.com"},
        )

        access_manual_webhook.fields = [
            {"pii_field": "last_name", "dsr_package_label": "last_name"}
        ]
        access_manual_webhook.save(db)

        with pytest.raises(ValidationError):
            privacy_request.get_manual_webhook_access_input_strict(
                access_manual_webhook
            )

    def test_non_strict_retrieval_from_cache(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test non-strict retrieval, we ignore extra fields saved and serialize missing fields as None"""
        privacy_request.cache_manual_webhook_access_input(
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

        overlap_input = privacy_request.get_manual_webhook_access_input_non_strict(
            access_manual_webhook
        )
        assert overlap_input == {
            "first_name": None,
            "last_name": "Customer",
            "phone": None,
        }, "Ignores 'email' field saved to privacy request"


class TestCacheManualWebhookErasureInput:
    def test_cache_manual_webhook_erasure_input(
        self, privacy_request, access_manual_webhook
    ):
        with pytest.raises(NoCachedManualWebhookEntry):
            privacy_request.get_manual_webhook_erasure_input_strict(
                access_manual_webhook
            )

        privacy_request.cache_manual_webhook_erasure_input(
            manual_webhook=access_manual_webhook,
            input_data={"email": False, "last_name": True},
        )

        assert privacy_request.get_manual_webhook_erasure_input_strict(
            access_manual_webhook
        ) == {
            "email": False,
            "last_name": True,
        }

    def test_cache_no_fields_supplied(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_erasure_input(
            manual_webhook=access_manual_webhook,
            input_data={},
        )

        assert privacy_request.get_manual_webhook_erasure_input_strict(
            access_manual_webhook
        ) == {
            "email": None,
            "last_name": None,
        }, "Missing fields persisted as None"

    def test_cache_some_fields_supplied(self, privacy_request, access_manual_webhook):
        privacy_request.cache_manual_webhook_erasure_input(
            manual_webhook=access_manual_webhook,
            input_data={
                "email": False,
            },
        )

        assert privacy_request.get_manual_webhook_erasure_input_strict(
            access_manual_webhook
        ) == {
            "email": False,
            "last_name": None,
        }, "Missing fields saved as None"

    def test_cache_extra_fields_not_in_webhook_specs(
        self, privacy_request, access_manual_webhook
    ):
        with pytest.raises(ValidationError):
            privacy_request.cache_manual_webhook_erasure_input(
                manual_webhook=access_manual_webhook,
                input_data={
                    "email": False,
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
            privacy_request.cache_manual_webhook_erasure_input(
                manual_webhook=access_manual_webhook,
                input_data={"email": False, "last_name": True},
            )

    def test_fields_added_to_webhook_definition(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test the use case where new fields have been added to the webhook definition
        since the webhook data was saved to the privacy request"""
        privacy_request.cache_manual_webhook_erasure_input(
            manual_webhook=access_manual_webhook,
            input_data={"last_name": True, "email": False},
        )

        access_manual_webhook.fields.append(
            {"pii_field": "Phone", "dsr_package_label": "phone"}
        )
        access_manual_webhook.save(db)

        with pytest.raises(ManualWebhookFieldsUnset):
            privacy_request.get_manual_webhook_erasure_input_strict(
                access_manual_webhook
            )

    def test_fields_removed_from_webhook_definition(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test the use case where fields have been removed from the webhook definition
        since the webhook data was saved to the privacy request"""
        privacy_request.cache_manual_webhook_erasure_input(
            manual_webhook=access_manual_webhook,
            input_data={"last_name": True, "email": False},
        )

        access_manual_webhook.fields = [
            {"pii_field": "last_name", "dsr_package_label": "last_name"}
        ]
        access_manual_webhook.save(db)

        with pytest.raises(ValidationError):
            privacy_request.get_manual_webhook_erasure_input_strict(
                access_manual_webhook
            )

    def test_non_strict_retrieval_from_cache(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test non-strict retrieval, we ignore extra fields saved and serialize missing fields as None"""
        privacy_request.cache_manual_webhook_erasure_input(
            manual_webhook=access_manual_webhook,
            input_data={"email": False, "last_name": True},
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

        overlap_input = privacy_request.get_manual_webhook_erasure_input_non_strict(
            access_manual_webhook
        )
        assert overlap_input == {
            "first_name": None,
            "last_name": True,
            "phone": None,
        }, "Ignores 'email' field saved to privacy request"


class TestCanRunFromCheckpoint:
    def test_can_run_from_checkpoint(self):
        assert (
            can_run_checkpoint(
                request_checkpoint=CurrentStep.email_post_send,
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


class TestPrivacyRequestCustomFieldFunctions:
    """Fides has two settings around custom privacy request fields:

    - CONFIG.execution.allow_custom_privacy_request_field_collection - whether or not to store custom privacy request fields in the database
    - CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution - whether or not to use custom privacy request fields in request execution

    These two constraints are enforced by controlling the behavior of
    the cache and persist functions on the PrivacyRequest model.
    """

    def test_cache_custom_privacy_request_fields(
        self,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_fields_in_request_execution_enabled,
    ):
        privacy_request = PrivacyRequest(id=str(uuid4()))
        privacy_request.cache_custom_privacy_request_fields(
            custom_privacy_request_fields={
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
                "support_id": CustomPrivacyRequestField(label="Support ID", value=1),
            }
        )
        assert privacy_request.get_cached_custom_privacy_request_fields() == {
            "first_name": "John",
            "last_name": "Doe",
            "subscriber_ids": ["123", "456"],
            "account_ids": [123, 456],
            "support_id": 1,
        }

    def test_cache_custom_privacy_request_fields_collection_disabled(
        self,
        allow_custom_privacy_request_field_collection_disabled,
    ):
        """Custom privacy request fields should not be cached if collection is disabled"""
        privacy_request = PrivacyRequest(id=str(uuid4()))
        privacy_request.cache_custom_privacy_request_fields(
            custom_privacy_request_fields={
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
                "support_id": CustomPrivacyRequestField(label="Support ID", value=1),
            }
        )
        assert privacy_request.get_cached_custom_privacy_request_fields() == {}

    def test_cache_custom_privacy_request_fields_collection_enabled_use_disabled(
        self,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_fields_in_request_execution_disabled,
    ):
        """Custom privacy request fields should not be cached if use is disabled"""
        privacy_request = PrivacyRequest(id=str(uuid4()))
        privacy_request.cache_custom_privacy_request_fields(
            custom_privacy_request_fields={
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
                "support_id": CustomPrivacyRequestField(label="Support ID", value=1),
            }
        )
        assert privacy_request.get_cached_custom_privacy_request_fields() == {}

    def test_persist_custom_privacy_request_fields(
        self,
        db,
        privacy_request,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_fields_in_request_execution_enabled,
    ):
        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
                "support_id": CustomPrivacyRequestField(label="Support ID", value=1),
            },
        )
        assert privacy_request.get_persisted_custom_privacy_request_fields() == {
            "first_name": {"label": "First name", "value": "John"},
            "last_name": {"label": "Last name", "value": "Doe"},
            "subscriber_ids": {"label": "Subscriber IDs", "value": ["123", "456"]},
            "account_ids": {"label": "Account IDs", "value": [123, 456]},
            "support_id": {"label": "Support ID", "value": 1},
        }

    def test_persist_custom_privacy_request_fields_collection_disabled(
        self,
        db,
        privacy_request,
        allow_custom_privacy_request_field_collection_disabled,
    ):
        """Custom privacy request fields should not be persisted if collection is disabled"""
        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
                "support_id": CustomPrivacyRequestField(label="Support ID", value=1),
            },
        )
        assert privacy_request.get_persisted_custom_privacy_request_fields() == {}


class TestPrivacyRequestCustomIdentities:
    def test_cache_custom_identities(self, privacy_request):
        privacy_request.cache_identity(
            identity={
                "customer_id": LabeledIdentity(label="Custom ID", value=123),
                "account_id": LabeledIdentity(label="Account ID", value="456"),
            },
        )
        assert privacy_request.get_cached_identity_data() == {
            "email": "test@example.com",
            "customer_id": {"label": "Custom ID", "value": 123},
            "account_id": {"label": "Account ID", "value": "456"},
        }

    def test_old_cache_can_be_read(self, privacy_request):
        """
        Previously we were storing unencoded values, but with 2.34 we updated
        the `cache_identity` function to JSON encode the values before caching.
        We need to make sure we can still read these old values using the
        new `get_cached_identity_data` function.
        """

        def cache_identity(identity: Identity, privacy_request_id: str) -> None:
            """Old function for caching identity"""
            cache: FidesopsRedis = get_cache()
            identity_dict: Dict[str, Any] = dict(identity)
            for key, value in identity_dict.items():
                if value is not None:
                    cache.set_with_autoexpire(
                        get_identity_cache_key(privacy_request_id, key),
                        value,
                    )

        cache_identity(
            identity=Identity(
                email="user@example.com",
                phone_number="+15558675309",
                ga_client_id="GA123",
                ljt_readerID="LJT456",
                fides_user_device_id="4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
            ),
            privacy_request_id=privacy_request.id,
        )
        assert privacy_request.get_cached_identity_data() == {
            "phone_number": "+15558675309",
            "email": "user@example.com",
            "ga_client_id": "GA123",
            "ljt_readerID": "LJT456",
            "fides_user_device_id": "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
        }

    def test_persist_custom_identities(self, db, privacy_request):
        privacy_request.persist_identity(
            db=db,
            identity={
                "customer_id": LabeledIdentity(label="Custom ID", value=123),
                "account_id": LabeledIdentity(label="Account ID", value="456"),
            },
        )
        assert privacy_request.get_persisted_identity() == Identity(
            email="test@example.com",
            phone_number="+12345678910",
            customer_id=LabeledIdentity(label="Custom ID", value=123),
            account_id=LabeledIdentity(label="Account ID", value="456"),
        )


class TestPrivacyRequestAttachments:

    @pytest.fixture
    def mock_s3_client(self, s3_client, monkeypatch):
        """Fixture to mock the S3 client for attachment tests"""

        def mock_get_s3_client(auth_method, storage_secrets):
            return s3_client

        monkeypatch.setattr(
            "fides.api.service.storage.s3.get_s3_client", mock_get_s3_client
        )
        return s3_client

    @pytest.fixture
    def create_attachment(self, db, attachment_data, mock_s3_client):
        """Fixture to create a single attachment"""

        def _create_attachment(contents: bytes = b"test contents"):
            return Attachment.create_and_upload(
                db=db,
                data=attachment_data,
                attachment_file=BytesIO(contents),
            )

        return _create_attachment

    @pytest.fixture
    def create_attachment_reference(self, db):
        """Fixture to create an attachment reference"""

        def _create_reference(
            reference_id: str, attachment_id: str, reference_type: str
        ):
            return AttachmentReference.create(
                db,
                data={
                    "reference_id": reference_id,
                    "attachment_id": attachment_id,
                    "reference_type": reference_type,
                },
            )

        return _create_reference

    @pytest.fixture
    def cleanup_attachments(self, db):
        """Fixture to clean up attachments after tests"""

        def _cleanup(attachments):
            for attachment in attachments:
                attachment.delete(db)
            db.commit()

        return _cleanup

    def test_retrieve_attachments_from_privacy_request(
        self,
        db,
        create_attachment,
        create_attachment_reference,
        cleanup_attachments,
        privacy_request,
    ):
        # Create Attachments
        attachment1 = create_attachment(b"contents of test file 1")
        attachment2 = create_attachment(b"contents of test file 2")
        attachment3 = create_attachment(b"contents of test file 3")

        # Associate Attachments with the PrivacyRequest
        for attachment in [attachment1, attachment2, attachment3]:
            create_attachment_reference(
                privacy_request.id,
                attachment.id,
                AttachmentReferenceType.privacy_request,
            )

        # Verify that attachments can be retrieved
        retrieved_request = (
            db.query(PrivacyRequest).filter_by(id=privacy_request.id).first()
        )
        attachments = retrieved_request.attachments

        assert len(attachments) == 3
        # Verify that the attachments are in the correct order
        assert attachments[0].id == attachment1.id
        assert attachments[1].id == attachment2.id
        assert attachments[2].id == attachment3.id

        # Verify deleting the privacy request deletes the attachments.
        privacy_request.delete(db)
        db.commit()
        assert Attachment.get(db, object_id=attachment1.id) is None
        assert Attachment.get(db, object_id=attachment2.id) is None
        assert Attachment.get(db, object_id=attachment3.id) is None

    def test_privacy_request_get_attachment_by_id(
        self, db, create_attachment_reference, attachment, privacy_request
    ):
        # Associate Attachment with the PrivacyRequest
        create_attachment_reference(
            privacy_request.id,
            attachment.id,
            AttachmentReferenceType.privacy_request,
        )

        retrieved_attachment = privacy_request.get_attachment_by_id(db, attachment.id)
        assert retrieved_attachment.id == attachment.id

    def test_privacy_request_delete_attachment_by_id(
        self, db, create_attachment_reference, attachment, privacy_request
    ):
        # Associate Attachment with the PrivacyRequest
        create_attachment_reference(
            privacy_request.id,
            attachment.id,
            AttachmentReferenceType.privacy_request,
        )

        privacy_request.delete_attachment_by_id(db, attachment.id)
        assert privacy_request.get_attachment_by_id(db, attachment.id) is None

    def test_privacy_request_get_manual_webhook_attachments(
        self,
        db,
        create_attachment,
        create_attachment_reference,
        cleanup_attachments,
        privacy_request,
        access_manual_webhook,
    ):
        # Create Attachments
        attachment1 = create_attachment(b"contents of test file 1")
        attachment2 = create_attachment(b"contents of test file 2")

        # Associate Attachments with both the PrivacyRequest and the Access Manual Webhook
        for attachment in [attachment1, attachment2]:
            # Create reference to privacy request
            create_attachment_reference(
                privacy_request.id,
                attachment.id,
                AttachmentReferenceType.privacy_request,
            )
            # Create reference to access manual webhook
            create_attachment_reference(
                access_manual_webhook.id,
                attachment.id,
                AttachmentReferenceType.access_manual_webhook,
            )

        # Verify that attachments can be retrieved for access manual webhook
        access_attachments = privacy_request.get_access_manual_webhook_attachments(
            db, access_manual_webhook.id
        )
        assert len(access_attachments) == 2
        attachment_ids = sorted([a.id for a in access_attachments])
        access_attachment_ids = sorted([attachment1.id, attachment2.id])
        assert attachment_ids == access_attachment_ids

        # Create an attachment that's only associated with the privacy request
        attachment3 = create_attachment(b"contents of test file 3")
        create_attachment_reference(
            privacy_request.id,
            attachment3.id,
            AttachmentReferenceType.privacy_request,
        )

        # Verify that attachment3 is not included in the manual webhook attachments
        access_attachments = privacy_request.get_access_manual_webhook_attachments(
            db, access_manual_webhook.id
        )
        assert len(access_attachments) == 2
        assert attachment3.id not in [a.id for a in access_attachments]

        # Test erasure manual webhook attachments
        erasure_attachments = privacy_request.get_erasure_manual_webhook_attachments(
            db, access_manual_webhook.id
        )
        assert (
            len(erasure_attachments) == 0
        )  # No attachments associated with erasure webhook

        # Clean up
        cleanup_attachments([attachment1, attachment2, attachment3])

    def test_privacy_request_get_manual_webhook_attachments_no_attachments(
        self, db, privacy_request, access_manual_webhook
    ):
        """Test getting manual webhook attachments when none exist"""
        access_attachments = privacy_request.get_access_manual_webhook_attachments(
            db, access_manual_webhook.id
        )
        assert len(access_attachments) == 0

        erasure_attachments = privacy_request.get_erasure_manual_webhook_attachments(
            db, access_manual_webhook.id
        )
        assert len(erasure_attachments) == 0

    def test_privacy_request_attachment_relationship_warnings(
        self,
        s3_client,
        db,
        privacy_request,
        create_attachment,
        create_attachment_reference,
        mock_s3_client,
    ):
        """Test that no SQLAlchemy relationship warnings occur when creating and accessing PrivacyRequest attachment relationships."""
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            # Create attachment and reference using fixtures
            attachment = create_attachment(b"test contents")
            attachment_ref = create_attachment_reference(
                privacy_request.id,
                attachment.id,
                AttachmentReferenceType.privacy_request,
            )
            db.refresh(privacy_request)
            db.refresh(attachment)

            # Test accessing relationships in various ways
            assert len(privacy_request.attachments) == 1

            # Query references directly
            attachment_refs = (
                db.query(AttachmentReference)
                .filter(
                    AttachmentReference.reference_id == privacy_request.id,
                    AttachmentReference.reference_type
                    == AttachmentReferenceType.privacy_request,
                )
                .all()
            )
            assert len(attachment_refs) == 1

            # Verify no SQLAlchemy relationship warnings were emitted
            sqlalchemy_warnings = [
                w for w in warning_list if issubclass(w.category, sa_exc.SAWarning)
            ]
            assert (
                len(sqlalchemy_warnings) == 0
            ), f"SQLAlchemy warnings found: {[str(w.message) for w in sqlalchemy_warnings]}"

            # Cleanup
            if db.query(AttachmentReference).filter_by(id=attachment_ref.id).first():
                attachment_ref.delete(db)
                db.commit()

            # Refresh the session to ensure clean state
            db.expire_all()


class TestPrivacyRequestComments:
    @pytest.fixture
    def create_comment(self, db, comment_data):
        """Fixture to create a single comment"""

        def _create_comment(contents: str = "test comment"):
            comment_data["comment_text"] = contents
            return Comment.create(db=db, data=comment_data)

        return _create_comment

    @pytest.fixture
    def create_comment_reference(self, db):
        """Fixture to create a comment reference"""

        def _create_reference(reference_id: str, comment_id: str, reference_type: str):
            return CommentReference.create(
                db,
                data={
                    "reference_id": reference_id,
                    "comment_id": comment_id,
                    "reference_type": reference_type,
                },
            )

        return _create_reference

    @pytest.fixture
    def cleanup_comments(self, db):
        """Fixture to clean up comments after tests"""

        def _cleanup(comments):
            for comment in comments:
                comment.delete(db)
            db.commit()

        return _cleanup

    def test_retrieve_comments_from_privacy_request(
        self,
        db,
        create_comment,
        create_comment_reference,
        cleanup_comments,
        privacy_request,
    ):
        # Create Comments
        comment1 = create_comment("test comment 1")
        comment2 = create_comment("test comment 2")
        comment3 = create_comment("test comment 3")

        # Associate Comments with the PrivacyRequest
        for comment in [comment1, comment2, comment3]:
            create_comment_reference(
                privacy_request.id,
                comment.id,
                CommentReferenceType.privacy_request,
            )

        # Verify that comments can be retrieved
        retrieved_request = (
            db.query(PrivacyRequest).filter_by(id=privacy_request.id).first()
        )
        comments = retrieved_request.comments

        assert len(comments) == 3
        # Verify that the comments are in the correct order
        assert comments[0].id == comment1.id
        assert comments[1].id == comment2.id
        assert comments[2].id == comment3.id

        # Verify deleting the privacy request deletes the comments.
        privacy_request.delete(db)
        db.commit()
        assert Comment.get(db, object_id=comment1.id) is None
        assert Comment.get(db, object_id=comment2.id) is None
        assert Comment.get(db, object_id=comment3.id) is None

    def test_privacy_request_get_comment_by_id(
        self, db, create_comment, create_comment_reference, privacy_request
    ):
        # Create and associate comment with the PrivacyRequest
        comment = create_comment("test comment")
        create_comment_reference(
            privacy_request.id,
            comment.id,
            CommentReferenceType.privacy_request,
        )

        # Verify that comment can be retrieved
        retrieved_comment = privacy_request.get_comment_by_id(db, comment.id)
        assert retrieved_comment.id == comment.id

    def test_privacy_request_comment_relationship_warnings(
        self, db, privacy_request, create_comment, create_comment_reference
    ):
        """Test that no SQLAlchemy relationship warnings occur when creating and accessing PrivacyRequest comment relationships."""
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            # Create comment and reference using fixtures
            comment = create_comment("test comment")
            comment_ref = create_comment_reference(
                privacy_request.id,
                comment.id,
                CommentReferenceType.privacy_request,
            )
            db.refresh(privacy_request)
            db.refresh(comment)

            # Test accessing relationships in various ways
            assert len(privacy_request.comments) == 1

            # Query references directly
            comment_refs = (
                db.query(CommentReference)
                .filter(
                    CommentReference.reference_id == privacy_request.id,
                    CommentReference.reference_type
                    == CommentReferenceType.privacy_request,
                )
                .all()
            )
            assert len(comment_refs) == 1

            # Verify no SQLAlchemy relationship warnings were emitted
            sqlalchemy_warnings = [
                w for w in warning_list if issubclass(w.category, sa_exc.SAWarning)
            ]
            assert (
                len(sqlalchemy_warnings) == 0
            ), f"SQLAlchemy warnings found: {[str(w.message) for w in sqlalchemy_warnings]}"

            # Cleanup
            if db.query(CommentReference).filter_by(id=comment_ref.id).first():
                comment_ref.delete(db)
                db.commit()

            # Refresh the session to ensure clean state
            db.expire_all()


class TestCancelCeleryTasks:
    """Test the cancel_celery_tasks method on PrivacyRequest."""

    @pytest.fixture
    def privacy_request_with_cached_tasks(self, db, policy):
        """Create a privacy request with cached task IDs."""
        from fides.api.models.privacy_request import PrivacyRequest, RequestTask
        from fides.api.models.worker_task import ExecutionLogStatus
        from fides.api.schemas.policy import ActionType
        from fides.api.util.cache import cache_task_tracking_key

        # Create the privacy request
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid4())}",
                "started_processing_at": datetime.utcnow(),
                "requested_at": datetime.utcnow() - timedelta(days=1),
                "status": PrivacyRequestStatus.in_processing,
                "origin": "https://example.com/testing",
                "policy_id": policy.id,
                "client_id": policy.client_id,
            },
        )

        # Create request tasks
        request_task_1 = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.in_processing,
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:customer",
                "dataset_name": "test_dataset",
                "collection_name": "customer",
                "upstream_tasks": [],
                "downstream_tasks": [],
            },
        )

        request_task_2 = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.in_processing,
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:orders",
                "dataset_name": "test_dataset",
                "collection_name": "orders",
                "upstream_tasks": [],
                "downstream_tasks": [],
            },
        )

        # Cache task IDs
        cache_task_tracking_key(privacy_request.id, "main_task_abc123")
        cache_task_tracking_key(request_task_1.id, "sub_task_def456")
        cache_task_tracking_key(request_task_2.id, "sub_task_ghi789")

        yield privacy_request

        # Clean up
        request_task_1.delete(db)
        request_task_2.delete(db)
        privacy_request.delete(db)

    @pytest.fixture
    def privacy_request_no_cached_tasks(self, db, policy):
        """Create a privacy request with no cached task IDs."""
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid4())}",
                "started_processing_at": datetime.utcnow(),
                "requested_at": datetime.utcnow() - timedelta(days=1),
                "status": PrivacyRequestStatus.in_processing,
                "origin": "https://example.com/testing",
                "policy_id": policy.id,
                "client_id": policy.client_id,
            },
        )

        yield privacy_request

        # Clean up
        privacy_request.delete(db)

    @pytest.mark.unit
    def test_cancel_celery_tasks_with_main_and_sub_tasks(self, privacy_request_with_cached_tasks):
        """Test canceling celery tasks when main and sub-tasks exist."""
        from unittest import mock
        from fides.api.tasks import celery_app

        privacy_request = privacy_request_with_cached_tasks

        with mock.patch.object(celery_app.control, 'revoke') as mock_revoke:
            privacy_request.cancel_celery_tasks()

            # Should revoke all 3 tasks: main + 2 sub-tasks
            assert mock_revoke.call_count == 3

            # Verify the task IDs that were revoked
            revoked_task_ids = [call.args[0] for call in mock_revoke.call_args_list]
            assert "main_task_abc123" in revoked_task_ids
            assert "sub_task_def456" in revoked_task_ids
            assert "sub_task_ghi789" in revoked_task_ids

            # Verify terminate=False for graceful shutdown
            for call in mock_revoke.call_args_list:
                assert call.kwargs.get('terminate') is False

    @pytest.mark.unit
    def test_cancel_celery_tasks_with_only_main_task(self, privacy_request_no_cached_tasks):
        """Test canceling celery tasks when only main task exists."""
        from unittest import mock
        from fides.api.tasks import celery_app
        from fides.api.util.cache import cache_task_tracking_key

        privacy_request = privacy_request_no_cached_tasks

        # Cache only the main task
        cache_task_tracking_key(privacy_request.id, "only_main_task_123")

        with mock.patch.object(celery_app.control, 'revoke') as mock_revoke:
            privacy_request.cancel_celery_tasks()

            # Should revoke only 1 task
            assert mock_revoke.call_count == 1
            mock_revoke.assert_called_with("only_main_task_123", terminate=False)

    @pytest.mark.unit
    def test_cancel_celery_tasks_no_cached_tasks(self, privacy_request_no_cached_tasks):
        """Test canceling celery tasks when no cached tasks exist."""
        from unittest import mock
        from fides.api.tasks import celery_app

        privacy_request = privacy_request_no_cached_tasks

        with mock.patch.object(celery_app.control, 'revoke') as mock_revoke:
            privacy_request.cancel_celery_tasks()

            # Should not revoke any tasks
            assert mock_revoke.call_count == 0

    @pytest.mark.unit
    def test_cancel_celery_tasks_with_revoke_failures(self, privacy_request_with_cached_tasks):
        """Test that revoke failures are handled gracefully."""
        from unittest import mock
        from fides.api.tasks import celery_app

        privacy_request = privacy_request_with_cached_tasks

        # Mock revoke to raise exception for specific task
        def side_effect(task_id, **kwargs):
            if task_id == "main_task_abc123":
                raise Exception("Revoke failed")
            return None

        with mock.patch.object(celery_app.control, 'revoke', side_effect=side_effect):
            with mock.patch("fides.api.models.privacy_request.privacy_request.logger") as mock_logger:
                privacy_request.cancel_celery_tasks()

                # Should log warning for failed revoke
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "Failed to revoke task main_task_abc123" in warning_call

    @pytest.mark.unit
    def test_cancel_celery_tasks_logging(self, privacy_request_with_cached_tasks):
        """Test that cancel_celery_tasks logs task revocations."""
        from unittest import mock
        from fides.api.tasks import celery_app

        privacy_request = privacy_request_with_cached_tasks

        with mock.patch.object(celery_app.control, 'revoke'):
            with mock.patch("fides.api.models.privacy_request.privacy_request.logger") as mock_logger:
                privacy_request.cancel_celery_tasks()

                # Should log info for each revoked task
                assert mock_logger.info.call_count == 3

                # Verify logging messages contain task IDs and privacy request ID
                info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
                for call in info_calls:
                    assert "Revoking task" in call
                    assert str(privacy_request.id) in call

    @pytest.mark.unit
    def test_get_request_task_celery_task_ids(self, privacy_request_with_cached_tasks):
        """Test that get_request_task_celery_task_ids returns correct task IDs."""
        privacy_request = privacy_request_with_cached_tasks

        task_ids = privacy_request.get_request_task_celery_task_ids()

        # Should return the 2 sub-task IDs
        assert len(task_ids) == 2
        assert "sub_task_def456" in task_ids
        assert "sub_task_ghi789" in task_ids

    @pytest.mark.unit
    def test_get_request_task_celery_task_ids_no_tasks(self, privacy_request_no_cached_tasks):
        """Test that get_request_task_celery_task_ids returns empty list when no tasks exist."""
        privacy_request = privacy_request_no_cached_tasks

        task_ids = privacy_request.get_request_task_celery_task_ids()

        # Should return empty list
        assert task_ids == []

    @pytest.mark.unit
    def test_cancel_celery_tasks_integration_with_cancel_processing(self, privacy_request_no_cached_tasks):
        """Test that cancel_celery_tasks is called when cancel_processing is invoked."""
        from unittest import mock

        privacy_request = privacy_request_no_cached_tasks

        with mock.patch.object(privacy_request, 'cancel_celery_tasks') as mock_cancel_tasks:
            with mock.patch.object(privacy_request, 'save'):
                privacy_request.cancel_processing(mock.Mock(), "Test cancellation")

                # cancel_celery_tasks should be called as part of cancel_processing
                mock_cancel_tasks.assert_called_once()
