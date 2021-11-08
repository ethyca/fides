import json
from datetime import datetime
from typing import List
from unittest import mock

from sqlalchemy import (
    column,
    table,
    select,
)

from fastapi_pagination import Params
import pytest
from starlette.testclient import TestClient

from fidesops.api.v1.urn_registry import (
    PRIVACY_REQUESTS,
    V1_URL_PREFIX,
    REQUEST_PREVIEW,
)
from fidesops.api.v1.scope_registry import (
    PRIVACY_REQUEST_CREATE,
    STORAGE_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_READ,
)
from fidesops.db.session import (
    get_db_engine,
    get_db_session,
)
from fidesops.models.client import ClientDetail
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.models.policy import DataCategory
from fidesops.schemas.dataset import DryRunDatasetResponse
from fidesops.util.cache import get_identity_cache_key

page_size = Params().size


def stringify_date(log_date: datetime) -> str:
    return log_date.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


class TestCreatePrivacyRequest:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    def test_privacy_request_unauthenticated(self, api_client: TestClient, url):
        resp = api_client.post(url)
        assert resp.status_code == 401

    def test_privacy_request_wrong_scopes(
        self, api_client: TestClient, url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        resp = api_client.post(url, json={}, headers=auth_header)
        assert resp.status_code == 403

    @mock.patch("fidesops.task.graph_task.run_access_request")
    def test_create_privacy_request(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identities": [{"email": "test@example.com"}],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch("fidesops.task.graph_task.run_access_request")
    def test_create_privacy_request_limit_exceeded(
        self,
        _,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        payload = []
        for i in range(0, 51):
            payload.append(
                {
                    "requested_at": "2021-08-30T16:09:37.359Z",
                    "policy_key": policy.key,
                    "identities": [{"email": "ftest{i}@example.com"}],
                },
            )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        response = api_client.post(url, headers=auth_header, json=payload)

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "ensure this value has at most 50 items"
        )

    @mock.patch("fidesops.models.privacy_request.PrivacyRequest.start_processing")
    def test_create_privacy_request_starts_processing(
        self,
        start_processing_mock,
        url,
        api_client: TestClient,
        db,
        generate_auth_header,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identities": [{"email": "test@example.com"}],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        assert start_processing_mock.called

        response_data = resp.json()["succeeded"]
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)

    @mock.patch("fidesops.task.graph_task.run_access_request")
    def test_create_privacy_request_with_external_id(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        external_id = "ext_some-uuid-here-1234"
        data = [
            {
                "external_id": external_id,
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identities": [{"email": "test@example.com"}],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(
            V1_URL_PREFIX + PRIVACY_REQUESTS, json=data, headers=auth_header
        )
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        assert response_data[0]["external_id"] == external_id
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        assert pr.external_id == external_id
        pr.delete(db=db)
        assert run_access_request_mock.called

    @mock.patch("fidesops.task.graph_task.run_access_request")
    def test_create_privacy_request_caches_identity(
        self,
        run_access_request_mock,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        policy,
        cache,
    ):
        identity = {"email": "test@example.com"}
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identities": [identity],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
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

    def test_create_privacy_request_no_identities(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identities": [],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 0
        response_data = resp.json()["failed"]
        assert len(response_data) == 1

    @pytest.mark.integration
    def test_create_and_process_access_request(
        self,
        postgres_example_test_dataset_config,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        customer_email = "customer-1@example.com"
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identities": [{"email": customer_email}],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        results = pr.get_results()
        assert len(results.keys()) == 11
        for key in results.keys():
            assert results[key] is not None
            assert results[key] != {}

        result_key_prefix = f"EN_{pr.id}__access_request__postgres_example_test_dataset:"
        customer_key = result_key_prefix + "customer"
        assert results[customer_key][0]["email"] == customer_email

        visit_key = result_key_prefix + "visit"
        assert results[visit_key][0]["email"] == customer_email

        pr.delete(db=db)

    @pytest.mark.integration_erasure
    def test_create_and_process_erasure_request_specific_category(
        self,
        postgres_example_test_dataset_config,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        erasure_policy,
    ):
        customer_email = "customer-1@example.com"
        customer_id = 1
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": erasure_policy.key,
                "identities": [{"email": customer_email}],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)

        example_postgres_uri = (
            "postgresql://postgres:postgres@postgres_example/postgres_example"
        )
        engine = get_db_engine(database_uri=example_postgres_uri)
        SessionLocal = get_db_session(engine=engine)
        integration_db = SessionLocal()
        stmt = select(
            column("id"),
            column("name"),
        ).select_from(table("customer"))
        res = integration_db.execute(stmt).all()

        customer_found = False
        for row in res:
            if customer_id in row:
                customer_found = True
                # Check that the `name` field is `None`
                assert row[1] is None
        assert customer_found

    @pytest.mark.integration_erasure
    def test_create_and_process_erasure_request_generic_category(
        self,
        postgres_example_test_dataset_config,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        erasure_policy,
    ):
        # It's safe to change this here since the `erasure_policy` fixture is scoped
        # at function level
        target = erasure_policy.rules[0].targets[0]
        target.data_category = DataCategory("user.provided.identifiable.contact").value
        target.save(db=db)

        email = "customer-2@example.com"
        customer_id = 2
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": erasure_policy.key,
                "identities": [{"email": email}],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)

        example_postgres_uri = (
            "postgresql://postgres:postgres@postgres_example/postgres_example"
        )
        engine = get_db_engine(database_uri=example_postgres_uri)
        SessionLocal = get_db_session(engine=engine)
        integration_db = SessionLocal()
        stmt = select(
            column("id"),
            column("email"),
        ).select_from(table("customer"))
        res = integration_db.execute(stmt).all()

        customer_found = False
        for row in res:
            if customer_id in row:
                customer_found = True
                # Check that the `email` field is `None` and that its data category
                # ("user.provided.identifiable.contact.email") has been erased by the parent
                # category ("user.provided.identifiable.contact")
                assert row[1] is None
            else:
                # There are two rows other rows, and they should not have been erased
                assert row[1] in ["customer-1@example.com", "jane@example.com"]
        assert customer_found

    @pytest.mark.integration_erasure
    def test_create_and_process_erasure_request_with_table_joins(
        self,
        postgres_example_test_dataset_config,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        erasure_policy,
    ):
        # It's safe to change this here since the `erasure_policy` fixture is scoped
        # at function level
        target = erasure_policy.rules[0].targets[0]
        target.data_category = DataCategory(
            "user.provided.identifiable.financial"
        ).value
        target.save(db=db)

        customer_email = "customer-1@example.com"
        customer_id = 1
        data = [
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": erasure_policy.key,
                "identities": [{"email": customer_email}],
            }
        ]
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE])
        resp = api_client.post(url, json=data, headers=auth_header)

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        pr = PrivacyRequest.get(db=db, id=response_data[0]["id"])
        pr.delete(db=db)

        example_postgres_uri = (
            "postgresql://postgres:postgres@postgres_example/postgres_example"
        )
        engine = get_db_engine(database_uri=example_postgres_uri)
        SessionLocal = get_db_session(engine=engine)
        integration_db = SessionLocal()
        stmt = select(
            column("customer_id"),
            column("id"),
            column("ccn"),
            column("code"),
            column("name"),
        ).select_from(table("payment_card"))
        res = integration_db.execute(stmt).all()

        card_found = False
        for row in res:
            if row[0] == customer_id:
                card_found = True
                assert row[2] is None
                assert row[3] is None
                assert row[4] is None

        assert card_found is True


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
            url + f"?completed_lt=2021-01-01&errored_gt=2021-01-02",
            headers=auth_header,
        )
        assert 400 == response.status_code

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
            url + f"?id={privacy_request.id}", headers=auth_header
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
                }
            ],
            "total": 1,
            "page": 1,
            "size": page_size,
        }

        resp = response.json()
        assert resp == expected_resp

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
        response = api_client.get(url + f"?created_lt=2019-01-01", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.get(url + f"?created_gt=2019-01-01", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 3
        assert resp["items"][0]["id"] == privacy_request.id
        assert resp["items"][1]["id"] == succeeded_privacy_request.id
        assert resp["items"][2]["id"] == failed_privacy_request.id

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
        response = api_client.get(url + f"?started_lt=2021-05-01", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 2
        assert resp["items"][0]["id"] == privacy_request.id
        assert resp["items"][1]["id"] == failed_privacy_request.id

        response = api_client.get(url + f"?started_gt=2021-05-01", headers=auth_header)
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
            url + f"?completed_lt=2021-10-01", headers=auth_header
        )
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.get(
            url + f"?completed_gt=2021-10-01", headers=auth_header
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
        response = api_client.get(url + f"?errored_lt=2021-01-01", headers=auth_header)
        assert 200 == response.status_code
        resp = response.json()
        assert len(resp["items"]) == 0

        response = api_client.get(url + f"?errored_gt=2021-01-01", headers=auth_header)
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
                    "results": {
                        "my-mongo-db": [
                            {
                                "collection_name": "orders",
                                "fields_affected": [
                                    {
                                        "path": "orders.name",
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
                                        "path": "user.email",
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
                                        "path": "address.street",
                                        "field_name": "street",
                                        "data_categories": [
                                            "user.provided.identifiable.contact.street"
                                        ],
                                    },
                                    {
                                        "path": "address.city",
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
                            "path": "user.email",
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
                            "path": "orders.name",
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
                            "path": "address.street",
                            "field_name": "street",
                            "data_categories": [
                                "user.provided.identifiable.contact.street"
                            ],
                        },
                        {
                            "path": "address.city",
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
