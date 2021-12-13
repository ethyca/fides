import pytest
import requests_mock
from datetime import datetime, timedelta
from pydantic import ValidationError
from typing import List
from uuid import uuid4

from sqlalchemy.orm import Session

from fidesops.common_exceptions import ClientUnsuccessfulException, PrivacyRequestPaused
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.util.cache import FidesopsRedis, get_identity_cache_key


def test_privacy_request(
    db: Session, policy: Policy, privacy_request: PrivacyRequest
) -> None:
    from_db = PrivacyRequest.get(db=db, id=privacy_request.id)
    assert from_db is not None
    assert from_db.id is not None
    assert from_db.policy.id == policy.id
    assert from_db.client_id == policy.client_id


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
    from_db = PrivacyRequest.get(db, id=privacy_request.id)
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
    from_db = PrivacyRequest.get(db=db, id=privacy_request.id)
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
    from_db = PrivacyRequest.get(db=db, id=privacy_request.id)
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
    identity = PrivacyRequestIdentity(**identity_kwargs)
    privacy_request.cache_identity(identity)
    key = get_identity_cache_key(
        privacy_request_id=privacy_request.id,
        identity_attribute=identity_attribute,
    )
    assert cache.get(key) == identity_value
    privacy_request.delete(db)
    from_db = PrivacyRequest.get(db=db, id=privacy_request.id)
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
        identity = PrivacyRequestIdentity(email="customer-1@example.com")
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
        identity = PrivacyRequestIdentity(email="customer-1@example.com")
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
        identity = PrivacyRequestIdentity(email="customer-1@example.com")
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
        identity = PrivacyRequestIdentity(email="customer-1@example.com")
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
        identity = PrivacyRequestIdentity(email="customer-1@example.com")
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
        identity = PrivacyRequestIdentity(email="customer-1@example.com")
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
