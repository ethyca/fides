import ast
import csv
import io
import json
from datetime import datetime
from typing import List
from unittest import mock

import pytest
from dateutil.parser import parse
from fastapi import status
from fastapi_pagination import Params
from starlette.testclient import TestClient

from fidesops.api.v1.endpoints.privacy_request_endpoints import (
    EMBEDDED_EXECUTION_LOG_LIMIT,
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
    PRIVACY_REQUEST_RESUME,
    PRIVACY_REQUESTS,
    REQUEST_PREVIEW,
    V1_URL_PREFIX,
)
from fidesops.core.config import config
from fidesops.models.audit_log import AuditLog
from fidesops.models.client import ClientDetail
from fidesops.models.policy import ActionType
from fidesops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fidesops.schemas.dataset import DryRunDatasetResponse
from fidesops.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fidesops.schemas.masking.masking_secrets import SecretType
from fidesops.util.cache import (
    get_encryption_cache_key,
    get_identity_cache_key,
    get_masking_secret_cache_key,
)
from fidesops.util.oauth_util import generate_jwe

page_size = Params().size


def stringify_date(log_date: datetime) -> str:
    return log_date.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


class TestCreatePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
    )
    def test_create_privacy_request_require_manual_approval(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        policy,
    ):
        config.execution.REQUIRE_MANUAL_REQUEST_APPROVAL = True

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
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)
        assert not run_access_request_mock.called

        config.execution.REQUIRE_MANUAL_REQUEST_APPROVAL = False

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
    )
    def test_create_privacy_request_starts_processing(
        self,
        start_processing_mock,
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
        assert resp.status_code == 200
        assert start_processing_mock.called

        response_data = resp.json()["succeeded"]
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        resp = api_client.post(V1_URL_PREFIX + PRIVACY_REQUESTS, json=data)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["external_id"] == external_id
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        assert pr.external_id == external_id
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        key = get_identity_cache_key(
            privacy_request_id=pr.id,
            identity_attribute=list(identity.keys())[0],
        )
        assert cache.get(key) == list(identity.values())[0]
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
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
                    "reviewer": None,
                    "policy": {
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                    },
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
                    "reviewer": None,
                    "policy": {
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                    },
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
            == succeeded_privacy_request.get_cached_identity_data()
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

    def test_filter_privacy_requests_by_internal_id(
        self,
        db,
        api_client,
        url,
        generate_auth_header,
        privacy_request,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        new_request_id = "test_internal_id_1"
        response = api_client.get(
            url + f"?request_id={new_request_id}", headers=auth_header
        )
        assert response.status_code == status.HTTP_200_OK
        resp = response.json()
        assert len(resp["items"]) == 0

        privacy_request.id = new_request_id
        privacy_request.save(db)

        response = api_client.get(
            url + f"?request_id={new_request_id}", headers=auth_header
        )
        assert response.status_code == status.HTTP_200_OK
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
                    "reviewer": None,
                    "policy": {
                        "drp_action": None,
                        "name": privacy_request.policy.name,
                        "key": privacy_request.policy.key,
                    },
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
        privacy_request.cache_identity(
            {"email": "email@example.com", "phone_number": "111-111-1111"}
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
            "email": "email@example.com",
            "phone_number": "111-111-1111",
        }
        assert first_row["Policy key"] == "example_access_request_policy"
        assert first_row["Request status"] == "approved"
        assert first_row["Reviewer"] == user.id
        assert parse(first_row["Time approved/denied"], ignoretz=True) == reviewed_at
        assert first_row["Denial reason"] == ""


class TestGetExecutionLogs:
    @pytest.fixture(scope="function")
    def url(self, db, privacy_request):
        return V1_URL_PREFIX + PRIVACY_REQUESTS + f"/{privacy_request.id}/log"

    def test_get_execution_logs_unauthenticated(
        self, api_client: TestClient, privacy_request, url
    ):
        response = api_client.get(url + "/", headers={})
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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
    )
    def test_approve_completed_privacy_request(
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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        auth_header = {"Authorization": "Bearer " + generate_jwe(json.dumps(payload))}

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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        auth_header = {"Authorization": "Bearer " + generate_jwe(json.dumps(payload))}

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

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
        auth_header = {"Authorization": "Bearer " + generate_jwe(json.dumps(payload))}
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
            + generate_jwe(json.dumps({"unexpected": "format"}))
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
                )
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
                )
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

    @mock.patch(
        "fidesops.service.privacy_request.request_runner_service.PrivacyRequestRunner.submit"
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
            "policy": {
                "drp_action": None,
                "key": privacy_request.policy.key,
                "name": privacy_request.policy.name,
            },
        }
