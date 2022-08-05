import ast
import csv
import io
import json
from datetime import datetime
from typing import List
from unittest import mock

import pytest
from dateutil.parser import parse
from fastapi import HTTPException, status
from fastapi_pagination import Params
from fideslib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fideslib.models.audit_log import AuditLog, AuditLogAction
from fideslib.models.client import ClientDetail
from fideslib.oauth.jwt import generate_jwe
from starlette.testclient import TestClient

from fidesops.api.v1.endpoints.privacy_request_endpoints import (
    EMBEDDED_EXECUTION_LOG_LIMIT,
    validate_manual_input,
)
from fidesops.api.v1.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
    STORAGE_CREATE_OR_UPDATE,
)
from fidesops.api.v1.urn_registry import (
    DATASETS,
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_DENY,
    PRIVACY_REQUEST_MANUAL_ERASURE,
    PRIVACY_REQUEST_MANUAL_INPUT,
    PRIVACY_REQUEST_RESUME,
    PRIVACY_REQUEST_RETRY,
    PRIVACY_REQUESTS,
    REQUEST_PREVIEW,
    V1_URL_PREFIX,
)
from fidesops.core.config import config
from fidesops.graph.config import CollectionAddress
from fidesops.graph.graph import DatasetGraph
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.models.policy import ActionType, PausedStep
from fidesops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    ManualAction,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fidesops.schemas.dataset import DryRunDatasetResponse
from fidesops.schemas.masking.masking_secrets import SecretType
from fidesops.schemas.policy import PolicyResponse
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.util.cache import (
    get_encryption_cache_key,
    get_identity_cache_key,
    get_masking_secret_cache_key,
)

page_size = Params().size


def stringify_date(log_date: datetime) -> str:
    return log_date.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


class TestCreatePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request(
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
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        TEST_PHONE_NUMBER = "+1 234 567 8910"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_require_manual_approval(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        config.execution.require_manual_request_approval = True

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

        config.execution.require_manual_request_approval = False

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_access_request"
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
            == "ensure this value has at most 50 items"
        )

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_create_privacy_request_caches_identity(
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
            }
        ]
        resp = api_client.post(url, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, object_id=response_data[0]["id"])
        key = get_identity_cache_key(
            privacy_request_id=pr.id,
            identity_attribute=list(identity.keys())[0],
        )
        assert cache.get(key) == list(identity.values())[0]
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        assert resp.json()["detail"][0]["msg"] == "Encryption key must be 16 bytes long"

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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


class TestGetPrivacyRequests:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail) -> str:
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
    ):
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
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "policy": {
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.dict()
                            for rule in PolicyResponse.from_orm(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "stopped_collection_details": None,
                    "resume_endpoint": None,
                }
            ],
            "total": 1,
            "page": 1,
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
    ):
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
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "policy": {
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.dict()
                            for rule in PolicyResponse.from_orm(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "stopped_collection_details": None,
                    "resume_endpoint": None,
                }
            ],
            "total": 1,
            "page": 1,
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
        assert (
            resp["items"][0]["identity"]
            == succeeded_privacy_request.get_persisted_identity()
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

    def test_filter_privacy_requests_by_identity_exact(
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
            identity=PrivacyRequestIdentity(
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
        postgres_execution_log,
        second_postgres_execution_log,
        mongo_execution_log,
        url,
        db,
    ):
        """Test privacy requests endpoint with verbose query param to show execution logs"""
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
                    "started_processing_at": stringify_date(
                        privacy_request.started_processing_at
                    ),
                    "finished_processing_at": None,
                    "status": privacy_request.status.value,
                    "external_id": privacy_request.external_id,
                    "identity": None,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "paused_at": None,
                    "reviewer": None,
                    "policy": {
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                        "rules": [
                            rule.dict()
                            for rule in PolicyResponse.from_orm(
                                privacy_request.policy
                            ).rules
                        ],
                    },
                    "stopped_collection_details": None,
                    "resume_endpoint": None,
                    "results": {
                        "my-mongo-db": [
                            {
                                "collection_name": "orders",
                                "fields_affected": [
                                    {
                                        "path": "my-mongo-db:orders:name",
                                        "field_name": "name",
                                        "data_categories": [
                                            "user.provided.identifiable.contact.name"
                                        ],
                                    }
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "in_processing",
                                "updated_at": stringify_date(
                                    mongo_execution_log.updated_at
                                ),
                            }
                        ],
                        "my-postgres-db": [
                            {
                                "collection_name": "user",
                                "fields_affected": [
                                    {
                                        "path": "my-postgres-db:user:email",
                                        "field_name": "email",
                                        "data_categories": [
                                            "user.provided.identifiable.contact.email"
                                        ],
                                    }
                                ],
                                "message": None,
                                "action_type": "access",
                                "status": "pending",
                                "updated_at": stringify_date(
                                    postgres_execution_log.updated_at
                                ),
                            },
                            {
                                "collection_name": "address",
                                "fields_affected": [
                                    {
                                        "path": "my-postgres-db:address:street",
                                        "field_name": "street",
                                        "data_categories": [
                                            "user.provided.identifiable.contact.street"
                                        ],
                                    },
                                    {
                                        "path": "my-postgres-db:address:city",
                                        "field_name": "city",
                                        "data_categories": [
                                            "user.provided.identifiable.contact.city"
                                        ],
                                    },
                                ],
                                "message": "Database timed out.",
                                "action_type": "access",
                                "status": "error",
                                "updated_at": stringify_date(
                                    second_postgres_execution_log.updated_at
                                ),
                            },
                        ],
                    },
                },
            ],
            "total": 1,
            "page": 1,
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
        TEST_PHONE = "+1 234 567 8910"
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
        assert parse(first_row["Time received"], ignoretz=True) == created_at
        assert ast.literal_eval(first_row["Subject identity"]) == {
            "email": TEST_EMAIL,
            "phone_number": TEST_PHONE,
        }
        assert first_row["Policy key"] == "example_access_request_policy"
        assert first_row["Request status"] == "approved"
        assert first_row["Reviewer"] == user.id
        assert parse(first_row["Time approved/denied"], ignoretz=True) == reviewed_at
        assert first_row["Denial reason"] == ""

        privacy_request.delete(db)

    def test_get_paused_access_privacy_request_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in a paused state waiting for manual input to the "manual_collection"
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)
        paused_step = PausedStep.access
        paused_collection = CollectionAddress("manual_dataset", "manual_collection")
        privacy_request.cache_paused_collection_details(
            step=paused_step,
            collection=paused_collection,
            action_needed=[
                ManualAction(
                    locators={"email": ["customer-1@example.com"]},
                    get=["authorized_user"],
                    update=None,
                )
            ],
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "paused"
        assert data["stopped_collection_details"] == {
            "step": "access",
            "collection": "manual_dataset:manual_collection",
            "action_needed": [
                {
                    "locators": {"email": ["customer-1@example.com"]},
                    "get": ["authorized_user"],
                    "update": None,
                }
            ],
        }
        assert data["resume_endpoint"] == "/privacy-request/{}/manual_input".format(
            privacy_request.id
        )

    def test_get_paused_erasure_privacy_request_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in a paused state waiting for manual erasure confirmation to the "another_collection"
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)
        paused_step = PausedStep.erasure
        paused_collection = CollectionAddress("manual_dataset", "another_collection")
        privacy_request.cache_paused_collection_details(
            step=paused_step,
            collection=paused_collection,
            action_needed=[
                ManualAction(
                    locators={"id": [32424]},
                    get=None,
                    update={"authorized_user": "abcde_masked_user"},
                )
            ],
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "paused"
        assert data["stopped_collection_details"] == {
            "step": "erasure",
            "collection": "manual_dataset:another_collection",
            "action_needed": [
                {
                    "locators": {"id": [32424]},
                    "get": None,
                    "update": {"authorized_user": "abcde_masked_user"},
                }
            ],
        }
        assert data["resume_endpoint"] == "/privacy-request/{}/erasure_confirm".format(
            privacy_request.id
        )

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
        assert data["stopped_collection_details"] is None
        assert data["resume_endpoint"] == "/privacy-request/{}/resume".format(
            privacy_request.id
        )

    def test_get_failed_request_resume_info(
        self, db, privacy_request, generate_auth_header, api_client, url
    ):
        # Mock the privacy request being in an errored state waiting for retry
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)
        privacy_request.cache_failed_collection_details(
            step=PausedStep.erasure,
            collection=CollectionAddress("manual_example", "another_collection"),
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert 200 == response.status_code

        data = response.json()["items"][0]
        assert data["status"] == "error"
        assert data["stopped_collection_details"] == {
            "step": "erasure",
            "collection": "manual_example:another_collection",
            "action_needed": None,
        }
        assert data["resume_endpoint"] == f"/privacy-request/{privacy_request.id}/retry"


class TestGetExecutionLogs:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
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
                            "data_categories": [
                                "user.provided.identifiable.contact.email"
                            ],
                        }
                    ],
                    "message": None,
                    "action_type": "access",
                    "status": "pending",
                    "updated_at": stringify_date(postgres_execution_log.updated_at),
                    "dataset_name": "my-postgres-db",
                },
                {
                    "collection_name": "orders",
                    "fields_affected": [
                        {
                            "path": "my-mongo-db:orders:name",
                            "field_name": "name",
                            "data_categories": [
                                "user.provided.identifiable.contact.name"
                            ],
                        }
                    ],
                    "message": None,
                    "action_type": "access",
                    "status": "in_processing",
                    "updated_at": stringify_date(mongo_execution_log.updated_at),
                    "dataset_name": "my-mongo-db",
                },
                {
                    "collection_name": "address",
                    "fields_affected": [
                        {
                            "path": "my-postgres-db:address:street",
                            "field_name": "street",
                            "data_categories": [
                                "user.provided.identifiable.contact.street"
                            ],
                        },
                        {
                            "path": "my-postgres-db:address:city",
                            "field_name": "city",
                            "data_categories": [
                                "user.provided.identifiable.contact.city"
                            ],
                        },
                    ],
                    "message": "Database timed out.",
                    "action_type": "access",
                    "status": "error",
                    "updated_at": stringify_date(
                        second_postgres_execution_log.updated_at
                    ),
                    "dataset_name": "my-postgres-db",
                },
            ],
            "total": 3,
            "page": 1,
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
            == "SELECT email,id FROM subscriptions WHERE email = ?"
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
        path = V1_URL_PREFIX + DATASETS
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
        manual_dataset_config,
        integration_manual_config,
        postgres_example_test_dataset_config,
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
            == "SELECT email,id FROM subscriptions WHERE email = ?"
        )

        assert next(
            response["query"]
            for response in response_body
            if response["collectionAddress"]["dataset"] == "manual_input"
            if response["collectionAddress"]["collection"] == "filing_cabinet"
        ) == {
            "locators": {"customer_id": ["?", "?"]},
            "get": ["authorized_user", "customer_id", "id", "payment_card_id"],
            "update": None,
        }

        assert next(
            response["query"]
            for response in response_body
            if response["collectionAddress"]["dataset"] == "manual_input"
            if response["collectionAddress"]["collection"] == "storage_unit"
        ) == {"locators": {"email": ["?"]}, "get": ["box_id", "email"], "update": None}


class TestApprovePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_APPROVE

    def test_approve_privacy_request_not_authenticated(self, url, api_client):
        response = api_client.patch(url)
        assert response.status_code == 401

    def test_approve_privacy_request_bad_scopes(
        self, url, api_client, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.patch(url, headers=auth_header)
        assert response.status_code == 403

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_approve_privacy_request(
        self,
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
            JWE_PAYLOAD_SCOPES: user.client.scopes,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
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

        assert submit_mock.called

        privacy_request.delete(db)

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_approve_privacy_request_creates_audit_log(
        self,
        submit_mock,
        db,
        url,
        api_client,
        generate_auth_header,
        user,
        privacy_request_status_pending,
    ):
        payload = {
            JWE_PAYLOAD_SCOPES: user.client.scopes,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
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


class TestDenyPrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_DENY

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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
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
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_deny_privacy_request_without_denial_reason(
        self,
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
            JWE_PAYLOAD_SCOPES: user.client.scopes,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
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

        assert denial_audit_log.message is None

        assert not submit_mock.called  # Shouldn't run! Privacy request was denied

        privacy_request.delete(db)

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_deny_privacy_request_with_denial_reason(
        self,
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
            JWE_PAYLOAD_SCOPES: user.client.scopes,
            JWE_PAYLOAD_CLIENT_ID: user.client.id,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(json.dumps(payload), config.security.app_encryption_key)
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
        generate_webhook_auth_header,
        policy_pre_execution_webhooks,
    ):
        response = api_client.post(url)
        assert response.status_code == 401

    def test_resume_privacy_request_invalid_jwe_format(
        self,
        url,
        api_client,
        generate_webhook_auth_header,
        policy_pre_execution_webhooks,
    ):
        auth_header = {
            "Authorization": "Bearer "
            + generate_jwe(
                json.dumps({"unexpected": "format"}), config.security.app_encryption_key
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_resume_privacy_request_invalid_scopes(
        self,
        url,
        api_client,
        generate_webhook_auth_header,
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
                config.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_resume_privacy_request_invalid_webhook(
        self,
        url,
        api_client,
        generate_webhook_auth_header,
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
                config.security.app_encryption_key,
            )
        }
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 404

    def test_resume_privacy_request_not_paused(
        self,
        url,
        api_client,
        generate_webhook_auth_header,
        policy_pre_execution_webhooks,
        privacy_request,
        db,
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db=db)
        auth_header = generate_webhook_auth_header(
            webhook=policy_pre_execution_webhooks[0]
        )
        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 400

        privacy_request.delete(db)

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_resume_privacy_request(
        self,
        submit_mock,
        url,
        api_client,
        generate_webhook_auth_header,
        policy_pre_execution_webhooks,
        privacy_request,
        db,
    ):
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db=db)
        auth_header = generate_webhook_auth_header(
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
            "started_processing_at": stringify_date(
                privacy_request.started_processing_at
            ),
            "finished_processing_at": None,
            "status": "in_processing",
            "external_id": privacy_request.external_id,
            "identity": None,
            "reviewed_at": None,
            "reviewed_by": None,
            "reviewer": None,
            "paused_at": None,
            "policy": {
                "drp_action": None,
                "key": privacy_request.policy.key,
                "name": privacy_request.policy.name,
                "rules": [
                    rule.dict()
                    for rule in PolicyResponse.from_orm(privacy_request.policy).rules
                ],
            },
            "stopped_collection_details": None,
            "resume_endpoint": None,
        }

        privacy_request.delete(db)


class TestResumeAccessRequestWithManualInput:
    @pytest.fixture(scope="function")
    def url(self, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_INPUT.format(
            privacy_request_id=privacy_request.id
        )

    def test_manual_resume_not_authenticated(self, api_client, url):
        response = api_client.post(url, headers={}, json={})
        assert response.status_code == 401

    def test_manual_resume_wrong_scope(self, api_client, url, generate_auth_header):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_manual_resume_privacy_request_not_paused(
        self, api_client, url, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header, json=[{"mock": "row"}])
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Invalid resume request: privacy request '{privacy_request.id}' status = in_processing. Privacy request is not paused."
        )

    def test_manual_resume_privacy_request_no_paused_location(
        self, db, api_client, url, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        response = api_client.post(url, headers=auth_header, json=[{"mock": "row"}])
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Cannot resume privacy request '{privacy_request.id}'; no paused details."
        )

        privacy_request.delete(db)

    def test_resume_with_manual_input_collection_has_changed(
        self, db, api_client, url, generate_auth_header, privacy_request
    ):
        """Fail if user has changed graph so that the paused node doesn't exist"""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        privacy_request.cache_paused_collection_details(
            step=PausedStep.access,
            collection=CollectionAddress("manual_example", "filing_cabinet"),
        )

        response = api_client.post(url, headers=auth_header, json=[{"mock": "row"}])
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "Cannot save manual data. No collection in graph with name: 'manual_example:filing_cabinet'."
        )

        privacy_request.delete(db)

    @pytest.mark.usefixtures(
        "postgres_example_test_dataset_config", "manual_dataset_config"
    )
    def test_resume_with_manual_input_invalid_data(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
    ):
        """Fail if the manual data entered does not match fields on the dataset"""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        privacy_request.cache_paused_collection_details(
            step=PausedStep.access,
            collection=CollectionAddress("manual_input", "filing_cabinet"),
        )

        response = api_client.post(url, headers=auth_header, json=[{"mock": "row"}])
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "Cannot save manual rows. No 'mock' field defined on the 'manual_input:filing_cabinet' collection."
        )

        privacy_request.delete(db)

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    @pytest.mark.usefixtures(
        "postgres_example_test_dataset_config", "manual_dataset_config"
    )
    def test_resume_with_manual_input(
        self,
        _,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        privacy_request.cache_paused_collection_details(
            step=PausedStep.access,
            collection=CollectionAddress("manual_input", "filing_cabinet"),
        )

        response = api_client.post(
            url,
            headers=auth_header,
            json=[
                {
                    "id": 1,
                    "authorized_user": "Jason Doe",
                    "customer_id": 1,
                    "payment_card_id": "abcde",
                }
            ],
        )
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

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


class TestResumeErasureRequestWithManualConfirmation:
    @pytest.fixture(scope="function")
    def url(self, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUEST_MANUAL_ERASURE.format(
            privacy_request_id=privacy_request.id
        )

    def test_manual_resume_not_authenticated(self, api_client, url):
        response = api_client.post(url, headers={}, json={})
        assert response.status_code == 401

    def test_manual_resume_wrong_scope(self, api_client, url, generate_auth_header):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        response = api_client.post(url, headers=auth_header, json={})
        assert response.status_code == 403

    def test_manual_resume_privacy_request_not_paused(
        self, api_client, url, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        response = api_client.post(url, headers=auth_header, json={"row_count": 0})
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Invalid resume request: privacy request '{privacy_request.id}' status = in_processing. Privacy request is not paused."
        )

    def test_manual_resume_privacy_request_no_paused_location(
        self, db, api_client, url, generate_auth_header, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        response = api_client.post(url, headers=auth_header, json={"row_count": 0})
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Cannot resume privacy request '{privacy_request.id}'; no paused details."
        )

        privacy_request.delete(db)

    def test_resume_with_manual_erasure_confirmation_collection_has_changed(
        self, db, api_client, url, generate_auth_header, privacy_request
    ):
        """Fail if user has changed graph so that the paused node doesn't exist"""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        privacy_request.cache_paused_collection_details(
            step=PausedStep.erasure,
            collection=CollectionAddress("manual_example", "filing_cabinet"),
        )

        response = api_client.post(url, headers=auth_header, json={"row_count": 0})
        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "Cannot save manual data. No collection in graph with name: 'manual_example:filing_cabinet'."
        )

        privacy_request.delete(db)

    def test_resume_still_paused_at_access_request(
        self, db, api_client, url, generate_auth_header, privacy_request
    ):
        """Fail if user hitting wrong endpoint to resume."""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        privacy_request.cache_paused_collection_details(
            step=PausedStep.access,
            collection=CollectionAddress("manual_example", "filing_cabinet"),
        )
        response = api_client.post(url, headers=auth_header, json={"row_count": 0})
        assert response.status_code == 400

        assert (
            response.json()["detail"]
            == "Collection 'manual_example:filing_cabinet' is paused at the access step. Pass in manual data instead to '/privacy-request/{privacy_request_id}/manual_input' to resume."
        )

        privacy_request.delete(db)

    @pytest.mark.usefixtures(
        "postgres_example_test_dataset_config", "manual_dataset_config"
    )
    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_resume_with_manual_count(
        self,
        _,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db)

        privacy_request.cache_paused_collection_details(
            step=PausedStep.erasure,
            collection=CollectionAddress("manual_input", "filing_cabinet"),
        )
        response = api_client.post(
            url,
            headers=auth_header,
            json={"row_count": 5},
        )
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

        privacy_request.delete(db)


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

    def test_restart_from_failure_no_stopped_collection(
        self, api_client, url, generate_auth_header, db, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == f"Cannot restart privacy request from failure '{privacy_request.id}'; no failed step or collection."
        )

        privacy_request.delete(db)

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
    )
    def test_restart_from_failure(
        self, submit_mock, api_client, url, generate_auth_header, db, privacy_request
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
        privacy_request.status = PrivacyRequestStatus.error
        privacy_request.save(db)

        privacy_request.cache_failed_collection_details(
            step=PausedStep.access,
            collection=CollectionAddress("test_dataset", "test_collection"),
        )

        response = api_client.post(url, headers=auth_header)
        assert response.status_code == 200

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

        submit_mock.assert_called_with(
            privacy_request_id=privacy_request.id,
            from_step=PausedStep.access.value,
            from_webhook_id=None,
        )
