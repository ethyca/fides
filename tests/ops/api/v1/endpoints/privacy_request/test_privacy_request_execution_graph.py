import pytest
from starlette.testclient import TestClient

from fides.api.models.privacy_request.execution_log import ExecutionLog
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_READ,
    STORAGE_CREATE_OR_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_EXECUTION_GRAPH,
    V1_URL_PREFIX,
)


class TestGetExecutionGraph:
    @pytest.fixture(scope="function")
    def url(self, privacy_request) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUEST_EXECUTION_GRAPH.format(
            privacy_request_id=privacy_request.id
        )

    def test_unauthenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert response.status_code == 401

    def test_wrong_scope(self, api_client: TestClient, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_no_tasks(self, api_client: TestClient, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        data = response.json()
        assert data["nodes"] == []
        assert data["action_type"] == "access"

    def test_graph_with_tasks(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        request_task,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        data = response.json()
        nodes = data["nodes"]
        assert len(nodes) == 3

        root = nodes[0]
        assert root["collection_address"] == "__ROOT__:__ROOT__"
        assert root["status"] == "complete"
        assert root["upstream_tasks"] == []
        assert root["downstream_tasks"] == ["test_dataset:test_collection"]
        collection_node = nodes[1]
        assert collection_node["collection_address"] == "test_dataset:test_collection"
        assert collection_node["status"] == "queued"

        terminator = nodes[2]
        assert terminator["collection_address"] == "__TERMINATE__:__TERMINATE__"
        assert terminator["status"] == "queued"

    def test_status_mapping(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        url,
        request_task,
    ):
        request_task.status = ExecutionLogStatus.in_processing
        request_task.save(db)

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        nodes = response.json()["nodes"]
        collection_node = next(
            n
            for n in nodes
            if n["collection_address"] == "test_dataset:test_collection"
        )
        assert collection_node["status"] == "executing"

    def test_action_type_filter(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        url,
        request_task,
    ):
        erasure_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.erasure,
                "status": "pending",
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "upstream_tasks": [],
                "downstream_tasks": [],
                "all_descendant_tasks": [],
            },
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])

        response = api_client.get(url + "?action_type=access", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "access"
        assert all(n["action_type"] == "access" for n in data["nodes"])

        response = api_client.get(url + "?action_type=erasure", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["action_type"] == "erasure"
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["action_type"] == "erasure"

        erasure_task.delete(db)

    def test_error_message_from_execution_log(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        url,
        request_task,
    ):
        request_task.status = ExecutionLogStatus.error
        request_task.save(db)

        ExecutionLog.create(
            db,
            data={
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "connection_key": None,
                "fields_affected": [],
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.error,
                "privacy_request_id": privacy_request.id,
                "message": "Connection timed out",
            },
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200

        nodes = response.json()["nodes"]
        errored_node = next(
            n
            for n in nodes
            if n["collection_address"] == "test_dataset:test_collection"
        )
        assert errored_node["status"] == "error"
        assert errored_node["message"] == "Connection timed out"

    def test_nonexistent_request(
        self,
        api_client: TestClient,
        generate_auth_header,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        bad_url = V1_URL_PREFIX + PRIVACY_REQUEST_EXECUTION_GRAPH.format(
            privacy_request_id="nonexistent_id"
        )
        response = api_client.get(bad_url, headers=auth_header)
        assert response.status_code == 404
