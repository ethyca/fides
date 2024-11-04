import ast
import csv
import io
import json
from datetime import datetime, timedelta
from random import randint
from typing import List
from unittest import mock
from uuid import uuid4

import pytest
from dateutil.parser import parse
from fastapi import HTTPException, status
from fastapi_pagination import Params
from starlette.testclient import TestClient

from fides.api.api.v1.endpoints.privacy_request_endpoints import (
    EMBEDDED_EXECUTION_LOG_LIMIT,
    validate_manual_input,
)
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
)
from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import CurrentStep, Policy
from fides.api.models.pre_approval_webhook import PreApprovalWebhookReply
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestError,
    PrivacyRequestNotifications,
    PrivacyRequestSource,
    PrivacyRequestStatus,
    generate_request_task_callback_jwe,
)
from fides.api.oauth.jwt import generate_jwe
from fides.api.oauth.roles import APPROVER, OWNER, VIEWER
from fides.api.schemas.dataset import DryRunDatasetResponse
from fides.api.schemas.masking.masking_secrets import SecretType
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceType,
    RequestReceiptBodyParams,
    RequestReviewDenyBodyParams,
    SubjectIdentityVerificationBodyParams,
)
from fides.api.schemas.policy import ActionType, PolicyResponse
from fides.api.schemas.redis_cache import Identity, LabeledIdentity
from fides.api.task.graph_runners import access_runner
from fides.api.tasks import MESSAGING_QUEUE_NAME
from fides.api.util.cache import get_encryption_cache_key, get_masking_secret_cache_key
from fides.api.util.fuzzy_search_utils import (
    get_should_refresh_automaton,
    manually_reset_automaton,
    remove_refresh_automaton_signal,
    set_automaton_cache_signal,
)
from fides.common.api.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_READ_ACCESS_RESULTS,
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_TRANSFER,
    PRIVACY_REQUEST_UPLOAD_DATA,
    PRIVACY_REQUEST_VIEW_DATA,
    STORAGE_CREATE_OR_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_DATASETS,
    PRIVACY_REQUEST_ACCESS_RESULTS,
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_AUTHENTICATED,
    PRIVACY_REQUEST_BULK_RETRY,
    PRIVACY_REQUEST_BULK_SOFT_DELETE,
    PRIVACY_REQUEST_DENY,
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT,
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT,
    PRIVACY_REQUEST_NOTIFICATIONS,
    PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE,
    PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE,
    PRIVACY_REQUEST_REQUEUE,
    PRIVACY_REQUEST_RESUME,
    PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT,
    PRIVACY_REQUEST_RETRY,
    PRIVACY_REQUEST_SEARCH,
    PRIVACY_REQUEST_SOFT_DELETE,
    PRIVACY_REQUEST_TRANSFER_TO_PARENT,
    PRIVACY_REQUEST_VERIFY_IDENTITY,
    PRIVACY_REQUESTS,
    REQUEST_PREVIEW,
    REQUEST_TASK_CALLBACK,
    REQUEST_TASKS,
    V1_URL_PREFIX,
)
from fides.config import CONFIG
from tests.conftest import generate_auth_header_for_user, generate_role_header_for_user

page_size = Params().size


def stringify_date(log_date: datetime) -> str:
    return log_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class TestCreatePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_create_privacy_request(
        self,
        mock_dispatch_message,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        print(resp.json())
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        pr.delete(db=db)
        assert run_access_request_mock.called
        assert not mock_dispatch_message.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_stores_identities(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_PHONE_NUMBER = "+12345678910"
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {
                    "email": TEST_EMAIL,
                    "phone_number": TEST_PHONE_NUMBER,
                },
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        assert persisted_identity.phone_number == TEST_PHONE_NUMBER
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_stores_custom_identities(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_PHONE_NUMBER = "+12345678910"
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {
                    "email": TEST_EMAIL,
                    "phone_number": TEST_PHONE_NUMBER,
                    "loyalty_id": {"label": "Loyalty ID", "value": "CH-1"},
                },
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.get_persisted_identity() == Identity(
            email=TEST_EMAIL,
            phone_number=TEST_PHONE_NUMBER,
            loyalty_id=LabeledIdentity(label="Loyalty ID", value="CH-1"),
        )
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_stores_custom_fields(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_CUSTOM_FIELDS = {
            "first_name": {"label": "First name", "value": "John"},
            "last_name": {"label": "Last name", "value": "Doe"},
        }
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {
                    "email": TEST_EMAIL,
                },
                "custom_privacy_request_fields": TEST_CUSTOM_FIELDS,
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        persisted_custom_privacy_request_fields = (
            pr.get_persisted_custom_privacy_request_fields()
        )
        assert persisted_custom_privacy_request_fields == TEST_CUSTOM_FIELDS
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_stores_multivalue_custom_fields(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_CUSTOM_FIELDS = {
            "first_name": {"label": "First name", "value": "John"},
            "subscriber_ids": {"label": "Subscriber IDs", "value": ["123", "456"]},
            "account_ids": {"label": "Account IDs", "value": [123, 456]},
        }
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {
                    "email": TEST_EMAIL,
                },
                "custom_privacy_request_fields": TEST_CUSTOM_FIELDS,
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        persisted_custom_privacy_request_fields = (
            pr.get_persisted_custom_privacy_request_fields()
        )
        assert persisted_custom_privacy_request_fields == TEST_CUSTOM_FIELDS

        for field in pr.custom_fields:
            if isinstance(field.encrypted_value["value"], list):
                # We don't hash list fields
                assert field.hashed_value is None
            else:
                assert field.hashed_value is not None
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_links_existing_custom_fields(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
        allow_custom_privacy_request_field_collection_enabled,
        provided_identity_and_consent_request_with_custom_fields,
    ):
        CONSENT_REQUEST_ID = provided_identity_and_consent_request_with_custom_fields.id
        TEST_EMAIL = "test@example.com"
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {
                    "email": TEST_EMAIL,
                },
                "consent_request_id": CONSENT_REQUEST_ID,
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        for custom_field in pr.custom_fields:
            assert custom_field.consent_request_id == CONSENT_REQUEST_ID
            assert custom_field.privacy_request_id == pr.id
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_create_privacy_request_require_manual_approval(
        self,
        mock_trigger_pre_approval_webhook,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
        require_manual_request_approval,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["status"] == "pending"
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        pr.delete(db=db)
        assert not run_access_request_mock.called
        assert not mock_trigger_pre_approval_webhook.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_create_privacy_request_require_manual_approval_with_pre_approval_webhooks(
        self,
        mock_trigger_pre_approval_webhook,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
        require_manual_request_approval,
        pre_approval_webhooks,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["status"] == "pending"
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        pr.delete(db=db)
        assert not run_access_request_mock.called
        assert mock_trigger_pre_approval_webhook.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_create_privacy_request_not_require_manual_approval_with_pre_approval_webhooks(
        self,
        mock_trigger_pre_approval_webhook,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
        pre_approval_webhooks,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["status"] == "pending"
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        pr.delete(db=db)
        assert run_access_request_mock.called
        assert not mock_trigger_pre_approval_webhook.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_with_masking_configuration(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        erasure_policy_string_rewrite,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": erasure_policy_string_rewrite.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.access_runner"
    )
    def test_create_privacy_request_limit_exceeded(
        self,
        _,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        payload = []
        for i in range(0, 51):
            payload.append(
                {
                    "requested_at": "2021-08-30T16:09:37.359Z",
                    "policy_key": policy.key,
                    "identity": {"email": "ftest{i}@example.com"},
                },
            )

        response = api_client.post(url, json=payload)

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "List should have at most 50 items after validation, not 51"
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_starts_processing(
        self,
        run_privacy_request_mock,
        url,
        api_client: TestClient,
        db,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert run_privacy_request_mock.called
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        pr.delete(db=db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_with_external_id(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        external_id = "ext_some-uuid-here-1234"
        data = [
            {
                "external_id": external_id,
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["external_id"] == external_id
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.external_id == external_id
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_caches_identity(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        identity = {"email": "test@example.com"}
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": identity,
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.get_cached_identity_data() == identity
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_caches_masking_secrets(
        self,
        run_erasure_request_mock,
        url,
        db,
        api_client: TestClient,
        erasure_policy_aes,
        cache,
    ):
        identity = {"email": "test@example.com"}
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": erasure_policy_aes.key,
                "identity": identity,
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        secret_key = get_masking_secret_cache_key(
            privacy_request_id=pr.id,
            masking_strategy="aes_encrypt",
            secret_type=SecretType.key,
        )
        assert cache.get_encoded_by_key(secret_key) is not None
        pr.delete(db=db)
        assert run_erasure_request_mock.called

    def test_create_privacy_request_invalid_encryption_values(
        self, url, db, api_client: TestClient, policy, cache
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
                "encryption_key": "test",
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 422
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, Encryption key must be 16 bytes long"
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_caches_encryption_keys(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
        cache,
    ):
        identity = {"email": "test@example.com"}
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": identity,
                "encryption_key": "test--encryption",
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        encryption_key = get_encryption_cache_key(
            privacy_request_id=pr.id,
            encryption_attr="key",
        )
        assert cache.get(encryption_key) == "test--encryption"

        pr.delete(db=db)
        assert run_access_request_mock.called

    def test_create_privacy_request_no_identities(
        self,
        url,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 0
        response_data = resp.json()["failed"]
        assert len(response_data) == 1

    def test_create_privacy_request_registers_async_task(
        self,
        db,
        url,
        api_client,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.get_cached_task_id() is not None
        assert pr.get_async_execution_task() is not None
        pr.delete(db=db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_creates_system_audit_log(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        response_data = resp.json()["succeeded"][0]
        approval_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == response_data["id"])
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()
        assert approval_audit_log is not None
        assert approval_audit_log.user_id == "system"

        approval_audit_log.delete(db=db)
        pr = PrivacyRequest.get(db=db, object_id=response_data["id"])
        pr.delete(db=db)

    @pytest.mark.usefixtures("messaging_config")
    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_error_notification(
        self,
        mailgun_dispatcher_mock,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_PHONE_NUMBER = "+12345678910"
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {
                    "email": TEST_EMAIL,
                    "phone_number": TEST_PHONE_NUMBER,
                },
            }
        ]

        PrivacyRequestNotifications.create(
            db=db,
            data={
                "email": "some@email.com, another@email.com",
                "notify_after_failures": 1,
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

        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        assert persisted_identity.phone_number == TEST_PHONE_NUMBER

        sent_errors = PrivacyRequestError.filter(
            db=db, conditions=(PrivacyRequestError.message_sent.is_(True))
        ).all()

        assert len(sent_errors) == 1

        assert run_access_request_mock.called
        assert mailgun_dispatcher_mock.called


class TestGetPrivacyRequests:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    def test_get_privacy_requests_unauthenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_privacy_requests_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_privacy_requests_approver_role(
        self, api_client: TestClient, generate_role_header, url
    ):
        auth_header = generate_role_header(roles=[APPROVER])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

    def test_conflicting_query_params(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url
            + f"?completed_lt=2021-01-01T00:00:00.000Z&errored_gt=2021-01-02T00:00:00.000Z",
            headers=auth_header,
        )
        assert 400 == response.status_code

    def test_get_privacy_requests_displays_reviewer(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        privacy_request,
        user,
        postgres_execution_log,
        mongo_execution_log,
    ):
        privacy_request.reviewer = user
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?request_id={privacy_request.id}", headers=auth_header
        )
        assert 200 == response.status_code

        reviewer = response.json()["items"][0]["reviewer"]
        assert reviewer
        assert user.id == reviewer["id"]
        assert user.username == reviewer["username"]
        privacy_request.delete(db)

    def test_get_privacy_requests_accept_datetime(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        privacy_request,
        postgres_execution_log,
        mongo_execution_log,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        for date_format in [
            "%Y-%m-%dT00:00:00.000Z",
            # "%Y-%m-%d",
        ]:
            date_input = privacy_request.created_at.strftime(date_format)
            response = api_client.get(
                url + f"?created_gt={date_input}",
                headers=auth_header,
            )

            assert 200 == response.status_code

    def test_get_privacy_requests_by_id(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        postgres_execution_log,
        mongo_execution_log,
        db,
    ):
        privacy_request.due_date = None
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?request_id={privacy_request.id}", headers=auth_header
        )
        assert 200 == response.status_code

        expected_resp = {
            "items": [
                {
                    "id": privacy_request.id,
                    "created_at": stringify_date(privacy_request.created_at),
                    "custom_privacy_request_fields": None,
                    "custom_privacy_request_fields_approved_at": None,
                    "custom_privacy_request_fields_approved_by": None,
                    "days_left": None,
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "identity_verified_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "source": None,
                    "policy": {
                        "drp_action": None,
                        "execution_timeframe": 7,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.model_dump(mode="json")
                            for rule in PolicyResponse.model_validate(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "action_required_details": None,
                    "resume_endpoint": None,
                    "deleted_at": None,
                    "deleted_by": None,
                }
            ],
            "total": 1,
            "page": 1,
            "pages": 1,
            "size": page_size,
        }

        resp = response.json()
        assert resp == expected_resp

    def test_get_privacy_requests_by_partial_id(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        postgres_execution_log,
        mongo_execution_log,
        db,
    ):
        privacy_request.due_date = None
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?request_id={privacy_request.id[:5]}", headers=auth_header
        )
        assert 200 == response.status_code

        expected_resp = {
            "items": [
                {
                    "id": privacy_request.id,
                    "created_at": stringify_date(privacy_request.created_at),
                    "custom_privacy_request_fields": None,
                    "custom_privacy_request_fields_approved_at": None,
                    "custom_privacy_request_fields_approved_by": None,
                    "days_left": None,
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "identity_verified_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "source": None,
                    "policy": {
                        "execution_timeframe": 7,
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.model_dump(mode="json")
                            for rule in PolicyResponse.model_validate(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "action_required_details": None,
                    "resume_endpoint": None,
                    "deleted_at": None,
                    "deleted_by": None,
                }
            ],
            "total": 1,
            "page": 1,
            "pages": 1,
            "size": page_size,
        }

        resp = response.json()
        assert resp == expected_resp

    def test_get_privacy_requests_with_identity(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?status=complete&include_identities=true", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id
        assert resp["items"][0][
            "identity"
        ] == succeeded_privacy_request.get_persisted_identity().labeled_dict(
            include_default_labels=True
        )

        assert resp["items"][0]["policy"]["key"] == privacy_request.policy.key
        assert resp["items"][0]["policy"]["name"] == privacy_request.policy.name

        # Now test the identities are omitted if not explicitly requested
        response = api_client.get(url + f"?status=complete", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id
        assert resp["items"][0].get("identity") is None

        response = api_client.get(
            url + f"?status=complete&include_identities=false", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id
        assert resp["items"][0].get("identity") is None

    def test_get_privacy_requests_with_custom_fields(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request_with_custom_fields,
    ):
        privacy_request = privacy_request_with_custom_fields
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?include_custom_privacy_request_fields=true", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id
        assert (
            resp["items"][0]["custom_privacy_request_fields"]
            == privacy_request.get_persisted_custom_privacy_request_fields()
        )

        assert resp["items"][0]["policy"]["key"] == privacy_request.policy.key
        assert resp["items"][0]["policy"]["name"] == privacy_request.policy.name

        # Now test the custom fields are omitted if not explicitly requested
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id
        assert resp["items"][0].get("custom_privacy_request_fields") is None

        response = api_client.get(
            url + f"?include_custom_privacy_request_fields=false", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id
        assert resp["items"][0].get("custom_privacy_request_fields") is None

    def test_filter_privacy_requests_by_action(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        executable_consent_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url + f"?action_type=access", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1

        response = api_client.get(url + f"?action_type=consent", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1

        response = api_client.get(url + f"?action_type=erasure", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

    def test_filter_privacy_requests_by_status(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url + f"?status=complete", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id

        response = api_client.get(url + f"?status=error", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == failed_privacy_request.id

    def test_filter_privacy_requests_include_deleted_requests(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?include_deleted_requests=true", headers=auth_header
        )

        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 2

        # Check that both the not-deleted and the soft-deleted privacy requests are returned
        assert (
            len([item for item in resp["items"] if item["id"] == privacy_request.id])
            == 1
        )
        assert (
            len(
                [
                    item
                    for item in resp["items"]
                    if item["id"] == soft_deleted_privacy_request.id
                ]
            )
            == 1
        )

    def test_filter_privacy_requests_exclude_deleted_requests(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?include_deleted_requests=false", headers=auth_header
        )

        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 1

        assert resp["items"][0]["id"] == privacy_request.id

    def test_filter_privacy_requests_excludes_deleted_requests_by_default(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        resp = response.json()
        assert len(resp["items"]) == 1

        assert resp["items"][0]["id"] == privacy_request.id

    def test_filter_privacy_request_by_multiple_statuses(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?status=complete&status=error", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 2
        assert resp["items"][0]["id"] == failed_privacy_request.id
        assert resp["items"][1]["id"] == succeeded_privacy_request.id

    def test_filter_privacy_requests_by_internal_id(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
                "id": "test_internal_id_1",
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        privacy_request = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?request_id={privacy_request.id}",
            headers=auth_header,
        )
        assert response.status_code == status.HTTP_200_OK
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    def test_filter_privacy_requests_by_identity_no_request_id(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
    ):
        TEST_EMAIL = "test-12345678910@example.com"
        privacy_request.persist_identity(
            db=db,
            identity=Identity(
                email=TEST_EMAIL,
            ),
        )
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?identity={TEST_EMAIL}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    # FIXME: don't skip this
    @pytest.mark.skip("skip until PROD-2811 is done")
    def test_fuzzy_search_bulk_privacy_requests_cache_exists(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
        privacy_request_awaiting_consent_email_send,
        privacy_request_awaiting_erasure_email_send,
        privacy_request_requires_input,
        bulk_privacy_requests_with_various_identities,
    ):
        # Override deterministic identities on specific privacy request for testing
        TEST_EMAIL_1 = "test-happy@example.com"
        TEST_PHONE_1 = "+11232342345"
        privacy_request.persist_identity(
            db=db,
            identity=Identity(email=TEST_EMAIL_1, phone_number=TEST_PHONE_1),
        )

        TEST_EMAIL_2 = "test-sad@example.com"
        TEST_PHONE_2 = "+11224923487"
        privacy_request_awaiting_consent_email_send.persist_identity(
            db=db,
            identity=Identity(email=TEST_EMAIL_2, phone_number=TEST_PHONE_2),
        )

        TEST_EMAIL_3 = "someone-nice@example.com"
        TEST_PHONE_3 = "+7361398443"
        privacy_request_awaiting_erasure_email_send.persist_identity(
            db=db,
            identity=Identity(email=TEST_EMAIL_3, phone_number=TEST_PHONE_3),
        )

        TEST_EMAIL_4 = "icedlatte123@email.com"
        TEST_PHONE_4 = "+2398984579"
        privacy_request_requires_input.persist_identity(
            db=db,
            identity=Identity(email=TEST_EMAIL_4, phone_number=TEST_PHONE_4),
        )
        # Persisting identities automatically adds to Automaton and sets cache signal,
        # so at this point we expect cache to exist
        assert get_should_refresh_automaton() is False

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # Test two matches on email
        FUZZY_SEARCH_STR_1 = "te"
        response = api_client.get(
            url + f"?fuzzy_search_str={FUZZY_SEARCH_STR_1}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert privacy_request.id in [result["id"] for result in resp["items"]]
        assert privacy_request_awaiting_consent_email_send.id in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_awaiting_erasure_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_requires_input.id not in [
            result["id"] for result in resp["items"]
        ]

        # Test one on email prefix
        FUZZY_SEARCH_STR_1 = "test-happy@exam"
        response = api_client.get(
            url + f"?fuzzy_search_str={FUZZY_SEARCH_STR_1}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert privacy_request.id in [result["id"] for result in resp["items"]]
        assert privacy_request_awaiting_consent_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_awaiting_erasure_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_requires_input.id not in [
            result["id"] for result in resp["items"]
        ]

        # Test one match on email full
        FUZZY_SEARCH_STR_1 = "test-happy@example.com"
        response = api_client.get(
            url + f"?fuzzy_search_str={FUZZY_SEARCH_STR_1}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert privacy_request.id in [result["id"] for result in resp["items"]]
        assert privacy_request_awaiting_consent_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_awaiting_erasure_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_requires_input.id not in [
            result["id"] for result in resp["items"]
        ]

        # Test one match on phone number
        FUZZY_SEARCH_STR_1 = "+11232"
        response = api_client.get(
            url + f"?fuzzy_search_str={FUZZY_SEARCH_STR_1}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert privacy_request.id in [result["id"] for result in resp["items"]]
        assert privacy_request_awaiting_consent_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_awaiting_erasure_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_requires_input.id not in [
            result["id"] for result in resp["items"]
        ]

        # Test partial match on request id
        FUZZY_SEARCH_STR_1 = privacy_request.id[:5]  # use first 5 chars
        response = api_client.get(
            url + f"?fuzzy_search_str={FUZZY_SEARCH_STR_1}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert privacy_request.id in [result["id"] for result in resp["items"]]
        assert privacy_request_awaiting_consent_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_awaiting_erasure_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_requires_input.id not in [
            result["id"] for result in resp["items"]
        ]

        # Test no match on email
        FUZZY_SEARCH_STR_1 = "happy"  # this is invalid because it's not the beginning of the given email identity
        response = api_client.get(
            url + f"?fuzzy_search_str={FUZZY_SEARCH_STR_1}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert privacy_request.id not in [result["id"] for result in resp["items"]]
        assert privacy_request_awaiting_consent_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_awaiting_erasure_email_send.id not in [
            result["id"] for result in resp["items"]
        ]
        assert privacy_request_requires_input.id not in [
            result["id"] for result in resp["items"]
        ]

    # FIXME: don't skip this
    @pytest.mark.skip("skip until PROD-2811 is done")
    def test_fuzzy_search_privacy_requests_no_cache(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
    ):

        # Override deterministic identities on a given privacy request for testing
        TEST_EMAIL = "test-happy@example.com"
        TEST_PHONE = "+11232342345"
        privacy_request.persist_identity(
            db=db,
            identity=Identity(email=TEST_EMAIL, phone_number=TEST_PHONE),
        )

        # Manually remove cache signal and set global _automaton to None
        remove_refresh_automaton_signal()
        manually_reset_automaton()

        assert get_should_refresh_automaton() is True

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        # test partial prefix match on email
        FUZZY_SEARCH_STR_1 = "test"
        response = api_client.get(
            url + f"?fuzzy_search_str={FUZZY_SEARCH_STR_1}",
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()
        assert privacy_request.id in [result["id"] for result in resp["items"]]

        # Test that the privacy request identities are automatically put in the cache as a side-effect of fuzzy-search
        identities = (
            privacy_request.retrieve_decrypted_identities_from_cache_by_privacy_request()
        )
        assert identities["email"] == TEST_EMAIL
        assert identities["phone_number"] == TEST_PHONE

    def test_filter_privacy_requests_by_external_id(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?external_id={succeeded_privacy_request.id}", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        privacy_request.external_id = "test_external_id_1"
        privacy_request.save(db)

        response = api_client.get(
            url + f"?external_id=test_external_id_1", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    def test_filter_privacy_requests_by_created(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?created_lt=2019-01-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.get(
            url + f"?created_gt=2019-01-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 3
        assert resp["items"][0]["id"] == failed_privacy_request.id
        assert resp["items"][1]["id"] == succeeded_privacy_request.id
        assert resp["items"][2]["id"] == privacy_request.id

    def test_filter_privacy_requests_by_conflicting_date_fields(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        # Search for privacy requests after 2019, but before 2018. This should return an error.
        start = "2019-01-01"
        end = "2018-01-01"
        response = api_client.get(
            url + f"?created_gt={start}T00:00:00.000Z&created_lt={end}T00:00:00.000Z",
            headers=auth_header,
        )
        assert 400 == response.status_code
        assert (
            response.json()["detail"]
            == f"Value specified for created_lt: {end} 00:00:00+00:00 must be after created_gt: {start} 00:00:00+00:00."
        )

    def test_filter_privacy_requests_by_started(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?started_lt=2021-05-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 2
        assert resp["items"][0]["id"] == failed_privacy_request.id
        assert resp["items"][1]["id"] == privacy_request.id

        response = api_client.get(
            url + f"?started_gt=2021-05-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id

    def test_filter_privacy_requests_by_completed(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?completed_lt=2021-10-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.get(
            url + f"?completed_gt=2021-10-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id

    def test_filter_privacy_requests_by_errored(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url + f"?errored_lt=2021-01-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.get(
            url + f"?errored_gt=2021-01-01T00:00:00.000Z", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == failed_privacy_request.id

    def test_verbose_privacy_requests(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request: PrivacyRequest,
        audit_log,
        postgres_execution_log,
        second_postgres_execution_log,
        mongo_execution_log,
        async_execution_log,
        url,
        db,
    ):
        """Test privacy requests endpoint with verbose query param to show execution logs"""
        privacy_request.due_date = None
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url + f"?verbose=True", headers=auth_header)
        assert 200 == response.status_code

        resp = response.json()
        assert (
            postgres_execution_log.updated_at < second_postgres_execution_log.updated_at
        )
        expected_resp = {
            "items": [
                {
                    "id": privacy_request.id,
                    "created_at": stringify_date(privacy_request.created_at),
                    "custom_privacy_request_fields": None,
                    "custom_privacy_request_fields_approved_at": None,
                    "custom_privacy_request_fields_approved_by": None,
                    "days_left": None,
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "identity_verified_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "source": None,
                    "policy": {
                        "execution_timeframe": 7,
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.model_dump(mode="json")
                            for rule in PolicyResponse.model_validate(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "action_required_details": None,
                    "resume_endpoint": None,
                    "deleted_at": None,
                    "deleted_by": None,
                    "results": {
                        "Request approved": [
                            {
                                "connection_key": None,
                                "collection_name": None,
                                "fields_affected": None,
                                "message": "",
                                "action_type": None,
                                "status": "approved",
                                "updated_at": stringify_date(audit_log.updated_at),
                                "user_id": "system",
                            }
                        ],
                        "my-mongo-db": [
                            {
                                "connection_key": None,
                                "collection_name": "orders",
                                "fields_affected": [
                                    {
                                        "path": "my-mongo-db:orders:name",
                                        "field_name": "name",
                                        "data_categories": ["user.contact.name"],
                                    }
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "in_processing",
                                "updated_at": stringify_date(
                                    mongo_execution_log.updated_at
                                ),
                                "user_id": None,
                            }
                        ],
                        "my-postgres-db": [
                            {
                                "connection_key": None,
                                "collection_name": "user",
                                "fields_affected": [
                                    {
                                        "path": "my-postgres-db:user:email",
                                        "field_name": "email",
                                        "data_categories": ["user.contact.email"],
                                    }
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "pending",
                                "updated_at": stringify_date(
                                    postgres_execution_log.updated_at
                                ),
                                "user_id": None,
                            },
                            {
                                "connection_key": None,
                                "collection_name": "address",
                                "fields_affected": [
                                    {
                                        "path": "my-postgres-db:address:street",
                                        "field_name": "street",
                                        "data_categories": [
                                            "user.contact.address.street"
                                        ],
                                    },
                                    {
                                        "path": "my-postgres-db:address:city",
                                        "field_name": "city",
                                        "data_categories": [
                                            "user.contact.address.city"
                                        ],
                                    },
                                ],
                                "message": "Database timed out.",
                                "action_type": "access",
                                "status": "error",
                                "updated_at": stringify_date(
                                    second_postgres_execution_log.updated_at
                                ),
                                "user_id": None,
                            },
                        ],
                        "my-async-connector": [
                            {
                                "connection_key": None,
                                "collection_name": "my_async_collection",
                                "fields_affected": [
                                    {
                                        "path": "my-async-connector:my_async_collection:street",
                                        "field_name": "street",
                                        "data_categories": [
                                            "user.contact.address.street"
                                        ],
                                    },
                                    {
                                        "path": "my-async-connector:my_async_collection:city",
                                        "field_name": "city",
                                        "data_categories": [
                                            "user.contact.address.city"
                                        ],
                                    },
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "awaiting_processing",
                                "updated_at": stringify_date(
                                    async_execution_log.updated_at
                                ),
                                "user_id": None,
                            }
                        ],
                    },
                },
            ],
            "total": 1,
            "page": 1,
            "pages": 1,
            "size": page_size,
        }
        assert resp == expected_resp

    def test_verbose_privacy_request_embed_limit(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        privacy_request: PrivacyRequest,
        url,
    ):
        for i in range(0, EMBEDDED_EXECUTION_LOG_LIMIT + 10):
            ExecutionLog.create(
                db=db,
                data={
                    "connection_key": "my-postgres-db-key",
                    "dataset_name": "my-postgres-db",
                    "collection_name": f"test_collection_{i}",
                    "fields_affected": [],
                    "action_type": ActionType.access,
                    "status": ExecutionLogStatus.pending,
                    "privacy_request_id": privacy_request.id,
                },
            )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url + f"?verbose=True", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert (
            len(resp["items"][0]["results"]["my-postgres-db"])
            == EMBEDDED_EXECUTION_LOG_LIMIT
        )
        db.query(ExecutionLog).filter(
            ExecutionLog.privacy_request_id == privacy_request.id
        ).delete()

    def test_get_privacy_requests_csv_format(
        self, db, generate_auth_header, api_client, url, privacy_request, user
    ):
        reviewed_at = datetime.now()
        created_at = datetime.now()

        privacy_request.created_at = created_at
        privacy_request.status = PrivacyRequestStatus.approved
        privacy_request.reviewed_by = user.id
        privacy_request.reviewed_at = reviewed_at
        TEST_EMAIL = "test@example.com"
        TEST_PHONE = "+12345678910"
        privacy_request.cache_identity(
            {
                "email": TEST_EMAIL,
                "phone_number": TEST_PHONE,
            }
        )
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url + f"?download_csv=True", headers=auth_header)
        assert 200 == response.status_code

        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename=privacy_requests_download_{datetime.today().strftime('%Y-%m-%d')}.csv"
        )

        content = response.content.decode()
        file = io.StringIO(content)
        csv_file = csv.DictReader(file, delimiter=",")

        first_row = next(csv_file)
        assert parse(first_row["Time Received"], ignoretz=True) == created_at
        assert ast.literal_eval(first_row["Subject Identity"]) == {
            "email": TEST_EMAIL,
            "phone_number": TEST_PHONE,
            "ga_client_id": None,
            "ljt_readerID": None,
            "fides_user_device_id": None,
            "external_id": None,
        }
        assert first_row["Request Type"] == "access"
        assert first_row["Status"] == "approved"
        assert first_row["Reviewed By"] == user.id
        assert parse(first_row["Time Approved/Denied"], ignoretz=True) == reviewed_at
        assert first_row["Denial Reason"] == ""
        assert first_row["Request ID"] == privacy_request.id

        privacy_request.delete(db)

    def test_get_requires_input_privacy_request_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in a requires_input state
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "requires_input"
        assert data["action_required_details"] is None
        assert data[
            "resume_endpoint"
        ] == "/privacy-request/{}/resume_from_requires_input".format(privacy_request.id)

    def test_get_paused_webhook_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "paused"
        assert data["action_required_details"] is None
        assert data["resume_endpoint"] == "/privacy-request/{}/resume".format(
            privacy_request.id
        )

    def test_get_failed_request_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in an errored state waiting for retry
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)
        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.erasure,
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "error"
        assert data["action_required_details"] == {
            "step": "erasure",
            "collection": None,
            "action_needed": None,
        }
        assert data["resume_endpoint"] == f"/privacy-request/{privacy_request.id}/retry"

    def test_get_failed_request_resume_info_from_email_post_send(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in an errored state waiting for retry
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)
        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.email_post_send,
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "error"
        assert data["action_required_details"] == {
            "step": "email_post_send",
            "collection": None,
            "action_needed": None,
        }
        assert data["resume_endpoint"] == f"/privacy-request/{privacy_request.id}/retry"

    @pytest.mark.parametrize(
        "due_date, days_left",
        [
            (
                datetime.utcnow() + timedelta(days=7),
                7,
            ),
            (
                datetime.utcnow(),
                0,
            ),
            (
                datetime.utcnow() + timedelta(days=-7),
                -7,
            ),
        ],
    )
    def test_get_privacy_requests_sets_days_left(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        privacy_request,
        due_date,
        days_left,
    ):
        privacy_request.due_date = due_date
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        data = response.json()["items"][0]
        assert data["days_left"] == days_left

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_sort_privacy_request_by_due_date(
        self,
        run_access_request_mock,
        generate_auth_header,
        url,
        db,
        api_client: TestClient,
        policy: Policy,
    ):
        days_left_values = []
        data = []
        now = datetime.utcnow()
        for _ in range(0, 10):
            days = randint(1, 100)
            requested_at = now + timedelta(days=days)
            data.append(
                {
                    "requested_at": str(requested_at),
                    "policy_key": policy.key,
                    "identity": {"email": "test@example.com"},
                }
            )
            days_left_values.append(days + policy.execution_timeframe)

        api_client.post(url, json=data)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.request(
            "GET",
            f"{url}?sort_direction=asc&sort_field=due_date",
            json=data,
            headers=auth_header,
        )
        asc_response_data = resp.json()["items"]
        days_left_values.sort()
        for i, request in enumerate(asc_response_data):
            assert request["days_left"] == days_left_values[i]

        resp = api_client.request(
            "GET",
            f"{url}?sort_direction=desc&sort_field=due_date",
            json=data,
            headers=auth_header,
        )
        desc_response_data = resp.json()["items"]
        days_left_values.reverse()
        for i, request in enumerate(desc_response_data):
            assert request["days_left"] == days_left_values[i]

        for request in desc_response_data:
            pr = PrivacyRequest.get(db=db, object_id=request["id"])
            pr.delete(db=db)


class TestPrivacyRequestSearch:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH

    def test_privacy_request_search_unauthenticated(self, api_client: TestClient, url):
        response = api_client.post(url, headers={})
        assert 401 == response.status_code

    def test_privacy_request_search_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code

    def test_privacy_request_search_approver_role(
        self, api_client: TestClient, generate_role_header, url
    ):
        auth_header = generate_role_header(roles=[APPROVER])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code

    def test_conflicting_query_params(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "completed_lt": "2021-01-01T00:00:00.000Z",
                "errored_gt": "2021-01-02T00:00:00.000Z",
            },
        )
        assert 400 == response.status_code

    def test_privacy_request_search_displays_reviewer(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        privacy_request,
        user,
        postgres_execution_log,
        mongo_execution_log,
    ):
        privacy_request.reviewer = user
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"request_id": privacy_request.id}
        )
        assert 200 == response.status_code

        reviewer = response.json()["items"][0]["reviewer"]
        assert reviewer
        assert user.id == reviewer["id"]
        assert user.username == reviewer["username"]
        privacy_request.delete(db)

    def test_privacy_request_search_accept_datetime(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        privacy_request,
        postgres_execution_log,
        mongo_execution_log,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        for date_format in [
            "%Y-%m-%dT00:00:00.000Z",
            # "%Y-%m-%d",
        ]:
            date_input = privacy_request.created_at.strftime(date_format)
            response = api_client.post(
                url, headers=auth_header, json={"created_gt": date_input}
            )

            assert 200 == response.status_code

    def test_privacy_request_search_by_id(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        postgres_execution_log,
        mongo_execution_log,
        db,
    ):
        privacy_request.due_date = None
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"request_id": privacy_request.id}
        )
        assert 200 == response.status_code

        expected_resp = {
            "items": [
                {
                    "id": privacy_request.id,
                    "created_at": stringify_date(privacy_request.created_at),
                    "custom_privacy_request_fields": None,
                    "custom_privacy_request_fields_approved_at": None,
                    "custom_privacy_request_fields_approved_by": None,
                    "days_left": None,
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "identity_verified_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "source": None,
                    "policy": {
                        "drp_action": None,
                        "execution_timeframe": 7,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.model_dump(mode="json")
                            for rule in PolicyResponse.model_validate(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "action_required_details": None,
                    "resume_endpoint": None,
                    "deleted_at": None,
                    "deleted_by": None,
                }
            ],
            "total": 1,
            "page": 1,
            "pages": 1,
            "size": page_size,
        }

        resp = response.json()
        assert resp == expected_resp

    def test_privacy_request_search_by_partial_id(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        postgres_execution_log,
        mongo_execution_log,
        db,
    ):
        privacy_request.due_date = None
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"request_id": privacy_request.id[:5]}
        )
        assert 200 == response.status_code

        expected_resp = {
            "items": [
                {
                    "id": privacy_request.id,
                    "created_at": stringify_date(privacy_request.created_at),
                    "custom_privacy_request_fields": None,
                    "custom_privacy_request_fields_approved_at": None,
                    "custom_privacy_request_fields_approved_by": None,
                    "days_left": None,
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "identity_verified_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "source": None,
                    "policy": {
                        "execution_timeframe": 7,
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.model_dump(mode="json")
                            for rule in PolicyResponse.model_validate(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "action_required_details": None,
                    "resume_endpoint": None,
                    "deleted_at": None,
                    "deleted_by": None,
                }
            ],
            "total": 1,
            "page": 1,
            "pages": 1,
            "size": page_size,
        }

        resp = response.json()
        assert resp == expected_resp

    def test_privacy_request_search_with_identity(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={"status": "complete", "include_identities": True},
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id
        assert resp["items"][0][
            "identity"
        ] == succeeded_privacy_request.get_persisted_identity().labeled_dict(
            include_default_labels=True
        )

        assert resp["items"][0]["policy"]["key"] == privacy_request.policy.key
        assert resp["items"][0]["policy"]["name"] == privacy_request.policy.name

        # Now test the identities are omitted if not explicitly requested
        response = api_client.post(
            url, headers=auth_header, json={"status": "complete"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id
        assert resp["items"][0].get("identity") is None

        response = api_client.post(
            url,
            headers=auth_header,
            json={"status": "complete", "include_identities": False},
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id
        assert resp["items"][0].get("identity") is None

    def test_privacy_request_search_with_custom_fields(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request_with_custom_fields,
    ):
        privacy_request = privacy_request_with_custom_fields
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={"include_custom_privacy_request_fields": True},
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id
        assert (
            resp["items"][0]["custom_privacy_request_fields"]
            == privacy_request.get_persisted_custom_privacy_request_fields()
        )

        assert resp["items"][0]["policy"]["key"] == privacy_request.policy.key
        assert resp["items"][0]["policy"]["name"] == privacy_request.policy.name

        # Now test the custom fields are omitted if not explicitly requested
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id
        assert resp["items"][0].get("custom_privacy_request_fields") is None

        response = api_client.post(
            url,
            headers=auth_header,
            json={"include_custom_privacy_request_fields": False},
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id
        assert resp["items"][0].get("custom_privacy_request_fields") is None

    def test_privacy_request_search_by_custom_fields_and_array_fields(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request_with_custom_fields,
        privacy_request_with_custom_array_fields,
    ):
        privacy_request = privacy_request_with_custom_fields
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "custom_privacy_request_fields": {"first_name": "John"},
                "include_custom_privacy_request_fields": True,
            },
        )
        assert 200 == response.status_code

        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id
        assert (
            resp["items"][0]["custom_privacy_request_fields"]
            == privacy_request.get_persisted_custom_privacy_request_fields()
        )
        assert resp["items"][0]["policy"]["key"] == privacy_request.policy.key
        assert resp["items"][0]["policy"]["name"] == privacy_request.policy.name

        # List fields are not indexed for search. privacy_request_with_custom_array_fields has a list of custom
        # privacy request fields but it will not be returned here
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "custom_privacy_request_fields": {"device_id": "device_1"},
                "include_custom_privacy_request_fields": True,
            },
        )
        assert 200 == response.status_code

        resp = response.json()
        assert len(resp["items"]) == 0

        # If a list field is sent in as the query param, we ignore the list field in search, it does not become a filter -
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "custom_privacy_request_fields": {"device_id": ["device_1"]},
                "include_custom_privacy_request_fields": True,
            },
        )
        assert 200 == response.status_code

        resp = response.json()
        assert len(resp["items"]) == 2

    def test_privacy_request_search_by_action(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        executable_consent_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"action_type": "access"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1

        response = api_client.post(
            url, headers=auth_header, json={"action_type": "consent"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1

        response = api_client.post(
            url, headers=auth_header, json={"action_type": "erasure"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

    def test_privacy_request_search_by_status(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"status": "complete"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id

        response = api_client.post(url, headers=auth_header, json={"status": "error"})
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == failed_privacy_request.id

    def test_privacy_request_search_by_multiple_statuses(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"status": ["complete", "error"]}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 2
        assert resp["items"][0]["id"] == failed_privacy_request.id
        assert resp["items"][1]["id"] == succeeded_privacy_request.id

    def test_privacy_request_search_excludes_deleted_by_default(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"status": "in_processing"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    def test_privacy_request_search_exclude_deleted_requests(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={"status": "in_processing", "include_deleted_requests": False},
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    def test_privacy_request_search_include_deleted_requests(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        privacy_request,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={"status": "in_processing", "include_deleted_requests": True},
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 2

        item_ids = [item["id"] for item in resp["items"]]
        assert privacy_request.id in item_ids
        assert soft_deleted_privacy_request.id in item_ids

    def test_privacy_request_search_by_internal_id(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
                "id": "test_internal_id_1",
            }
        ]
        resp = api_client.post(V1_URL_PREFIX + PRIVACY_REQUESTS, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        privacy_request = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"request_id": privacy_request.id}
        )
        assert response.status_code == status.HTTP_200_OK
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    def test_privacy_request_search_by_identity_no_request_id(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
    ):
        TEST_EMAIL = "test-12345678910@example.com"
        privacy_request.persist_identity(
            db=db,
            identity=Identity(
                email=TEST_EMAIL,
            ),
        )
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"identities": {"email": TEST_EMAIL}}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    def test_privacy_request_search_by_external_id(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"external_id": succeeded_privacy_request.id}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        privacy_request.external_id = "test_external_id_1"
        privacy_request.save(db)

        response = api_client.post(
            url, headers=auth_header, json={"external_id": "test_external_id_1"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request.id

    def test_privacy_request_search_by_created(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"created_lt": "2019-01-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.post(
            url, headers=auth_header, json={"created_gt": "2019-01-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 3
        assert resp["items"][0]["id"] == failed_privacy_request.id
        assert resp["items"][1]["id"] == succeeded_privacy_request.id
        assert resp["items"][2]["id"] == privacy_request.id

    def test_privacy_request_search_by_conflicting_date_fields(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        # Search for privacy requests after 2019, but before 2018. This should return an error.
        start = "2019-01-01"
        end = "2018-01-01"
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "created_gt": f"{start}T00:00:00.000Z",
                "created_lt": f"{end}T00:00:00.000Z",
            },
        )
        assert 400 == response.status_code
        assert (
            response.json()["detail"]
            == f"Value specified for created_lt: {end} 00:00:00+00:00 must be after created_gt: {start} 00:00:00+00:00."
        )

    def test_privacy_request_search_by_started(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"started_lt": "2021-05-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 2
        assert resp["items"][0]["id"] == failed_privacy_request.id
        assert resp["items"][1]["id"] == privacy_request.id

        response = api_client.post(
            url, headers=auth_header, json={"started_gt": "2021-05-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id

    def test_privacy_request_search_by_completed(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"completed_lt": "2021-10-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.post(
            url, headers=auth_header, json={"completed_gt": "2021-10-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == succeeded_privacy_request.id

    def test_privacy_request_search_by_errored(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        succeeded_privacy_request,
        failed_privacy_request,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"errored_lt": "2021-01-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.post(
            url, headers=auth_header, json={"errored_gt": "2021-01-01T00:00:00.000Z"}
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == failed_privacy_request.id

    def test_verbose_privacy_requests(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request: PrivacyRequest,
        audit_log,
        postgres_execution_log,
        second_postgres_execution_log,
        mongo_execution_log,
        async_execution_log,
        url,
        db,
    ):
        """Test privacy requests endpoint with verbose query param to show execution logs"""
        privacy_request.due_date = None
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header, json={"verbose": True})
        assert 200 == response.status_code

        resp = response.json()
        assert (
            postgres_execution_log.updated_at < second_postgres_execution_log.updated_at
        )
        expected_resp = {
            "items": [
                {
                    "id": privacy_request.id,
                    "created_at": stringify_date(privacy_request.created_at),
                    "custom_privacy_request_fields": None,
                    "custom_privacy_request_fields_approved_at": None,
                    "custom_privacy_request_fields_approved_by": None,
                    "days_left": None,
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "identity_verified_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "source": None,
                    "policy": {
                        "execution_timeframe": 7,
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.model_dump(mode="json")
                            for rule in PolicyResponse.model_validate(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "action_required_details": None,
                    "resume_endpoint": None,
                    "deleted_at": None,
                    "deleted_by": None,
                    "results": {
                        "Request approved": [
                            {
                                "connection_key": None,
                                "collection_name": None,
                                "fields_affected": None,
                                "message": "",
                                "action_type": None,
                                "status": "approved",
                                "updated_at": stringify_date(audit_log.updated_at),
                                "user_id": "system",
                            }
                        ],
                        "my-mongo-db": [
                            {
                                "connection_key": None,
                                "collection_name": "orders",
                                "fields_affected": [
                                    {
                                        "path": "my-mongo-db:orders:name",
                                        "field_name": "name",
                                        "data_categories": ["user.contact.name"],
                                    }
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "in_processing",
                                "updated_at": stringify_date(
                                    mongo_execution_log.updated_at
                                ),
                                "user_id": None,
                            }
                        ],
                        "my-postgres-db": [
                            {
                                "connection_key": None,
                                "collection_name": "user",
                                "fields_affected": [
                                    {
                                        "path": "my-postgres-db:user:email",
                                        "field_name": "email",
                                        "data_categories": ["user.contact.email"],
                                    }
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "pending",
                                "updated_at": stringify_date(
                                    postgres_execution_log.updated_at
                                ),
                                "user_id": None,
                            },
                            {
                                "connection_key": None,
                                "collection_name": "address",
                                "fields_affected": [
                                    {
                                        "path": "my-postgres-db:address:street",
                                        "field_name": "street",
                                        "data_categories": [
                                            "user.contact.address.street"
                                        ],
                                    },
                                    {
                                        "path": "my-postgres-db:address:city",
                                        "field_name": "city",
                                        "data_categories": [
                                            "user.contact.address.city"
                                        ],
                                    },
                                ],
                                "message": "Database timed out.",
                                "action_type": "access",
                                "status": "error",
                                "updated_at": stringify_date(
                                    second_postgres_execution_log.updated_at
                                ),
                                "user_id": None,
                            },
                        ],
                        "my-async-connector": [
                            {
                                "connection_key": None,
                                "collection_name": "my_async_collection",
                                "fields_affected": [
                                    {
                                        "path": "my-async-connector:my_async_collection:street",
                                        "field_name": "street",
                                        "data_categories": [
                                            "user.contact.address.street"
                                        ],
                                    },
                                    {
                                        "path": "my-async-connector:my_async_collection:city",
                                        "field_name": "city",
                                        "data_categories": [
                                            "user.contact.address.city"
                                        ],
                                    },
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "awaiting_processing",
                                "updated_at": stringify_date(
                                    async_execution_log.updated_at
                                ),
                                "user_id": None,
                            }
                        ],
                    },
                },
            ],
            "total": 1,
            "page": 1,
            "pages": 1,
            "size": page_size,
        }
        assert resp == expected_resp

    def test_verbose_privacy_request_embed_limit(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        privacy_request: PrivacyRequest,
        url,
    ):
        for i in range(0, EMBEDDED_EXECUTION_LOG_LIMIT + 10):
            ExecutionLog.create(
                db=db,
                data={
                    "connection_key": "my-postgres-db-key",
                    "dataset_name": "my-postgres-db",
                    "collection_name": f"test_collection_{i}",
                    "fields_affected": [],
                    "action_type": ActionType.access,
                    "status": ExecutionLogStatus.pending,
                    "privacy_request_id": privacy_request.id,
                },
            )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header, json={"verbose": True})
        assert 200 == response.status_code
        resp = response.json()
        assert (
            len(resp["items"][0]["results"]["my-postgres-db"])
            == EMBEDDED_EXECUTION_LOG_LIMIT
        )
        db.query(ExecutionLog).filter(
            ExecutionLog.privacy_request_id == privacy_request.id
        ).delete()

    def test_privacy_request_search_csv_format(
        self, db, generate_auth_header, api_client, url, privacy_request, user
    ):
        reviewed_at = datetime.now()
        created_at = datetime.now()

        privacy_request.created_at = created_at
        privacy_request.status = PrivacyRequestStatus.approved
        privacy_request.reviewed_by = user.id
        privacy_request.reviewed_at = reviewed_at
        TEST_EMAIL = "test@example.com"
        TEST_PHONE = "+12345678910"
        privacy_request.cache_identity(
            {
                "email": TEST_EMAIL,
                "phone_number": TEST_PHONE,
            }
        )
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, headers=auth_header, json={"download_csv": True}
        )
        assert 200 == response.status_code

        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert (
            response.headers["content-disposition"]
            == f"attachment; filename=privacy_requests_download_{datetime.today().strftime('%Y-%m-%d')}.csv"
        )

        content = response.content.decode()
        file = io.StringIO(content)
        csv_file = csv.DictReader(file, delimiter=",")

        first_row = next(csv_file)
        assert parse(first_row["Time Received"], ignoretz=True) == created_at
        assert ast.literal_eval(first_row["Subject Identity"]) == {
            "email": TEST_EMAIL,
            "phone_number": TEST_PHONE,
            "ga_client_id": None,
            "ljt_readerID": None,
            "fides_user_device_id": None,
            "external_id": None,
        }
        assert first_row["Request Type"] == "access"
        assert first_row["Status"] == "approved"
        assert first_row["Reviewed By"] == user.id
        assert parse(first_row["Time Approved/Denied"], ignoretz=True) == reviewed_at
        assert first_row["Denial Reason"] == ""
        assert first_row["Request ID"] == privacy_request.id

        privacy_request.delete(db)

    def test_get_requires_input_privacy_request_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in a requires_input state
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "requires_input"
        assert data["action_required_details"] is None
        assert data[
            "resume_endpoint"
        ] == "/privacy-request/{}/resume_from_requires_input".format(privacy_request.id)

    def test_get_paused_webhook_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "paused"
        assert data["action_required_details"] is None
        assert data["resume_endpoint"] == "/privacy-request/{}/resume".format(
            privacy_request.id
        )

    def test_get_failed_request_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in an errored state waiting for retry
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)
        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.erasure,
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "error"
        assert data["action_required_details"] == {
            "step": "erasure",
            "collection": None,
            "action_needed": None,
        }
        assert data["resume_endpoint"] == f"/privacy-request/{privacy_request.id}/retry"

    def test_get_failed_request_resume_info_from_email_post_send(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in an errored state waiting for retry
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)
        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.email_post_send,
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "error"
        assert data["action_required_details"] == {
            "step": "email_post_send",
            "collection": None,
            "action_needed": None,
        }
        assert data["resume_endpoint"] == f"/privacy-request/{privacy_request.id}/retry"

    @pytest.mark.parametrize(
        "due_date, days_left",
        [
            (
                datetime.utcnow() + timedelta(days=7),
                7,
            ),
            (
                datetime.utcnow(),
                0,
            ),
            (
                datetime.utcnow() + timedelta(days=-7),
                -7,
            ),
        ],
    )
    def test_privacy_request_search_sets_days_left(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        privacy_request,
        due_date,
        days_left,
    ):
        privacy_request.due_date = due_date
        privacy_request.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        data = response.json()["items"][0]
        assert data["days_left"] == days_left

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_sort_privacy_request_by_due_date(
        self,
        run_access_request_mock,
        generate_auth_header,
        url,
        db,
        api_client: TestClient,
        policy: Policy,
    ):
        days_left_values = []
        data = []
        now = datetime.utcnow()
        for _ in range(0, 10):
            days = randint(1, 100)
            requested_at = now + timedelta(days=days)
            data.append(
                {
                    "requested_at": str(requested_at),
                    "policy_key": policy.key,
                    "identity": {"email": "test@example.com"},
                }
            )
            days_left_values.append(days + policy.execution_timeframe)

        api_client.post(V1_URL_PREFIX + PRIVACY_REQUEST_SEARCH, json=data)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.post(
            url,
            headers=auth_header,
            json={"sort_direction": "asc", "sort_field": "due_date"},
        )
        asc_response_data = resp.json()["items"]
        days_left_values.sort()
        for i, request in enumerate(asc_response_data):
            assert request["days_left"] == days_left_values[i]

        resp = api_client.post(
            url,
            headers=auth_header,
            json={"sort_direction": "desc", "sort_field": "due_date"},
        )
        desc_response_data = resp.json()["items"]
        days_left_values.reverse()
        for i, request in enumerate(desc_response_data):
            assert request["days_left"] == days_left_values[i]

        for request in desc_response_data:
            pr = PrivacyRequest.get(db=db, object_id=request["id"])
            pr.delete(db=db)

    def test_privacy_request_search_by_default_identities(
        self,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
        privacy_request_with_email_identity,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "identities": {"email": "customer-1@example.com"},
                "include_identities": True,
            },
        )
        assert 200 == response.status_code

        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request_with_email_identity.id

    def test_privacy_request_search_by_custom_identities(
        self,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
        privacy_request_with_custom_identities,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={"identities": {"loyalty_id": "CH-1"}, "include_identities": True},
        )
        assert 200 == response.status_code

        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request_with_custom_identities.id

    @pytest.mark.usefixtures("allow_custom_privacy_request_field_collection_enabled")
    def test_privacy_request_search_by_custom_fields(
        self,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
        privacy_request_with_custom_fields,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "custom_privacy_request_fields": {"first_name": "John"},
                "include_custom_privacy_request_fields": True,
            },
        )
        assert 200 == response.status_code

        resp = response.json()
        assert len(resp["items"]) == 1
        assert resp["items"][0]["id"] == privacy_request_with_custom_fields.id


class TestGetExecutionLogs:
    @pytest.fixture(scope="function")
    def url(self, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUESTS + f"/{privacy_request.id}/log"

    def test_get_execution_logs_unauthenticated(
        self, api_client: TestClient, privacy_request, url
    ):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_execution_logs_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_execution_logs_invalid_privacy_request_id(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            V1_URL_PREFIX + PRIVACY_REQUESTS + f"/invalid_privacy_request_id/log",
            headers=auth_header,
        )
        assert 404 == response.status_code

    def test_get_execution_logs(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        postgres_execution_log,
        mongo_execution_log,
        second_postgres_execution_log,
        async_execution_log,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            url,
            headers=auth_header,
        )
        assert 200 == response.status_code
        resp = response.json()

        expected_resp = {
            "items": [
                {
                    "collection_name": "user",
                    "fields_affected": [
                        {
                            "path": "my-postgres-db:user:email",
                            "field_name": "email",
                            "data_categories": ["user.contact.email"],
                        }
                    ],
                    "message": None,
                    "action_type": "access",
                    "status": "pending",
                    "updated_at": stringify_date(postgres_execution_log.updated_at),
                    "connection_key": None,
                    "dataset_name": "my-postgres-db",
                },
                {
                    "collection_name": "orders",
                    "fields_affected": [
                        {
                            "path": "my-mongo-db:orders:name",
                            "field_name": "name",
                            "data_categories": ["user.contact.name"],
                        }
                    ],
                    "message": None,
                    "action_type": "access",
                    "status": "in_processing",
                    "updated_at": stringify_date(mongo_execution_log.updated_at),
                    "connection_key": None,
                    "dataset_name": "my-mongo-db",
                },
                {
                    "collection_name": "address",
                    "fields_affected": [
                        {
                            "path": "my-postgres-db:address:street",
                            "field_name": "street",
                            "data_categories": ["user.contact.address.street"],
                        },
                        {
                            "path": "my-postgres-db:address:city",
                            "field_name": "city",
                            "data_categories": ["user.contact.address.city"],
                        },
                    ],
                    "message": "Database timed out.",
                    "action_type": "access",
                    "status": "error",
                    "updated_at": stringify_date(
                        second_postgres_execution_log.updated_at
                    ),
                    "connection_key": None,
                    "dataset_name": "my-postgres-db",
                },
                {
                    "collection_name": "my_async_collection",
                    "fields_affected": [
                        {
                            "path": "my-async-connector:my_async_collection:street",
                            "field_name": "street",
                            "data_categories": ["user.contact.address.street"],
                        },
                        {
                            "path": "my-async-connector:my_async_collection:city",
                            "field_name": "city",
                            "data_categories": ["user.contact.address.city"],
                        },
                    ],
                    "message": None,
                    "action_type": "access",
                    "status": "awaiting_processing",
                    "updated_at": stringify_date(async_execution_log.updated_at),
                    "connection_key": None,
                    "dataset_name": "my-async-connector",
                },
            ],
            "total": 4,
            "page": 1,
            "pages": 1,
            "size": page_size,
        }

        assert resp == expected_resp


class TestRequestPreview:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + REQUEST_PREVIEW

    def test_request_preview(
        self,
        dataset_config_preview,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        data = [dataset_config_preview.fides_key]
        response = api_client.put(url, headers=auth_header, json=data)
        assert response.status_code == 200
        response_body: List[DryRunDatasetResponse] = json.loads(response.text)
        assert (
            next(
                response["query"]
                for response in response_body
                if response["collectionAddress"]["dataset"] == "postgres"
                if response["collectionAddress"]["collection"] == "subscriptions"
            )
            == 'SELECT email, id FROM "subscriptions" WHERE (email = ?)'
        )

    def test_request_preview_incorrect_body(
        self,
        dataset_config_preview,
        api_client: TestClient,
        url,
        generate_auth_header,
        example_datasets,
        mongo_connection_config,
        connection_config,
    ) -> None:
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {"connection_key": mongo_connection_config.key}
        datasets_url = path.format(**path_params)

        # Use the dataset endpoint to create the Mongo DatasetConfig
        api_client.patch(
            datasets_url,
            headers=generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE]),
            json=[example_datasets[1]],
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        data = [
            example_datasets[1]["fides_key"]
        ]  # Mongo dataset that references a postgres dataset
        response = api_client.put(url, headers=auth_header, json=data)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Referred to object postgres_example_test_dataset:customer:id does not "
            "exist. Make sure all referenced datasets are included in the request body."
        )

        # Use the dataset endpoint to create the Postgres DatasetConfig
        api_client.patch(
            datasets_url,
            headers=generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE]),
            json=[example_datasets[0]],
        )

        # Preview still 400's, because both dataset fideskeys aren't included in the response
        response = api_client.put(url, headers=auth_header, json=data)
        assert response.status_code == 400

        # Preview returns a 200, because both dataset keys are in the request body
        response = api_client.put(
            url,
            headers=auth_header,
            json=[example_datasets[0]["fides_key"], example_datasets[1]["fides_key"]],
        )
        assert response.status_code == 200

    def test_request_preview_all(
        self,
        dataset_config_preview,
        mongo_connection_config,
        postgres_example_test_dataset_config,
        mongo_dataset_config,
        api_client: TestClient,
        url,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.put(url, headers=auth_header)
        assert response.status_code == 200
        response_body: List[DryRunDatasetResponse] = json.loads(response.text)

        assert (
            next(
                response["query"]
                for response in response_body
                if response["collectionAddress"]["dataset"] == "postgres"
                if response["collectionAddress"]["collection"] == "subscriptions"
            )
            == 'SELECT email, id FROM "subscriptions" WHERE (email = ?)'
        )
        assert (
            next(
                response["query"]
                for response in response_body
                if response["collectionAddress"]["dataset"] == "mongo_test"
                if response["collectionAddress"]["collection"] == "customer_feedback"
            )
            == "db.mongo_test.customer_feedback.find({'customer_information.email': ?}, {'_id': 1, 'customer_information': 1, 'date': 1, 'message': 1, 'rating': 1})"
        )


class TestApprovePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_APPROVE

    @pytest.fixture(scope="function")
    def privacy_request_review_notification_enabled(self, db):
        """Enable request review notification"""
        original_value = CONFIG.notifications.send_request_review_notification
        CONFIG.notifications.send_request_review_notification = True
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.send_request_review_notification = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    def test_approve_privacy_request_not_authenticated(self, url, api_client):
        response = api_client.patch(url)
        assert response.status_code == 401

    def test_approve_privacy_request_bad_scopes(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.patch(url, headers=auth_header)
        assert response.status_code == 403

    def test_approve_privacy_request_viewer_role(
        self, url, api_client, generate_role_header
    ):
        auth_header = generate_role_header(roles=[VIEWER])
        response = api_client.patch(url, headers=auth_header)
        assert response.status_code == 403

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_approve_privacy_request_approver_role(
        self, _, url, api_client, generate_role_header, privacy_request, db
    ):
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db=db)

        auth_header = generate_role_header(roles=[APPROVER])
        body = {"request_ids": [privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_approve_privacy_request_does_not_exist(
        self, submit_mock, db, url, api_client, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])

        body = {"request_ids": ["does_not_exist"]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["succeeded"] == []
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "No privacy request found with id 'does_not_exist'"
        )
        assert not submit_mock.called

    @pytest.mark.parametrize(
        "privacy_request_status",
        [PrivacyRequestStatus.complete, PrivacyRequestStatus.canceled],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_approve_privacy_request_in_non_pending_state(
        self,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        privacy_request,
        privacy_request_status,
    ):
        privacy_request.status = privacy_request_status
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])

        body = {"request_ids": [privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["succeeded"] == []
        assert len(response_body["failed"]) == 1
        assert response_body["failed"][0]["message"] == "Cannot transition status"
        assert (
            response_body["failed"][0]["data"]["status"] == privacy_request_status.value
        )
        assert not submit_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_approve_deleted_privacy_request(
        self,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])

        body = {"request_ids": [soft_deleted_privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["succeeded"] == []
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "Cannot transition status for a deleted request"
        )
        assert (
            response_body["failed"][0]["data"]["id"] == soft_deleted_privacy_request.id
        )
        assert not submit_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_approve_privacy_request_no_user_on_client(
        self,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        privacy_request,
        user,
    ):
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])

        body = {"request_ids": [privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0
        assert response_body["succeeded"][0]["status"] == "approved"
        assert response_body["succeeded"][0]["id"] == privacy_request.id
        assert response_body["succeeded"][0]["reviewed_at"] is not None
        assert response_body["succeeded"][0]["reviewed_by"] is None  # No user on client

        assert submit_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_approve_privacy_request(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request,
    ):
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db=db)

        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }

        body = {"request_ids": [privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)

        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0
        assert response_body["succeeded"][0]["status"] == "approved"
        assert response_body["succeeded"][0]["id"] == privacy_request.id
        assert response_body["succeeded"][0]["reviewed_at"] is not None
        assert response_body["succeeded"][0]["reviewed_by"] == user.id
        assert (
            response_body["succeeded"][0]["custom_privacy_request_fields_approved_at"]
            is None
        )
        assert (
            response_body["succeeded"][0]["custom_privacy_request_fields_approved_by"]
            is None
        )

        assert submit_mock.called
        assert not mock_dispatch_message.called

        privacy_request.delete(db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_approve_privacy_request_with_custom_fields(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_with_custom_fields,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        privacy_request = privacy_request_with_custom_fields
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db=db)

        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }

        body = {"request_ids": [privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)

        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0
        assert response_body["succeeded"][0]["status"] == "approved"
        assert response_body["succeeded"][0]["id"] == privacy_request.id
        assert response_body["succeeded"][0]["reviewed_at"] is not None
        assert response_body["succeeded"][0]["reviewed_by"] == user.id
        assert (
            response_body["succeeded"][0]["custom_privacy_request_fields_approved_at"]
            is not None
        )
        assert (
            response_body["succeeded"][0]["custom_privacy_request_fields_approved_by"]
            == user.id
        )

        assert submit_mock.called
        assert not mock_dispatch_message.called

        privacy_request.delete(db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_approve_privacy_request_creates_audit_log_and_sends_email(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
        privacy_request_review_notification_enabled,
    ):
        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }

        body = {"request_ids": [privacy_request_status_pending.id]}
        api_client.patch(url, headers=auth_header, json=body)
        approval_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.user_id == user.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()

        assert approval_audit_log is not None
        assert approval_audit_log.message == ""

        approval_audit_log.delete(db)

        call_args = mock_dispatch_message.call_args[1]
        task_kwargs = call_args["kwargs"]
        assert task_kwargs["to_identity"] == Identity(
            email="test@example.com"
        ).model_dump(mode="json")
        assert task_kwargs["service_type"] == MessagingServiceType.mailgun.value

        message_meta = task_kwargs["message_meta"]
        assert (
            message_meta["action_type"]
            == MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE
        )
        assert message_meta["body_params"] is None
        queue = call_args["queue"]
        assert queue == MESSAGING_QUEUE_NAME


class TestMarkPrivacyRequestPreApproveEligible:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request_status_pending):
        return V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )

    @pytest.fixture(scope="function")
    def privacy_request_review_notification_enabled(self, db):
        """Enable request receipt"""
        original_value = CONFIG.notifications.send_request_review_notification
        CONFIG.notifications.send_request_review_notification = True
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.send_request_review_notification = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    def test_mark_eligible_not_authenticated(
        self,
        url,
        api_client,
        privacy_request_status_pending,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        response = api_client.post(url)
        assert response.status_code == 401

    def test_mark_eligible_invalid_jwe_format(
        self,
        url,
        api_client,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps({"unexpected": "format"}), CONFIG.security.app_encryption_key
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_mark_eligible_invalid_scopes(
        self,
        url,
        api_client,
        privacy_request_status_pending,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        """
        Test scopes are correct, although we just gave a user this token with the
        correct scopes, the check doesn't mean much
        """

        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "webhook_id": pre_approval_webhooks[0].id,
                        "scopes": [PRIVACY_REQUEST_READ],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_mark_eligible_invalid_webhook(
        self,
        url,
        api_client,
        privacy_request_status_pending,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "webhook_id": "invalid",
                        "scopes": [PRIVACY_REQUEST_REVIEW],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 404

    def test_mark_eligible_nonexistent_privacy_request(
        self,
        url,
        api_client,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        invalid_privacy_request_url = (
            V1_URL_PREFIX
            + PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE.format(privacy_request_id="invalid")
        )
        response = api_client.post(invalid_privacy_request_url, headers=auth_header)
        assert response.status_code == 404

    def test_mark_eligible_privacy_request_not_pending(
        self,
        url,
        db,
        api_client,
        privacy_request_status_pending,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        privacy_request_status_pending.status = PrivacyRequestStatus.approved
        privacy_request_status_pending.save(db=db)

        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 400

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_mark_eligible_but_not_all_webhook_replies_received(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
        privacy_request_review_notification_enabled,
    ):
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        # new webhook reply
        response = api_client.post(url, headers=auth_header)

        assert response.status_code == 200
        assert not submit_mock.called
        assert not mock_dispatch_message.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_mark_eligible_webhook_deleted(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
        privacy_request_review_notification_enabled,
    ):
        """If a webhook is deleted, its eligibility is no longer needed"""
        # mock previous webhook reply
        PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": pre_approval_webhooks[0].id,
                "privacy_request_id": privacy_request_status_pending.id,
                "is_eligible": False,
            },
        )
        pre_approval_webhooks[0].delete(db)

        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )

        # new webhook reply
        response = api_client.post(url, headers=auth_header)

        assert response.status_code == 200
        assert submit_mock.called
        assert mock_dispatch_message.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_mark_eligible_but_some_webhooks_not_eligible(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
        privacy_request_review_notification_enabled,
    ):
        # mock previous webhook reply
        PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": pre_approval_webhooks[0].id,
                "privacy_request_id": privacy_request_status_pending.id,
                "is_eligible": False,
            },
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )

        # new webhook reply
        response = api_client.post(url, headers=auth_header)

        assert response.status_code == 200
        assert not submit_mock.called
        assert not mock_dispatch_message.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_mark_eligible_and_all_webhooks_eligible(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
        privacy_request_review_notification_enabled,
    ):
        # mock previous webhook reply
        PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": pre_approval_webhooks[0].id,
                "privacy_request_id": privacy_request_status_pending.id,
                "is_eligible": True,
            },
        )
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )

        # new webhook reply
        response = api_client.post(url, headers=auth_header)

        assert response.status_code == 200

        approval_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request_status_pending.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()

        assert approval_audit_log is not None
        assert approval_audit_log.message == ""
        assert approval_audit_log.webhook_id == pre_approval_webhooks[1].id

        approval_audit_log.delete(db)

        assert submit_mock.called
        assert mock_dispatch_message.called


class TestMarkPrivacyRequestPreApproveNotEligible:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request_status_pending):
        return V1_URL_PREFIX + PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE.format(
            privacy_request_id=privacy_request_status_pending.id
        )

    def test_mark_not_eligible_not_authenticated(
        self,
        url,
        api_client,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        response = api_client.post(url)
        assert response.status_code == 401

    def test_mark_not_eligible_invalid_jwe_format(
        self,
        url,
        api_client,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps({"unexpected": "format"}), CONFIG.security.app_encryption_key
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_mark_not_eligible_invalid_scopes(
        self,
        url,
        api_client,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        """
        Test scopes are correct, although we just gave a user this token with the
        correct scopes, the check doesn't mean much
        """

        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "webhook_id": pre_approval_webhooks[0].id,
                        "scopes": [PRIVACY_REQUEST_READ],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_mark_not_eligible_invalid_webhook(
        self,
        url,
        api_client,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "webhook_id": "invalid",
                        "scopes": [PRIVACY_REQUEST_REVIEW],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 404

    def test_mark_not_eligible_nonexistent_privacy_request(
        self,
        url,
        api_client,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        invalid_privacy_request_url = (
            V1_URL_PREFIX
            + PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE.format(
                privacy_request_id="invalid"
            )
        )
        response = api_client.post(invalid_privacy_request_url, headers=auth_header)
        assert response.status_code == 404

    def test_mark_not_eligible_privacy_request_not_pending(
        self,
        url,
        db,
        api_client,
        privacy_request_status_pending,
        generate_pre_approval_webhook_auth_header,
        pre_approval_webhooks,
    ):
        privacy_request_status_pending.status = PrivacyRequestStatus.approved
        privacy_request_status_pending.save(db=db)

        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 400

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_mark_not_eligible(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )

        # new webhook reply
        response = api_client.post(url, headers=auth_header)

        assert response.status_code == 200
        assert not submit_mock.called
        assert not mock_dispatch_message.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_mark_not_eligible_with_previous_eligible(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
        pre_approval_webhooks,
        generate_pre_approval_webhook_auth_header,
    ):
        # mock previous webhook reply
        PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": pre_approval_webhooks[0].id,
                "privacy_request_id": privacy_request_status_pending.id,
                "is_eligible": True,
            },
        )

        auth_header = generate_pre_approval_webhook_auth_header(
            webhook=pre_approval_webhooks[1]
        )

        # new webhook reply
        response = api_client.post(url, headers=auth_header)

        assert response.status_code == 200
        assert not submit_mock.called
        assert not mock_dispatch_message.called


class TestDenyPrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_DENY

    @pytest.fixture(autouse=True, scope="function")
    def privacy_request_review_notification_enabled(self, db):
        """Enable request review notification"""
        original_value = CONFIG.notifications.send_request_review_notification
        CONFIG.notifications.send_request_review_notification = True
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.send_request_review_notification = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    def test_deny_privacy_request_not_authenticated(self, url, api_client):
        response = api_client.patch(url)
        assert response.status_code == 401

    def test_deny_privacy_request_bad_scopes(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.patch(url, headers=auth_header)
        assert response.status_code == 403

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_deny_privacy_request_does_not_exist(
        self, submit_mock, db, url, api_client, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])

        body = {"request_ids": ["does_not_exist"]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["succeeded"] == []
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "No privacy request found with id 'does_not_exist'"
        )
        assert not submit_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_deny_completed_privacy_request(
        self, submit_mock, db, url, api_client, generate_auth_header, privacy_request
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db=db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])

        body = {"request_ids": [privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["succeeded"] == []
        assert len(response_body["failed"]) == 1
        assert response_body["failed"][0]["message"] == "Cannot transition status"
        assert response_body["failed"][0]["data"]["status"] == "complete"
        assert not submit_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_deny_deleted_privacy_request(
        self,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        soft_deleted_privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_REVIEW])

        body = {"request_ids": [soft_deleted_privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["succeeded"] == []
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "Cannot transition status for a deleted request"
        )
        assert (
            response_body["failed"][0]["data"]["id"] == soft_deleted_privacy_request.id
        )
        assert not submit_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_deny_privacy_request_without_denial_reason(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request,
    ):
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db=db)

        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }

        body = {"request_ids": [privacy_request.id]}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0
        assert response_body["succeeded"][0]["status"] == "denied"
        assert response_body["succeeded"][0]["id"] == privacy_request.id
        assert response_body["succeeded"][0]["reviewed_at"] is not None
        assert response_body["succeeded"][0]["reviewed_by"] == user.id
        denial_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request.id)
                & (AuditLog.user_id == user.id)
            ),
        ).first()

        call_args = mock_dispatch_message.call_args[1]
        task_kwargs = call_args["kwargs"]
        assert task_kwargs["to_identity"] == Identity(
            email="test@example.com"
        ).model_dump(mode="json")
        assert task_kwargs["service_type"] == MessagingServiceType.mailgun.value

        message_meta = task_kwargs["message_meta"]
        assert (
            message_meta["action_type"]
            == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY
        )
        assert message_meta["body_params"] == RequestReviewDenyBodyParams(
            rejection_reason=None
        ).model_dump(mode="json")
        queue = call_args["queue"]
        assert queue == MESSAGING_QUEUE_NAME

        assert denial_audit_log.message is None

        assert not submit_mock.called  # Shouldn't run! Privacy request was denied

        privacy_request.delete(db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_deny_privacy_request_with_denial_reason(
        self,
        mock_dispatch_message,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request,
    ):
        privacy_request.status = PrivacyRequestStatus.pending
        privacy_request.save(db=db)

        payload = {
            JWE_PAYLOAD_ROLES: user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        denial_reason = "Your request was denied because reasons"
        body = {"request_ids": [privacy_request.id], "reason": denial_reason}
        response = api_client.patch(url, headers=auth_header, json=body)
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0
        assert response_body["succeeded"][0]["status"] == "denied"
        assert response_body["succeeded"][0]["id"] == privacy_request.id
        assert response_body["succeeded"][0]["reviewed_at"] is not None
        assert response_body["succeeded"][0]["reviewed_by"] == user.id
        denial_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request.id)
                & (AuditLog.user_id == user.id)
            ),
        ).first()

        call_args = mock_dispatch_message.call_args[1]
        task_kwargs = call_args["kwargs"]
        assert task_kwargs["to_identity"] == Identity(
            email="test@example.com"
        ).model_dump(mode="json")
        assert task_kwargs["service_type"] == MessagingServiceType.mailgun.value

        message_meta = task_kwargs["message_meta"]
        assert (
            message_meta["action_type"]
            == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY
        )
        assert message_meta["body_params"] == RequestReviewDenyBodyParams(
            rejection_reason=denial_reason
        ).model_dump(mode="json")
        queue = call_args["queue"]
        assert queue == MESSAGING_QUEUE_NAME

        assert denial_audit_log.message == denial_reason

        assert not submit_mock.called  # Shouldn't run! Privacy request was denied

        privacy_request.delete(db)


class TestResumePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_RESUME.format(
            privacy_request_id=privacy_request.id
        )

    def test_resume_privacy_request_not_authenticated(
        self,
        url,
        api_client,
        generate_policy_webhook_auth_header,
        policy_pre_execution_webhooks,
    ):
        response = api_client.post(url)
        assert response.status_code == 401

    def test_resume_privacy_request_invalid_jwe_format(
        self,
        url,
        api_client,
        generate_policy_webhook_auth_header,
        policy_pre_execution_webhooks,
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps({"unexpected": "format"}), CONFIG.security.app_encryption_key
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_resume_privacy_request_invalid_scopes(
        self,
        url,
        api_client,
        generate_policy_webhook_auth_header,
        policy_pre_execution_webhooks,
    ):
        """
        Test scopes are correct, although we just gave a user this token with the
        correct scopes, the check doesn't mean much
        """

        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "webhook_id": policy_pre_execution_webhooks[0].id,
                        "scopes": [PRIVACY_REQUEST_READ],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_resume_privacy_request_invalid_webhook(
        self,
        url,
        api_client,
        generate_policy_webhook_auth_header,
        policy_post_execution_webhooks,
    ):
        """Only can resume execution after Pre-Execution webhooks"""
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "webhook_id": policy_post_execution_webhooks[0].id,
                        "scopes": [PRIVACY_REQUEST_CALLBACK_RESUME],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 404

    def test_resume_privacy_request_not_paused(
        self,
        url,
        api_client,
        generate_policy_webhook_auth_header,
        policy_pre_execution_webhooks,
        privacy_request,
        db,
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db=db)
        auth_header = generate_policy_webhook_auth_header(
            webhook=policy_pre_execution_webhooks[0]
        )
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 400

        privacy_request.delete(db)

    def test_resume_deleted_privacy_request(
        self,
        api_client,
        generate_policy_webhook_auth_header,
        policy_pre_execution_webhooks,
        soft_deleted_privacy_request,
        db,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_RESUME.format(
            privacy_request_id=soft_deleted_privacy_request.id
        )
        soft_deleted_privacy_request.status = PrivacyRequestStatus.paused
        soft_deleted_privacy_request.save(db=db)
        auth_header = generate_policy_webhook_auth_header(
            webhook=policy_pre_execution_webhooks[0]
        )
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == f"Privacy request with id {soft_deleted_privacy_request.id} has been deleted."
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_resume_privacy_request(
        self,
        submit_mock,
        url,
        api_client,
        generate_policy_webhook_auth_header,
        policy_pre_execution_webhooks,
        privacy_request,
        db,
    ):
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.due_date = None
        privacy_request.save(db=db)
        auth_header = generate_policy_webhook_auth_header(
            webhook=policy_pre_execution_webhooks[0]
        )
        response = api_client.post(
            url, headers=auth_header, json={"derived_identity": {}}
        )
        assert response.status_code == 200
        response_body = json.loads(response.text)
        assert submit_mock.called
        assert response_body == {
            "id": privacy_request.id,
            "created_at": stringify_date(privacy_request.created_at),
            "custom_privacy_request_fields": None,
            "custom_privacy_request_fields_approved_at": None,
            "custom_privacy_request_fields_approved_by": None,
            "days_left": None,
            "started_processing_at": stringify_date(
                privacy_request.started_processing_at
            ),
            "finished_processing_at": None,
            "identity_verified_at": None,
            "status": "in_processing",
            "external_id": privacy_request.external_id,
            "identity": None,
            "reviewed_at": None,
            "reviewed_by": None,
            "reviewer": None,
            "source": None,
            "paused_at": None,
            "policy": {
                "execution_timeframe": 7,
                "drp_action": None,
                "key": privacy_request.policy.key,
                "name": privacy_request.policy.name,
                "rules": [
                    rule.model_dump(mode="json")
                    for rule in PolicyResponse.model_validate(
                        privacy_request.policy
                    ).rules
                ],
            },
            "action_required_details": None,
            "resume_endpoint": None,
            "deleted_at": None,
            "deleted_by": None,
        }

        privacy_request.delete(db)


class TestValidateManualInput:
    """Verify pytest cell-var-from-loop warning is a false positive"""

    @pytest.fixture(scope="function")
    @pytest.mark.usefixtures("postgres_example_test_dataset_config")
    def dataset_graph(self, db):
        datasets = DatasetConfig.all(db=db)
        dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
        dataset_graph = DatasetGraph(*dataset_graphs)
        return dataset_graph

    @pytest.mark.usefixtures("postgres_example_test_dataset_config")
    def test_all_fields_match(self, dataset_graph):
        paused_location = CollectionAddress("postgres_example_test_dataset", "address")

        manual_rows = [{"city": "Nashville", "state": "TN"}]
        validate_manual_input(manual_rows, paused_location, dataset_graph)

    @pytest.mark.usefixtures("postgres_example_test_dataset_config")
    def test_one_field_does_not_match(self, dataset_graph):
        paused_location = CollectionAddress("postgres_example_test_dataset", "address")

        manual_rows = [{"city": "Nashville", "state": "TN", "ccn": "aaa-aaa"}]
        with pytest.raises(HTTPException) as exc:
            validate_manual_input(manual_rows, paused_location, dataset_graph)
        assert (
            exc.value.detail
            == "Cannot save manual rows. No 'ccn' field defined on the 'postgres_example_test_dataset:address' collection."
        )

    @pytest.mark.usefixtures("postgres_example_test_dataset_config")
    def test_field_on_second_row_does_not_match(self, dataset_graph):
        paused_location = CollectionAddress("postgres_example_test_dataset", "address")

        manual_rows = [
            {"city": "Nashville", "state": "TN"},
            {"city": "Austin", "misspelled_state": "TX"},
        ]
        with pytest.raises(HTTPException) as exc:
            validate_manual_input(manual_rows, paused_location, dataset_graph)
        assert (
            exc.value.detail
            == "Cannot save manual rows. No 'misspelled_state' field defined on the 'postgres_example_test_dataset:address' collection."
        )


class TestBulkRestartFromFailure:
    @pytest.fixture(scope="function")
    def url(self):
        return f"{V1_URL_PREFIX}{PRIVACY_REQUEST_BULK_RETRY}"

    def test_restart_from_failure_not_authenticated(self, api_client, url):
        data = ["1234", "5678"]
        response = api_client.post(url, json=data, headers={})
        assert response.status_code == 401

    def test_restart_from_failure_wrong_scope(
        self, api_client, url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        data = ["1234", "5678"]

        response = api_client.post(url, json=data, headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.usefixtures("privacy_requests")
    def test_restart_from_failure_not_errored(
        self, api_client, url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        data = ["1234", "5678"]

        response = api_client.post(url, json=data, headers=auth_header)
        assert response.status_code == 200

        assert response.json()["succeeded"] == []

        failed_ids = [
            x["data"]["privacy_request_id"] for x in response.json()["failed"]
        ]
        assert sorted(failed_ids) == sorted(data)

    def test_restart_from_failure_deleted_request(
        self, api_client, url, generate_auth_header, soft_deleted_privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        data = [soft_deleted_privacy_request.id]

        response = api_client.post(url, json=data, headers=auth_header)
        assert response.status_code == 200

        assert response.json()["succeeded"] == []
        assert response.json()["failed"] == [
            {
                "message": "Cannot restart a deleted privacy request",
                "data": {"privacy_request_id": soft_deleted_privacy_request.id},
            }
        ]

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_from_failure_no_stopped_step(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_requests
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        data = [privacy_requests[0].id]

        privacy_requests[0].status = PrivacyRequestStatus.error
        privacy_requests[0].save(db)

        response = api_client.post(url, json=data, headers=auth_header)

        assert response.status_code == 200
        db.refresh(privacy_requests[0])
        assert privacy_requests[0].status == PrivacyRequestStatus.in_processing
        assert response.json()["failed"] == []

        succeeded_ids = [x["id"] for x in response.json()["succeeded"]]

        assert privacy_requests[0].id in succeeded_ids

        # Just restarted from the beginning
        submit_mock.assert_called_with(
            privacy_request_id=privacy_requests[0].id,
            from_step=None,
            from_webhook_id=None,
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_from_failure_from_specific_collection(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_requests
    ):
        """Collection is no longer a relevant parameter here, but its inclusion does not affect
        restarting the privacy request"""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        data = [privacy_requests[0].id]
        privacy_requests[0].status = PrivacyRequestStatus.error
        privacy_requests[0].save(db)

        privacy_requests[0].cache_failed_checkpoint_details(
            step=CurrentStep.access,
        )

        response = api_client.post(url, json=data, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_requests[0])
        assert privacy_requests[0].status == PrivacyRequestStatus.in_processing
        assert response.json()["failed"] == []

        succeeded_ids = [x["id"] for x in response.json()["succeeded"]]

        assert privacy_requests[0].id in succeeded_ids

        submit_mock.assert_called_with(
            privacy_request_id=privacy_requests[0].id,
            from_step=CurrentStep.access.value,
            from_webhook_id=None,
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_from_failure_outside_graph(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_requests
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        data = [privacy_requests[0].id]
        privacy_requests[0].status = PrivacyRequestStatus.error
        privacy_requests[0].save(db)

        privacy_requests[0].cache_failed_checkpoint_details(
            step=CurrentStep.email_post_send,
        )

        response = api_client.post(url, json=data, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_requests[0])
        assert privacy_requests[0].status == PrivacyRequestStatus.in_processing
        assert response.json()["failed"] == []

        succeeded_ids = [x["id"] for x in response.json()["succeeded"]]

        assert privacy_requests[0].id in succeeded_ids

        submit_mock.assert_called_with(
            privacy_request_id=privacy_requests[0].id,
            from_step=CurrentStep.email_post_send.value,
            from_webhook_id=None,
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_mixed_result(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_requests
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        bad_test_id = "bad_test_id"
        data = [privacy_requests[0].id, bad_test_id]
        privacy_requests[0].status = PrivacyRequestStatus.error
        privacy_requests[0].save(db)

        privacy_requests[0].cache_failed_checkpoint_details(
            step=CurrentStep.access,
        )

        response = api_client.post(url, json=data, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_requests[0])
        assert privacy_requests[0].status == PrivacyRequestStatus.in_processing

        succeeded_ids = [x["id"] for x in response.json()["succeeded"]]
        failed_ids = [
            x["data"]["privacy_request_id"] for x in response.json()["failed"]
        ]

        assert privacy_requests[0].id in succeeded_ids
        assert bad_test_id in failed_ids

        submit_mock.assert_called_with(
            privacy_request_id=privacy_requests[0].id,
            from_step=CurrentStep.access.value,
            from_webhook_id=None,
        )


class TestRestartFromFailure:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_RETRY.format(
            privacy_request_id=privacy_request.id
        )

    def test_restart_from_failure_not_authenticated(self, api_client, url):
        response = api_client.post(url, headers={})
        assert response.status_code == 401

    def test_restart_from_failure_wrong_scope(
        self, api_client, url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 403

    def test_restart_from_failure_not_errored(
        self, api_client, url, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Cannot restart privacy request from failure: privacy request '{privacy_request.id}' status = in_processing."
        )

    def test_restart_from_failure_deleted(
        self, api_client, generate_auth_header, db, soft_deleted_privacy_request
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_RETRY.format(
            privacy_request_id=soft_deleted_privacy_request.id
        )
        soft_deleted_privacy_request.status = PrivacyRequestStatus.error
        soft_deleted_privacy_request.save(db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == f"Privacy request with id {soft_deleted_privacy_request.id} has been deleted."
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_from_failure_no_stopped_step(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

        submit_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=None,
            from_webhook_id=None,
        )

        privacy_request.delete(db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_from_failure_from_access_step(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)

        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.access,
        )

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

        submit_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.access.value,
            from_webhook_id=None,
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_from_email_post_send(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)

        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.email_post_send,
        )

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

        submit_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.email_post_send.value,
            from_webhook_id=None,
        )


class TestVerifyIdentity:
    code = "123456"

    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_VERIFY_IDENTITY.format(
            privacy_request_id=privacy_request.id
        )

    @pytest.fixture(scope="function")
    def privacy_request_receipt_notification_enabled(self, db):
        """Enable request receipt"""
        original_value = CONFIG.notifications.send_request_receipt_notification
        CONFIG.notifications.send_request_receipt_notification = True
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.send_request_receipt_notification = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    def test_incorrect_privacy_request_status(self, api_client, url, privacy_request):
        request_body = {"code": self.code}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == f"Invalid identity verification request. Privacy request '{privacy_request.id}' status = in_processing."
        )

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_verification_code_expired(
        self,
        mock_dispatch_message,
        db,
        api_client,
        url,
        privacy_request,
        privacy_request_receipt_notification_enabled,
    ):
        privacy_request.status = PrivacyRequestStatus.identity_unverified
        privacy_request.save(db)

        request_body = {"code": self.code}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == f"Identification code expired for {privacy_request.id}."
        )
        assert not mock_dispatch_message.called

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_invalid_code(
        self,
        mock_dispatch_message,
        db,
        api_client,
        url,
        privacy_request,
        privacy_request_receipt_notification_enabled,
    ):
        privacy_request.status = PrivacyRequestStatus.identity_unverified
        privacy_request.save(db)
        privacy_request.cache_identity_verification_code("999999")

        request_body = {"code": self.code}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 403
        assert (
            resp.json()["detail"]
            == f"Incorrect identification code for '{privacy_request.id}'"
        )
        assert not mock_dispatch_message.called

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_too_many_attempts(
        self,
        mock_dispatch_message,
        db,
        api_client,
        url,
        privacy_request,
        privacy_request_receipt_notification_enabled,
    ):
        VERIFICATION_CODE = "999999"
        privacy_request.status = PrivacyRequestStatus.identity_unverified
        privacy_request.save(db)
        privacy_request.cache_identity_verification_code(VERIFICATION_CODE)

        request_body = {"code": self.code}
        for _ in range(0, CONFIG.security.identity_verification_attempt_limit):
            resp = api_client.post(url, headers={}, json=request_body)
            assert resp.status_code == 403
            assert (
                resp.json()["detail"]
                == f"Incorrect identification code for '{privacy_request.id}'"
            )
            assert not mock_dispatch_message.called

        assert (
            privacy_request._get_cached_verification_code_attempt_count()
            == CONFIG.security.identity_verification_attempt_limit
        )

        request_body = {"code": VERIFICATION_CODE}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 403
        assert resp.json()["detail"] == f"Attempt limit hit for '{privacy_request.id}'"
        assert not mock_dispatch_message.called
        assert privacy_request.get_cached_verification_code() is None
        assert privacy_request._get_cached_verification_code_attempt_count() == 0

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_verify_identity_no_admin_approval_needed(
        self,
        mock_dispatch_message,
        mock_run_privacy_request,
        db,
        api_client,
        url,
        privacy_request,
        privacy_request_receipt_notification_enabled,
    ):
        privacy_request.status = PrivacyRequestStatus.identity_unverified
        privacy_request.save(db)
        privacy_request.cache_identity_verification_code(self.code)

        request_body = {"code": self.code}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 200

        resp = resp.json()
        assert resp["status"] == "pending"
        assert resp["identity_verified_at"] is not None

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.pending
        assert privacy_request.identity_verified_at is not None

        approved_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()

        assert approved_audit_log is not None

        assert mock_run_privacy_request.called

        assert mock_dispatch_message.called

        call_args = mock_dispatch_message.call_args[1]
        task_kwargs = call_args["kwargs"]
        assert task_kwargs["to_identity"] == Identity(
            phone_number="+12345678910", email="test@example.com"
        ).model_dump(mode="json")
        assert task_kwargs["service_type"] == MessagingServiceType.mailgun.value

        message_meta = task_kwargs["message_meta"]
        assert (
            message_meta["action_type"] == MessagingActionType.PRIVACY_REQUEST_RECEIPT
        )
        assert message_meta["body_params"] == RequestReceiptBodyParams(
            request_types={ActionType.access.value}
        ).model_dump(mode="json")
        queue = call_args["queue"]
        assert queue == MESSAGING_QUEUE_NAME

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.trigger_pre_approval_webhook"
    )
    def test_verify_identity_admin_approval_needed_with_pre_approval_webhooks(
        self,
        mock_trigger_pre_approval_webhook,
        mock_dispatch_message,
        mock_run_privacy_request,
        db,
        api_client,
        url,
        privacy_request,
        privacy_request_receipt_notification_enabled,
        require_manual_request_approval,
        pre_approval_webhooks,
    ):
        privacy_request.status = PrivacyRequestStatus.identity_unverified
        privacy_request.save(db)
        privacy_request.cache_identity_verification_code(self.code)

        request_body = {"code": self.code}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 200

        resp = resp.json()
        assert resp["status"] == "pending"
        assert resp["identity_verified_at"] is not None

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.pending
        assert privacy_request.identity_verified_at is not None

        approved_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()

        assert approved_audit_log is None

        assert not mock_run_privacy_request.called

        assert mock_dispatch_message.called

        assert mock_trigger_pre_approval_webhook.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_verify_identity_no_admin_approval_needed_email_disabled(
        self,
        mock_dispatch_message,
        mock_run_privacy_request,
        db,
        api_client,
        url,
        privacy_request,
    ):
        privacy_request.status = PrivacyRequestStatus.identity_unverified
        privacy_request.save(db)
        privacy_request.cache_identity_verification_code(self.code)

        request_body = {"code": self.code}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 200

        resp = resp.json()
        assert resp["status"] == "pending"
        assert resp["identity_verified_at"] is not None

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.pending
        assert privacy_request.identity_verified_at is not None

        approved_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()

        assert approved_audit_log is not None

        assert mock_run_privacy_request.called

        assert not mock_dispatch_message.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_verify_identity_admin_approval_needed(
        self,
        mock_dispatch_message,
        mock_run_privacy_request,
        require_manual_request_approval,
        db,
        api_client,
        url,
        privacy_request,
        privacy_request_receipt_notification_enabled,
    ):
        privacy_request.status = PrivacyRequestStatus.identity_unverified
        privacy_request.save(db)
        privacy_request.cache_identity_verification_code(self.code)

        request_body = {"code": self.code}
        resp = api_client.post(url, headers={}, json=request_body)
        assert resp.status_code == 200

        resp = resp.json()
        assert resp["status"] == "pending"
        assert resp["identity_verified_at"] is not None

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.pending
        assert privacy_request.identity_verified_at is not None

        approved_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == privacy_request.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()

        assert approved_audit_log is None
        assert not mock_run_privacy_request.called

        assert mock_dispatch_message.called

        call_args = mock_dispatch_message.call_args[1]
        task_kwargs = call_args["kwargs"]
        assert task_kwargs["to_identity"] == Identity(
            phone_number="+12345678910", email="test@example.com"
        ).model_dump(mode="json")
        assert task_kwargs["service_type"] == MessagingServiceType.mailgun.value

        message_meta = task_kwargs["message_meta"]
        assert (
            message_meta["action_type"] == MessagingActionType.PRIVACY_REQUEST_RECEIPT
        )
        assert message_meta["body_params"] == RequestReceiptBodyParams(
            request_types={ActionType.access.value}
        ).model_dump(mode="json")
        queue = call_args["queue"]
        assert queue == MESSAGING_QUEUE_NAME


class TestCreatePrivacyRequestEmailVerificationRequired:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    def test_create_privacy_request_no_email_config(
        self,
        url,
        db,
        api_client: TestClient,
        policy,
        subject_identity_verification_required,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["failed"]
        assert len(response_data) == 1
        assert response_data[0]["message"] == "Verification message could not be sent."
        assert (
            response_data[0]["data"]["status"]
            == PrivacyRequestStatus.identity_unverified.value
        )
        pr = PrivacyRequest.get(
            db=db, object_id=response_data[0]["data"]["privacy_request_id"]
        )
        pr.delete(db=db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch("fides.api.service._verification.dispatch_message")
    def test_create_privacy_request_with_email_config(
        self,
        mock_dispatch_message,
        mock_execute_request,
        url,
        db,
        api_client: TestClient,
        policy,
        messaging_config,
        subject_identity_verification_required,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        approval_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == pr.id)
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()
        assert approval_audit_log is None
        assert not mock_execute_request.called

        assert response_data[0]["status"] == PrivacyRequestStatus.identity_unverified

        assert mock_dispatch_message.called
        kwargs = mock_dispatch_message.call_args.kwargs
        assert (
            kwargs["action_type"] == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION
        )
        assert kwargs["to_identity"] == Identity(email="test@example.com")
        assert kwargs["service_type"] == MessagingServiceType.mailgun.value
        assert kwargs["message_body_params"] == SubjectIdentityVerificationBodyParams(
            verification_code=pr.get_cached_verification_code(),
            verification_code_ttl_seconds=CONFIG.redis.identity_verification_code_ttl_seconds,
        )

        pr.delete(db=db)


class TestUploadManualWebhookAccessInputs:
    @pytest.fixture(scope="function")
    def url(
        self,
        db,
        privacy_request_requires_input,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        return V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {"email": "customer-1@example.com", "last_name": "McCustomer"}

    def test_patch_inputs_not_authenticated(self, api_client: TestClient, url):
        response = api_client.patch(url, headers={})
        assert 401 == response.status_code

    def test_patch_inputs_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header, payload
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_READ])
        response = api_client.patch(url, headers=auth_header)
        assert 403 == response.status_code

    def test_patch_inputs_privacy_request_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        payload,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id="bad_privacy_request",
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No privacy request found with id 'bad_privacy_request'."
        )

    def test_patch_inputs_connection_config_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        payload,
        privacy_request_requires_input,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key="bad_connection_key",
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No connection config with key 'bad_connection_key'"
        )

    def test_patch_inputs_manual_webhook_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        payload,
        privacy_request_requires_input,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No access manual webhook exists for connection config with key 'manual_webhook_example'"
        )

    def test_supply_invalid_fields(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        payload,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(
            url, headers=auth_header, json={"bad_field": "value"}
        )
        assert 422 == response.status_code
        assert response.json()["detail"][0]["msg"] == "Extra inputs are not permitted"

    def test_patch_inputs_bad_privacy_request_status(
        self,
        api_client,
        payload,
        generate_auth_header,
        privacy_request,
        integration_manual_webhook_config,
        access_manual_webhook,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert (
            response.json()["detail"]
            == f"Invalid manual webhook access upload request: privacy request '{privacy_request.id}' status = in_processing."
        )

    def test_patch_inputs_for_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        payload,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        assert response.json() is None

        assert (
            privacy_request_requires_input.get_manual_webhook_access_input_strict(
                access_manual_webhook
            )
            == payload
        )


class TestUploadManualWebhookErasureInputs:
    @pytest.fixture(scope="function")
    def url(
        self,
        db,
        privacy_request_requires_input,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        return V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )

    @pytest.fixture(scope="function")
    def payload(self):
        return {"email": False, "last_name": True}

    def test_patch_inputs_not_authenticated(self, api_client: TestClient, url):
        response = api_client.patch(url, headers={})
        assert 401 == response.status_code

    def test_patch_inputs_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header, payload
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_READ])
        response = api_client.patch(url, headers=auth_header)
        assert 403 == response.status_code

    def test_patch_inputs_privacy_request_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        payload,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id="bad_privacy_request",
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No privacy request found with id 'bad_privacy_request'."
        )

    def test_patch_inputs_connection_config_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        payload,
        privacy_request_requires_input,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key="bad_connection_key",
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No connection config with key 'bad_connection_key'"
        )

    def test_patch_inputs_manual_webhook_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        payload,
        privacy_request_requires_input,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No access manual webhook exists for connection config with key 'manual_webhook_example'"
        )

    def test_supply_invalid_fields(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        payload,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(
            url, headers=auth_header, json={"bad_field": "value"}
        )
        assert 422 == response.status_code
        assert response.json()["detail"][0]["msg"] == "Extra inputs are not permitted"

    def test_patch_inputs_bad_privacy_request_status(
        self,
        api_client,
        payload,
        generate_auth_header,
        privacy_request,
        integration_manual_webhook_config,
        access_manual_webhook,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert (
            response.json()["detail"]
            == f"Invalid manual webhook access upload request: privacy request '{privacy_request.id}' status = in_processing."
        )

    def test_patch_inputs_for_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        payload,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_UPLOAD_DATA])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 200 == response.status_code
        assert response.json() is None

        assert (
            privacy_request_requires_input.get_manual_webhook_erasure_input_strict(
                access_manual_webhook
            )
            == payload
        )


class TestGetManualWebhookAccessInputs:
    @pytest.fixture(scope="function")
    def url(
        self,
        db,
        privacy_request_requires_input,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        return V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )

    def test_get_inputs_not_authenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_inputs_wrong_scopes(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_inputs_privacy_request_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id="bad_privacy_request",
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No privacy request found with id 'bad_privacy_request'."
        )

    def test_get_inputs_connection_config_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_requires_input,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key="bad_connection_key",
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No connection config with key 'bad_connection_key'"
        )

    def test_get_inputs_manual_webhook_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_requires_input,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No access manual webhook exists for connection config with key 'manual_webhook_example'"
        )

    def test_get_inputs_bad_privacy_request_status(
        self,
        api_client,
        generate_auth_header,
        privacy_request,
        integration_manual_webhook_config,
        access_manual_webhook,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT.format(
            privacy_request_id=privacy_request.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert (
            response.json()["detail"]
            == f"Invalid manual webhook access upload request: privacy request '{privacy_request.id}' status = in_processing."
        )

    def test_no_manual_webhook_data_exists(
        self,
        api_client,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json() == {
            "checked": False,
            "fields": {"email": None, "last_name": None},
        }

    def test_cached_data_extra_saved_webhook_field(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
        cached_access_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])

        access_manual_webhook.fields = [
            {"pii_field": "id_no", "dsr_package_label": "id_number"}
        ]
        access_manual_webhook.save(db)
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == {
            "checked": False,
            "fields": {"id_number": None},
        }, "Response has checked=False, so this data needs to be re-uploaded before we can run the privacy request."

    def test_cached_data_missing_saved_webhook_field(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
        cached_access_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])

        access_manual_webhook.fields.append(
            {"pii_field": "id_no", "dsr_package_label": "id_number"}
        )
        access_manual_webhook.save(db)
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        assert response.json() == {
            "checked": False,
            "fields": {
                "id_number": None,
                "email": "customer-1@example.com",
                "last_name": "McCustomer",
            },
        }, "Response has checked=False. A new field has been defined on the webhook, so we should re-examine to see if that is more data we need to retrieve."

    def test_get_inputs_for_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
        cached_access_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json() == {
            "checked": True,
            "fields": {
                "email": "customer-1@example.com",
                "last_name": "McCustomer",
            },
        }


class TestGetManualWebhookErasureInputs:
    @pytest.fixture(scope="function")
    def url(
        self,
        db,
        privacy_request_requires_input,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        return V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )

    def test_get_inputs_not_authenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_inputs_wrong_scopes(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_get_inputs_privacy_request_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT.format(
            privacy_request_id="bad_privacy_request",
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No privacy request found with id 'bad_privacy_request'."
        )

    def test_get_inputs_connection_config_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_requires_input,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key="bad_connection_key",
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No connection config with key 'bad_connection_key'"
        )

    def test_get_inputs_manual_webhook_does_not_exist(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request_requires_input,
        integration_manual_webhook_config,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 404 == response.status_code
        assert (
            response.json()["detail"]
            == "No access manual webhook exists for connection config with key 'manual_webhook_example'"
        )

    def test_get_inputs_bad_privacy_request_status(
        self,
        api_client,
        generate_auth_header,
        privacy_request,
        integration_manual_webhook_config,
        access_manual_webhook,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT.format(
            privacy_request_id=privacy_request.id,
            connection_key=integration_manual_webhook_config.key,
        )
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert (
            response.json()["detail"]
            == f"Invalid manual webhook erasure upload request: privacy request '{privacy_request.id}' status = in_processing."
        )

    def test_no_manual_webhook_data_exists(
        self,
        api_client,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json() == {
            "checked": False,
            "fields": {"email": None, "last_name": None},
        }

    def test_cached_data_extra_saved_webhook_field(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
        cached_erasure_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])

        access_manual_webhook.fields = [
            {"pii_field": "id_no", "dsr_package_label": "id_number"}
        ]
        access_manual_webhook.save(db)
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == {
            "checked": False,
            "fields": {"id_number": None},
        }, "Response has checked=False, so this data needs to be re-uploaded before we can run the privacy request."

    def test_cached_data_missing_saved_webhook_field(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
        cached_erasure_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])

        access_manual_webhook.fields.append(
            {"pii_field": "id_no", "dsr_package_label": "id_number"}
        )
        access_manual_webhook.save(db)
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == 200
        assert response.json() == {
            "checked": False,
            "fields": {
                "id_number": None,
                "email": False,
                "last_name": True,
            },
        }, "Response has checked=False. A new field has been defined on the webhook, so we should re-examine to see if that is more data we need to retrieve."

    def test_get_inputs_for_manual_webhook(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
        cached_erasure_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_VIEW_DATA])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json() == {
            "checked": True,
            "fields": {
                "email": False,
                "last_name": True,
            },
        }


class TestResumePrivacyRequestFromRequiresInput:
    @pytest.fixture(scope="function")
    def url(
        self,
        db,
        privacy_request_requires_input,
    ):
        return V1_URL_PREFIX + PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT.format(
            privacy_request_id=privacy_request_requires_input.id,
        )

    def test_resume_from_requires_input_status_not_authenticated(self, url, api_client):
        response = api_client.post(url, headers={})
        assert response.status_code == 401

    def test_resume_from_requires_input_status_not_authorized(
        self, url, privacy_request, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 403

    def test_resume_from_requires_input_status_wrong_status(
        self, api_client, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_CALLBACK_RESUME])
        url = V1_URL_PREFIX + PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT.format(
            privacy_request_id=privacy_request.id,
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Cannot resume privacy request from 'requires_input': privacy request '{privacy_request.id}' status = {privacy_request.status.value}."
        )

    def test_resume_from_requires_input_status_deleted_request(
        self, api_client, generate_auth_header, soft_deleted_privacy_request
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_CALLBACK_RESUME])
        url = V1_URL_PREFIX + PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT.format(
            privacy_request_id=soft_deleted_privacy_request.id,
        )
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == f"Privacy request with id {soft_deleted_privacy_request.id} has been deleted."
        )

    def test_resume_from_requires_input_status_missing_cached_data(
        self,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_CALLBACK_RESUME])

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Cannot resume privacy request. No data cached for privacy_request_id '{privacy_request_requires_input.id}' for connection config '{integration_manual_webhook_config.key}'"
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_resume_from_requires_input_status_data_empty_but_confirmed(
        self,
        run_privacy_request_mock,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request_requires_input.cache_manual_webhook_access_input(
            access_manual_webhook,
            {},
        )

        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json()["status"] == PrivacyRequestStatus.in_processing
        assert run_privacy_request_mock.called

        call_kwargs = run_privacy_request_mock.call_args.kwargs
        assert call_kwargs["privacy_request_id"] == privacy_request_requires_input.id
        assert call_kwargs["from_webhook_id"] is None
        assert call_kwargs["from_step"] is None

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_resume_from_requires_input_status(
        self,
        run_privacy_request_mock,
        api_client: TestClient,
        db,
        url,
        generate_auth_header,
        access_manual_webhook,
        integration_manual_webhook_config,
        privacy_request_requires_input,
        cached_access_input,
    ):
        auth_header = generate_auth_header([PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        assert response.json()["status"] == PrivacyRequestStatus.in_processing
        assert run_privacy_request_mock.called

        call_kwargs = run_privacy_request_mock.call_args.kwargs
        assert call_kwargs["privacy_request_id"] == privacy_request_requires_input.id
        assert call_kwargs["from_webhook_id"] is None
        assert call_kwargs["from_step"] is None


class TestCreatePrivacyRequestEmailReceiptNotification:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    @pytest.fixture(scope="function")
    def privacy_request_receipt_notification_enabled(self, db):
        """Enable request receipt notification"""
        original_value = CONFIG.notifications.send_request_receipt_notification
        CONFIG.notifications.send_request_receipt_notification = True
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.notifications.send_request_receipt_notification = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_create_privacy_request_no_email_config(
        self,
        mock_dispatch_message,
        mock_execute_request,
        url,
        db,
        api_client: TestClient,
        policy,
        privacy_request_receipt_notification_enabled,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])

        assert mock_execute_request.called
        assert response_data[0]["status"] == PrivacyRequestStatus.pending

        assert mock_dispatch_message.called

        call_args = mock_dispatch_message.call_args[1]
        task_kwargs = call_args["kwargs"]
        assert task_kwargs["to_identity"] == Identity(
            email="test@example.com"
        ).model_dump(mode="json")
        assert task_kwargs["service_type"] == MessagingServiceType.mailgun.value

        message_meta = task_kwargs["message_meta"]
        assert (
            message_meta["action_type"] == MessagingActionType.PRIVACY_REQUEST_RECEIPT
        )
        assert message_meta["body_params"] == RequestReceiptBodyParams(
            request_types={ActionType.access.value}
        ).model_dump(mode="json")
        queue = call_args["queue"]
        assert queue == MESSAGING_QUEUE_NAME

        pr.delete(db=db)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.dispatch_message_task.apply_async"
    )
    def test_create_privacy_request_with_email_config(
        self,
        mock_dispatch_message,
        mock_execute_request,
        url,
        db,
        api_client: TestClient,
        policy,
        messaging_config,
        privacy_request_receipt_notification_enabled,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert mock_execute_request.called

        assert response_data[0]["status"] == PrivacyRequestStatus.pending
        assert mock_dispatch_message.called

        call_args = mock_dispatch_message.call_args[1]
        task_kwargs = call_args["kwargs"]
        assert task_kwargs["to_identity"] == Identity(
            email="test@example.com"
        ).model_dump(mode="json")
        assert task_kwargs["service_type"] == MessagingServiceType.mailgun.value

        message_meta = task_kwargs["message_meta"]
        assert (
            message_meta["action_type"] == MessagingActionType.PRIVACY_REQUEST_RECEIPT
        )
        assert message_meta["body_params"] == RequestReceiptBodyParams(
            request_types={ActionType.access.value}
        ).model_dump(mode="json")
        queue = call_args["queue"]
        assert queue == MESSAGING_QUEUE_NAME

        pr.delete(db=db)


class TestCreatePrivacyRequestAuthenticated:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return f"{V1_URL_PREFIX}{PRIVACY_REQUEST_AUTHENTICATED}"

    @pytest.fixture
    def verification_config(self, db):
        original = CONFIG.execution.subject_identity_verification_required
        CONFIG.execution.subject_identity_verification_required = True
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.execution.subject_identity_verification_required = original
        ApplicationConfig.update_config_set(db, CONFIG)

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request(
        self,
        run_access_request_mock,
        url,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert run_access_request_mock.called

    @pytest.mark.parametrize(
        "source, expected_submitted_by",
        [
            (PrivacyRequestSource.request_manager, lambda user: user.client.user_id),
            (PrivacyRequestSource.privacy_center, lambda _: None),
            (None, lambda _: None),
        ],
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_request_manager_privacy_request_stores_submitted_by(
        self,
        run_access_request_mock,
        db,
        url,
        api_client,
        owner_user,
        policy,
        source,
        expected_submitted_by,
    ):
        auth_header = generate_role_header_for_user(
            owner_user, roles=owner_user.permissions.roles
        )
        data = [
            {
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
                "source": source,
            }
        ]
        resp = api_client.post(
            url,
            headers=auth_header,
            json=data,
        )
        assert resp.status_code == 200

        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.submitted_by == expected_submitted_by(owner_user)

        pr.delete(db=db)
        assert run_access_request_mock.called

    @pytest.mark.usefixtures("verification_config")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_bypass_verification(
        self,
        run_access_request_mock,
        url,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert run_access_request_mock.called

    def test_create_privacy_requests_unauthenticated(
        self, api_client: TestClient, url, policy
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        response = api_client.post(url, json=data, headers={})
        assert 401 == response.status_code

    def test_create_privacy_requests_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url, policy
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.post(url, json=data, headers=auth_header)
        assert 403 == response.status_code

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_stores_identities(
        self,
        run_access_request_mock,
        url,
        db,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        TEST_EMAIL = "test@example.com"
        TEST_PHONE_NUMBER = "+12345678910"
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {
                    "email": TEST_EMAIL,
                    "phone_number": TEST_PHONE_NUMBER,
                },
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        persisted_identity = pr.get_persisted_identity()
        assert persisted_identity.email == TEST_EMAIL
        assert persisted_identity.phone_number == TEST_PHONE_NUMBER
        assert run_access_request_mock.called

    @pytest.mark.usefixtures("require_manual_request_approval")
    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_require_manual_approval(
        self,
        run_access_request_mock,
        url,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["status"] == "pending"
        assert not run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_with_masking_configuration(
        self,
        run_access_request_mock,
        url,
        generate_auth_header,
        api_client: TestClient,
        erasure_policy_string_rewrite,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": erasure_policy_string_rewrite.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.access_runner"
    )
    def test_create_privacy_request_limit_exceeded(
        self,
        _,
        url,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        payload = []
        for _ in range(0, 51):
            payload.append(
                {
                    "requested_at": "2021-08-30T16:09:37.359Z",
                    "policy_key": policy.key,
                    "identity": {"email": "ftest{i}@example.com"},
                },
            )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        response = api_client.post(url, json=payload, headers=auth_header)

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "List should have at most 50 items after validation, not 51"
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_starts_processing(
        self,
        run_privacy_request_mock,
        url,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert run_privacy_request_mock.called
        assert resp.status_code == 200

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_with_external_id(
        self,
        run_access_request_mock,
        url,
        db,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        external_id = "ext_some-uuid-here-1234"
        data = [
            {
                "external_id": external_id,
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["external_id"] == external_id
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.external_id == external_id
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_caches_identity(
        self,
        run_access_request_mock,
        url,
        db,
        generate_auth_header,
        api_client: TestClient,
        policy,
        cache,
    ):
        identity = {"email": "test@example.com"}
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": identity,
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.get_cached_identity_data() == identity
        assert run_access_request_mock.called

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_caches_masking_secrets(
        self,
        run_erasure_request_mock,
        url,
        db,
        generate_auth_header,
        api_client: TestClient,
        erasure_policy_aes,
        cache,
    ):
        identity = {"email": "test@example.com"}
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": erasure_policy_aes.key,
                "identity": identity,
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        secret_key = get_masking_secret_cache_key(
            privacy_request_id=pr.id,
            masking_strategy="aes_encrypt",
            secret_type=SecretType.key,
        )
        assert cache.get_encoded_by_key(secret_key) is not None
        assert run_erasure_request_mock.called

    def test_create_privacy_request_invalid_encryption_values(
        self, url, generate_auth_header, api_client: TestClient, policy  # , cache
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
                "encryption_key": "test",
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 422
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, Encryption key must be 16 bytes long"
        )

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_caches_encryption_keys(
        self,
        run_access_request_mock,
        url,
        db,
        generate_auth_header,
        api_client: TestClient,
        policy,
        cache,
    ):
        identity = {"email": "test@example.com"}
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": identity,
                "encryption_key": "test--encryption",
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        encryption_key = get_encryption_cache_key(
            privacy_request_id=pr.id,
            encryption_attr="key",
        )
        assert cache.get(encryption_key) == "test--encryption"
        assert run_access_request_mock.called

    def test_create_privacy_request_no_identities(
        self,
        url,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 0
        response_data = resp.json()["failed"]
        assert len(response_data) == 1

    def test_create_privacy_request_registers_async_task(
        self,
        db,
        url,
        generate_auth_header,
        api_client,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        assert pr.get_cached_task_id() is not None
        assert pr.get_async_execution_task() is not None

    @mock.patch(
        "fides.api.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_creates_system_audit_log(
        self,
        run_access_request_mock,
        url,
        db,
        generate_auth_header,
        api_client: TestClient,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "test@example.com"},
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        response_data = resp.json()["succeeded"][0]
        approval_audit_log: AuditLog = AuditLog.filter(
            db=db,
            conditions=(
                (AuditLog.privacy_request_id == response_data["id"])
                & (AuditLog.action == AuditLogAction.approved)
            ),
        ).first()
        assert approval_audit_log is not None
        assert approval_audit_log.user_id == "system"
        assert run_access_request_mock.called


@pytest.mark.integration
class TestPrivacyRequestDataTransfer:

    @pytest.mark.usefixtures("postgres_integration_db")
    async def test_privacy_request_data_transfer(
        self,
        api_client: TestClient,
        privacy_request,
        generate_auth_header,
        policy,
        db,
        postgres_example_test_dataset_config_read_access,
    ):
        pr = privacy_request.save(db=db)
        merged_graph = postgres_example_test_dataset_config_read_access.get_graph()
        graph = DatasetGraph(merged_graph)

        # execute the privacy request to mimic the expected workflow on the "child"
        # this will populate the access results in the cache, which is required for the
        # transfer endpoint to work
        access_runner(
            privacy_request,
            policy,
            graph,
            ConnectionConfig.all(db=db),
            {"email": "customer-1@example.com"},
            db,
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_TRANSFER])
        rules = policy.get_rules_for_action(action_type=ActionType.access)
        response = api_client.get(
            f"{V1_URL_PREFIX}{PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=pr.id, rule_key=rules[0].key)}",
            headers=auth_header,
        )

        # assert we've got some of our expected data in the response,
        # in the shape we expect
        response_data: dict = response.json()
        assert "postgres_example_test_dataset:address" in response_data.keys()
        assert response_data["postgres_example_test_dataset:address"] == [
            {
                "city": "Exampletown",
                "state": "NY",
                "street": "Example Street",
                "zip": "12345",
                "house": 123,
            },
            {
                "city": "Exampletown",
                "state": "NY",
                "street": "Example Lane",
                "zip": "12321",
                "house": 4,
            },
        ]
        assert "postgres_example_test_dataset:customer" in response_data.keys()
        assert response_data["postgres_example_test_dataset:customer"] == [
            {"name": "John Customer", "email": "customer-1@example.com", "id": 1}
        ]

    def test_privacy_request_data_transfer_wrong_scope(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        db,
    ):
        pr = privacy_request.save(db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(
            f"{V1_URL_PREFIX}{PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=pr.id, rule_key='test_rule')}",
            headers=auth_header,
        )

        assert response.status_code == 403

    def test_privacy_request_data_transfer_not_authenticated(
        self,
        api_client: TestClient,
        privacy_request,
        db,
    ):
        pr = privacy_request.save(db)
        response = api_client.get(
            f"{V1_URL_PREFIX}{PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=pr.id, rule_key='test_rule')}"
        )

        assert response.status_code == 401


class TestCreatePrivacyRequestErrorNotification:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return f"{V1_URL_PREFIX}{PRIVACY_REQUEST_NOTIFICATIONS}"

    def test_get_privacy_request_notification_info(
        self,
        url,
        generate_auth_header,
        db,
        api_client,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_NOTIFICATIONS_READ])
        data = {
            "email": "some@email.com, another@email.com",
            "notify_after_failures": 5,
        }

        expected = {
            "email_addresses": ["some@email.com", "another@email.com"],
            "notify_after_failures": 5,
        }

        PrivacyRequestNotifications.create(db=db, data=data)

        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == expected

    def test_get_privacy_requests_notification_info_unauthenticated(
        self, api_client, url
    ):
        response = api_client.get(url)
        assert response.status_code == 401

    def test_get_privacy_requests_notification_info_wrong_scope(
        self, api_client, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_create_privacy_request_notification_info(
        self,
        url,
        generate_auth_header,
        api_client,
    ):
        auth_header = generate_auth_header(
            scopes=[PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE]
        )

        data = {
            "email_addresses": ["some@email.com", "another@email.com"],
            "notify_after_failures": 5,
        }

        response = api_client.put(url, json=data, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == data

    def test_create_privacy_request_notification_info_deletes_addresses(
        self,
        url,
        generate_auth_header,
        api_client,
        db,
    ):
        PrivacyRequestNotifications.create(
            db=db,
            data={
                "email": "test@email.com, test2@email.com",
                "notify_after_failures": 10,
            },
        )
        auth_header = generate_auth_header(
            scopes=[PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE]
        )

        data = {
            "email_addresses": [],
            "notify_after_failures": 5,
        }

        response = api_client.put(url, json=data, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == data

        info = PrivacyRequestNotifications.all(db)
        assert info == []

    def test_create_privacy_request_notification_info_no_addresses(
        self,
        url,
        generate_auth_header,
        api_client,
    ):
        auth_header = generate_auth_header(
            scopes=[PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE]
        )

        data = {
            "email_addresses": [],
            "notify_after_failures": 1,
        }

        response = api_client.put(url, json=data, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == data

    def test_create_privacy_requests_notification_info_unauthenticated(
        self, api_client, url
    ):
        response = api_client.put(url)
        assert response.status_code == 401

    def test_create_privacy_requests_notification_info_wrong_scope(
        self, api_client, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.put(url, headers=auth_header)
        assert response.status_code == 403

    def test_update_privacy_request_notification_info(
        self,
        url,
        db,
        generate_auth_header,
        api_client,
    ):
        PrivacyRequestNotifications.create(
            db=db, data={"email": "me@email.com", "notify_after_failures": 1}
        )
        auth_header = generate_auth_header(
            scopes=[PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE]
        )
        data = {
            "email_addresses": ["some@email.com", "another@email.com"],
            "notify_after_failures": 5,
        }

        response = api_client.put(url, json=data, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == data


class TestPrivacyRequestTasksList:
    @pytest.fixture(scope="function")
    def url(self, privacy_request) -> str:
        return V1_URL_PREFIX + REQUEST_TASKS.format(
            privacy_request_id=privacy_request.id
        )

    def test_get_request_tasks_unauthenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 401 == response.status_code

    def test_get_request_tasks_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert 403 == response.status_code

    def test_no_tasks(self, api_client, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        assert response.json() == []

    def test_get_request_tasks(
        self, api_client: TestClient, generate_auth_header, url, request_task
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert len(response.json()) == 3
        resp = response.json()
        root_response = resp[0]
        assert root_response["collection_address"] == "__ROOT__:__ROOT__"
        assert resp[1]["collection_address"] == "test_dataset:test_collection"
        assert resp[2]["collection_address"] == "__TERMINATE__:__TERMINATE__"

        assert root_response["upstream_tasks"] == []
        assert root_response["downstream_tasks"] == ["test_dataset:test_collection"]
        assert root_response["status"] == "complete"
        assert root_response["action_type"] == "access"

        # No DSR data is returned in the response
        assert set(root_response.keys()) == {
            "id",
            "collection_address",
            "status",
            "created_at",
            "updated_at",
            "upstream_tasks",
            "downstream_tasks",
            "action_type",
        }

    def test_get_async_tasks(
        self, db, api_client: TestClient, generate_auth_header, url, request_task
    ):
        request_task.status = ExecutionLogStatus.awaiting_processing
        request_task.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code
        assert len(response.json()) == 3
        resp = response.json()
        root_response = resp[0]
        assert root_response["collection_address"] == "__ROOT__:__ROOT__"
        assert resp[1]["collection_address"] == "test_dataset:test_collection"
        assert resp[2]["collection_address"] == "__TERMINATE__:__TERMINATE__"

        assert root_response["upstream_tasks"] == []
        assert root_response["downstream_tasks"] == ["test_dataset:test_collection"]
        assert root_response["status"] == "complete"
        assert root_response["action_type"] == "access"

        assert resp[1]["status"] == "awaiting_processing"

        # No DSR data is returned in the response
        assert set(root_response.keys()) == {
            "id",
            "collection_address",
            "status",
            "created_at",
            "updated_at",
            "upstream_tasks",
            "downstream_tasks",
            "action_type",
        }


class TestRequeuePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, privacy_request, request_task) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUEST_REQUEUE.format(
            privacy_request_id=privacy_request.id
        )

    def test_requeue_privacy_request_unauthenticated(self, api_client: TestClient, url):
        response = api_client.post(url, headers={})
        assert 401 == response.status_code

    def test_requeue_privacy_request_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code

    def test_requeue_privacy_request_privacy_request_not_found(
        self, api_client: TestClient, generate_auth_header, url, request_task
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_REQUEUE.format(
            privacy_request_id="adsf", task_id=request_task.id
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 404 == response.status_code

    def test_requeue_privacy_request_already_completed(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        url,
        privacy_request,
        request_task,
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db)
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 400 == response.status_code
        assert (
            response.json()["detail"]
            == f"Request failed. Cannot re-queue privacy request {privacy_request.id} with status {privacy_request.status.value}"
        )

    def test_requeue_deleted_privacy_request(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        soft_deleted_privacy_request,
        request_task,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_REQUEUE.format(
            privacy_request_id=soft_deleted_privacy_request.id
        )
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 422 == response.status_code
        assert (
            response.json()["detail"]
            == f"Privacy request with id {soft_deleted_privacy_request.id} has been deleted."
        )

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_privacy_request"
    )
    def test_requeue_privacy_request_from_cached_failure_point(
        self,
        queue_privacy_request_mock,
        privacy_request,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        privacy_request.cache_failed_checkpoint_details(
            step=CurrentStep.erasure,
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        assert queue_privacy_request_mock.called
        queue_privacy_request_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.erasure.value,
        )

    @pytest.mark.usefixtures("consent_request_task")
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_privacy_request"
    )
    def test_requeue_privacy_request_with_consent_tasks(
        self,
        queue_privacy_request_mock,
        privacy_request,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        assert queue_privacy_request_mock.called
        queue_privacy_request_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.consent.value,
        )

    @pytest.mark.usefixtures("erasure_request_task", "request_task")
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_privacy_request"
    )
    def test_requeue_privacy_request_with_erasure_tasks(
        self,
        queue_privacy_request_mock,
        db,
        privacy_request,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        terminate_access_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )
        terminate_access_task.status = ExecutionLogStatus.complete
        terminate_access_task.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        assert queue_privacy_request_mock.called
        queue_privacy_request_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.erasure.value,
        )

    @pytest.mark.usefixtures("erasure_request_task", "request_task")
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_privacy_request"
    )
    def test_requeue_privacy_request_erasure_tasks_but_access_step_not_complete(
        self,
        queue_privacy_request_mock,
        privacy_request,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        assert queue_privacy_request_mock.called
        queue_privacy_request_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.access.value,
        )

    @pytest.mark.usefixtures("request_task")
    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_privacy_request"
    )
    def test_requeue_privacy_request_with_access_tasks(
        self,
        queue_privacy_request_mock,
        privacy_request,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header)
        assert 200 == response.status_code
        assert queue_privacy_request_mock.called
        queue_privacy_request_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.access.value,
        )


class TestRequestTaskAsyncCallback:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + REQUEST_TASK_CALLBACK

    def test_request_task_async_callback_unauthenticated(
        self, api_client: TestClient, url
    ):
        response = api_client.post(url, headers={})
        assert 401 == response.status_code
        assert response.json()["detail"] == "Failed to authenticate"

    def test_request_task_async_callback_invalid_request_task_in_jwe(
        self, api_client: TestClient, url
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "request_task_id": "bad_id",
                        "scopes": [PRIVACY_REQUEST_CALLBACK_RESUME],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }

        response = api_client.post(url, headers=auth_header)
        assert 404 == response.status_code
        assert response.json()["detail"] == "No Request Task found with id 'bad_id'."

    def test_request_task_async_callback_invalid_scope_in_jwe(
        self, api_client: TestClient, url, request_task
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "request_task_id": request_task.id,
                        "scopes": [PRIVACY_REQUEST_READ],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }

        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code
        assert response.json()["detail"] == "Not Authorized for this action"

    def test_request_task_async_callback_unsupported_data_in_jwe(
        self, api_client: TestClient, url
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "webhook_id": "test_webhook_id",
                        "scopes": [PRIVACY_REQUEST_READ],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                CONFIG.security.app_encryption_key,
            )
        }

        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code
        assert response.json()["detail"] == "Not Authorized for this action"

    def test_request_task_async_callback_jwe_encrypted_with_invalid_token(
        self, api_client: TestClient, url, request_task
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps(
                    {
                        "request_task_id": request_task.id,
                        "scopes": [PRIVACY_REQUEST_CALLBACK_RESUME],
                        "iat": datetime.now().isoformat(),
                    }
                ),
                "1MBlw12k9EIjEBVMnL6Myy4lTDpw41c4",
            )
        }

        response = api_client.post(url, headers=auth_header)
        assert 403 == response.status_code
        assert response.json()["detail"] == "Not Authorized for this action"

    def test_request_task_async_callback_invalid_privacy_request_status(
        self, db, api_client: TestClient, url, request_task, privacy_request
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db)

        auth_header = {
            "Authorization": "Bearer "
            + generate_request_task_callback_jwe(request_task)
        }

        response = api_client.post(url, headers=auth_header, json={})
        assert 400 == response.status_code
        assert (
            response.json()["detail"]
            == f"Callback failed. Cannot queue access task '{request_task.id}' with privacy request status 'complete'"
        )

    def test_request_task_async_callback_invalid_request_task_status(
        self, api_client: TestClient, url, request_task
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_request_task_callback_jwe(request_task)
        }

        response = api_client.post(url, headers=auth_header, json={})
        assert 400 == response.status_code
        assert (
            response.json()["detail"]
            == f"Callback failed. Cannot queue access task '{request_task.id}' with request task status 'pending'"
        )

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_request_task",
    )
    def test_request_task_async_callback_no_results_supplied(
        self,
        mock_queue_request_task,
        db,
        api_client: TestClient,
        url,
        request_task,
        privacy_request,
    ):
        """Hitting this endpoint with an empty json result will still resume privacy request processing.
        Hitting this endpoint is assumed to mean the async action was completed"""
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        request_task.status = ExecutionLogStatus.awaiting_processing
        request_task.save(db)

        auth_header = {
            "Authorization": "Bearer "
            + generate_request_task_callback_jwe(request_task)
        }

        response = api_client.post(url, headers=auth_header, json={})
        assert 200 == response.status_code
        assert response.json() == {"task_queued": True}
        assert mock_queue_request_task.called

        db.refresh(request_task)
        assert request_task.callback_succeeded
        assert request_task.access_data is None
        assert request_task.rows_masked is None
        assert request_task.get_access_data() == []

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_request_task",
    )
    def test_request_task_async_callback_access_data_supplied(
        self, _, db, api_client: TestClient, url, request_task, privacy_request
    ):
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        request_task.status = ExecutionLogStatus.awaiting_processing
        request_task.save(db)

        auth_header = {
            "Authorization": "Bearer "
            + generate_request_task_callback_jwe(request_task)
        }

        response = api_client.post(
            url,
            headers=auth_header,
            json={"access_results": [{"id": 1, "user_id": "abcde", "state": "VA"}]},
        )
        assert 200 == response.status_code
        assert response.json() == {"task_queued": True}

        db.refresh(request_task)
        assert request_task.callback_succeeded
        assert request_task.get_access_data() == [
            {"id": 1, "user_id": "abcde", "state": "VA"}
        ]

    def test_request_task_async_callback_incorrect_format_of_access_data_supplied(
        self, db, api_client: TestClient, url, request_task, privacy_request
    ):
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        request_task.status = ExecutionLogStatus.awaiting_processing
        request_task.save(db)

        auth_header = {
            "Authorization": "Bearer "
            + generate_request_task_callback_jwe(request_task)
        }

        response = api_client.post(
            url,
            headers=auth_header,
            json={"access_results": {"id": 1, "user_id": "abcde", "state": "VA"}},
        )
        assert 422 == response.status_code

    @mock.patch(
        "fides.api.api.v1.endpoints.privacy_request_endpoints.queue_request_task",
    )
    def test_erasure_request_task_async_callback(
        self,
        mock_queue_request_task,
        db,
        api_client: TestClient,
        url,
        erasure_request_task,
        privacy_request,
    ):
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        erasure_request_task.status = ExecutionLogStatus.awaiting_processing
        erasure_request_task.save(db)

        auth_header = {
            "Authorization": "Bearer "
            + generate_request_task_callback_jwe(erasure_request_task)
        }

        response = api_client.post(url, headers=auth_header, json={"rows_masked": 2})
        assert 200 == response.status_code
        assert response.json() == {"task_queued": True}

        assert mock_queue_request_task.called

        db.refresh(erasure_request_task)
        assert erasure_request_task.callback_succeeded
        assert erasure_request_task.access_data is None
        assert erasure_request_task.rows_masked == 2


class TestSoftDeletePrivacyRequest:
    def test_soft_delete_privacy_request_unauthenticated(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SOFT_DELETE.format(
            privacy_request_id=privacy_request.id
        )
        response = api_client.post(url)
        assert response.status_code == 401

    def test_soft_delete_privacy_request_bad_scopes(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
        generate_auth_header,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SOFT_DELETE.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 403

    def test_soft_delete_privacy_request_no_user_on_client(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        db,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SOFT_DELETE.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_DELETE])
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.deleted_at is not None
        assert privacy_request.deleted_by is None  # No user on the client

    def test_soft_delete_privacy_request(
        self,
        api_client: TestClient,
        generate_auth_header,
        owner_user,
        privacy_request,
        db,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SOFT_DELETE.format(
            privacy_request_id=privacy_request.id
        )
        payload = {
            JWE_PAYLOAD_ROLES: owner_user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: owner_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.deleted_at is not None
        assert privacy_request.deleted_by == owner_user.id

    def test_soft_delete_privacy_request_already_deleted(
        self,
        api_client: TestClient,
        generate_auth_header,
        owner_user,
        soft_deleted_privacy_request,
        db,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_SOFT_DELETE.format(
            privacy_request_id=soft_deleted_privacy_request.id
        )
        payload = {
            JWE_PAYLOAD_ROLES: owner_user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: owner_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == f"Privacy request with id {soft_deleted_privacy_request.id} has been deleted."
        )


class TestBulkSoftDeletePrivacyRequest:
    def test_bulk_soft_delete_privacy_request_unauthenticated(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_BULK_SOFT_DELETE
        response = api_client.post(url, json={"request_ids": [privacy_request.id]})
        assert response.status_code == 401

    def test_bulk_soft_delete_privacy_request_bad_scopes(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
        generate_auth_header,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_BULK_SOFT_DELETE
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.post(
            url, json={"request_ids": [privacy_request.id]}, headers=auth_header
        )
        assert response.status_code == 403

    def test_bulk_soft_delete_privacy_request_no_user_on_client(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_requests,
        db,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_BULK_SOFT_DELETE
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_DELETE])
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "request_ids": [privacy_requests[0].id, privacy_requests[2].id],
            },
        )
        assert response.status_code == 200

        assert len(response.json()["failed"]) == 0
        assert len(response.json()["succeeded"]) == 2
        success_ids = response.json()["succeeded"]
        assert privacy_requests[0].id in success_ids
        assert privacy_requests[2].id in success_ids

        for privacy_request in privacy_requests:
            db.refresh(privacy_request)

        # First and third requests should have been deleted
        assert privacy_requests[0].deleted_at is not None
        assert privacy_requests[0].deleted_by is None  # No user on the client

        assert privacy_requests[2].deleted_at is not None
        assert privacy_requests[2].deleted_by is None  # No user on the client

        # Second request shouldn't be deleted
        assert privacy_requests[1].deleted_at is None
        assert privacy_requests[1].deleted_by is None

    def test_bulk_soft_delete_privacy_request(
        self,
        api_client: TestClient,
        generate_auth_header,
        owner_user,
        privacy_requests,
        db,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_BULK_SOFT_DELETE
        payload = {
            JWE_PAYLOAD_ROLES: owner_user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: owner_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "request_ids": [privacy_requests[0].id, privacy_requests[2].id],
            },
        )
        assert response.status_code == 200
        assert len(response.json()["failed"]) == 0
        assert len(response.json()["succeeded"]) == 2
        success_ids = response.json()["succeeded"]
        assert privacy_requests[0].id in success_ids
        assert privacy_requests[2].id in success_ids

        for privacy_request in privacy_requests:
            db.refresh(privacy_request)

        # First and third requests should have been deleted
        assert privacy_requests[0].deleted_at is not None
        assert privacy_requests[0].deleted_by == owner_user.id

        assert privacy_requests[2].deleted_at is not None
        assert privacy_requests[2].deleted_by == owner_user.id

        # Second request shouldn't be deleted
        assert privacy_requests[1].deleted_at is None
        assert privacy_requests[1].deleted_by is None

    def test_bulk_soft_delete_privacy_request_already_deleted(
        self,
        api_client: TestClient,
        generate_auth_header,
        owner_user,
        soft_deleted_privacy_request,
        privacy_request,
        db,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_BULK_SOFT_DELETE
        payload = {
            JWE_PAYLOAD_ROLES: owner_user.client.roles,
            JWE_PAYLOAD_CLIENT_ID: owner_user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
        }
        response = api_client.post(
            url,
            headers=auth_header,
            json={
                "request_ids": [soft_deleted_privacy_request.id, privacy_request.id],
            },
        )
        assert response.status_code == 200
        assert response.json()["failed"] == [
            {
                "message": f"Privacy request '{soft_deleted_privacy_request.id}' has already been deleted.",
                "data": {"privacy_request_id": soft_deleted_privacy_request.id},
            }
        ]
        assert len(response.json()["succeeded"]) == 1
        assert response.json()["succeeded"][0] == privacy_request.id


class TestGetAccessResults:
    def test_get_access_results_unauthenticated(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        response = api_client.get(url)
        assert response.status_code == 401

    def test_get_access_results_bad_scopes(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
        generate_auth_header,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_access_results_approver(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
        approver_user,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            approver_user, roles=approver_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_access_results_approver(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
        approver_user,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            approver_user, roles=approver_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_access_results_viewer(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
        viewer_user,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            viewer_user, roles=viewer_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_access_results_viewer_and_approver(
        self,
        api_client: TestClient,
        privacy_request: PrivacyRequest,
        viewer_and_approver_user,
    ):
        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            viewer_and_approver_user, roles=viewer_and_approver_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_access_results_request_not_complete(
        self,
        privacy_request: PrivacyRequest,
        api_client: TestClient,
        owner_user,
        db,
    ):
        privacy_request.status = PrivacyRequestStatus.in_processing
        privacy_request.save(db)

        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            owner_user, roles=owner_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 400
        assert response.json() == {
            "detail": f"Access results for privacy request '{privacy_request.id}' are not available because the request is not complete."
        }

    def test_get_access_results_no_data(
        self,
        privacy_request: PrivacyRequest,
        api_client: TestClient,
        db,
        owner_user,
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db)

        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            owner_user, roles=owner_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == {
            "access_result_urls": [],
        }

    def test_get_access_results_owner(
        self,
        privacy_request: PrivacyRequest,
        api_client: TestClient,
        owner_user,
        db,
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.access_result_urls = {
            "access_result_urls": [
                "https://example.com/access_results1",
                "https://example.com/access_results2",
            ]
        }
        privacy_request.save(db)

        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            owner_user, roles=owner_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert response.json() == {
            "access_result_urls": [
                "https://example.com/access_results1",
                "https://example.com/access_results2",
            ]
        }

    def test_get_access_results_contributor(
        self,
        privacy_request: PrivacyRequest,
        api_client: TestClient,
        contributor_user,
        db,
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db)

        url = V1_URL_PREFIX + PRIVACY_REQUEST_ACCESS_RESULTS.format(
            privacy_request_id=privacy_request.id
        )
        auth_header = generate_role_header_for_user(
            contributor_user, roles=contributor_user.permissions.roles
        )
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
