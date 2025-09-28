"""
Enhanced tests for RequestTaskSubRequest functionality with polling strategies
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.request_task import (
    AsyncTaskType,
    RequestTaskSubRequest,
)
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.saas_connector import SaaSConnector


@pytest.mark.integration
class TestRequestTaskSubRequest:
    """Test suite for RequestTaskSubRequest model and functionality (1:N relationship)"""

    def test_create_request_task_sub_request(self, db, polling_request_task):
        """Test creating RequestTaskSubRequest entry"""
        test_data = {
            "request_id": str(uuid4()),
            "status": "initiated",
            "metadata": {"endpoint": "/api/v1/users"},
        }

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "sub_request_status": "pending",
            },
        )

        assert sub_request.request_task_id == polling_request_task.id
        assert sub_request.param_values == test_data
        assert sub_request.param_values["request_id"] == test_data["request_id"]
        assert sub_request.sub_request_status == "pending"

    def test_request_task_relationship(self, db, polling_request_task):
        """Test the 1:N relationship between RequestTask and RequestTaskSubRequest"""
        test_data = {"request_id": "test_123", "api_version": "v1"}

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "sub_request_status": "pending",
            },
        )

        # Refresh the request_task to load the relationship
        db.refresh(polling_request_task)

        # Test dynamic relationship - sub_requests returns a query object
        sub_requests = polling_request_task.sub_requests.all()
        assert len(sub_requests) == 1
        assert sub_requests[0].param_values == test_data

    def test_update_request_data(self, db, polling_request_task):
        """Test updating existing sub-request data"""
        initial_data = {"request_id": "initial_123", "status": "pending"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": initial_data,
                "sub_request_status": "pending",
            },
        )

        # Update the data
        updated_data = {
            "request_id": "initial_123",
            "status": "completed",
            "result_url": "/api/results/123",
        }
        sub_request.param_values = updated_data
        sub_request.sub_request_status = "completed"
        sub_request.save(db)

        # Verify update
        db.refresh(sub_request)
        assert sub_request.param_values == updated_data
        assert sub_request.param_values["status"] == "completed"
        assert sub_request.sub_request_status == "completed"

    def test_multiple_sub_requests_per_task(self, db, polling_request_task):
        """Test that a RequestTask can have multiple sub-requests (1:N relationship)"""
        # Create multiple sub-requests for the same task
        sub_request1 = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "sub_req_1", "endpoint": "/users"},
                "sub_request_status": "pending",
            },
        )

        sub_request2 = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "sub_req_2", "endpoint": "/orders"},
                "sub_request_status": "pending",
            },
        )

        sub_request3 = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "sub_req_3", "endpoint": "/profiles"},
                "sub_request_status": "completed",
            },
        )

        # Verify the task has multiple sub-requests
        db.refresh(polling_request_task)
        sub_requests = polling_request_task.sub_requests.all()

        assert len(sub_requests) == 3
        request_ids = [sr.param_values["request_id"] for sr in sub_requests]
        assert "sub_req_1" in request_ids
        assert "sub_req_2" in request_ids
        assert "sub_req_3" in request_ids

    def test_multiple_tasks_separate_sub_requests(
        self, db, in_processing_privacy_request
    ):
        """Test that different RequestTasks have separate sub-requests"""
        # Create two request tasks
        task1 = RequestTask.create(
            db=db,
            data={
                "privacy_request_id": in_processing_privacy_request.id,
                "action_type": ActionType.access,
                "status": "pending",
                "collection_address": "test_dataset:users",
                "dataset_name": "test_dataset",
                "collection_name": "users",
                "async_type": AsyncTaskType.polling,
            },
        )

        task2 = RequestTask.create(
            db=db,
            data={
                "privacy_request_id": in_processing_privacy_request.id,
                "action_type": ActionType.access,
                "status": "pending",
                "collection_address": "test_dataset:orders",
                "dataset_name": "test_dataset",
                "collection_name": "orders",
                "async_type": AsyncTaskType.polling,
            },
        )

        # Create sub-requests for each task
        data1 = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": task1.id,
                "param_values": {"request_id": "users_123", "endpoint": "/users"},
                "sub_request_status": "pending",
            },
        )

        data2 = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": task2.id,
                "param_values": {"request_id": "orders_456", "endpoint": "/orders"},
                "sub_request_status": "pending",
            },
        )

        # Verify each task has its own sub-requests
        db.refresh(task1)
        db.refresh(task2)

        task1_sub_requests = task1.sub_requests.all()
        task2_sub_requests = task2.sub_requests.all()

        assert len(task1_sub_requests) == 1
        assert len(task2_sub_requests) == 1
        assert task1_sub_requests[0].param_values["request_id"] == "users_123"
        assert task2_sub_requests[0].param_values["request_id"] == "orders_456"
        assert data1.id != data2.id


@pytest.mark.integration_saas
class TestSaaSConnectorSubRequestIntegration:
    """Test integration between SaaSConnector and sub-request storage (1:N relationship)"""

    @pytest.fixture
    def mock_saas_connector(self):
        """Create a mock SaaS connector"""
        connector = Mock(spec=SaaSConnector)
        connector.secrets = {"api_key": "test_key", "domain": "test.example.com"}
        return connector

    @pytest.fixture
    def request_task_with_sub_requests(self, db, polling_request_task):
        """Create a request task with stored sub-requests"""
        # Add multiple sub-requests to the existing polling_request_task
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {
                    "request_id": "async_req_12345",
                    "initiated_at": "2023-01-01T10:00:00Z",
                    "endpoint": "/api/v1/users",
                },
                "sub_request_status": "pending",
            },
        )

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {
                    "request_id": "async_req_67890",
                    "initiated_at": "2023-01-01T10:30:00Z",
                    "endpoint": "/api/v1/orders",
                },
                "sub_request_status": "pending",
            },
        )

        return polling_request_task

    def test_connector_save_sub_request(
        self, db, polling_request_task, mock_saas_connector
    ):
        """Test SaaSConnector saving sub-request data with proper session"""
        test_data = {"request_id": str(uuid4()), "api_endpoint": "/test"}

        # Test the save method with session
        mock_saas_connector._save_request_data(polling_request_task, test_data)

        # Verify data was saved as a sub-request
        db.refresh(polling_request_task)
        sub_requests = polling_request_task.sub_requests.all()
        assert len(sub_requests) == 1
        assert sub_requests[0].param_values == test_data

    def test_get_sub_requests_from_task(
        self, db, request_task_with_sub_requests, mock_saas_connector
    ):
        """Test retrieving sub-requests from a task"""
        db.refresh(request_task_with_sub_requests)
        sub_requests = request_task_with_sub_requests.sub_requests.all()

        assert len(sub_requests) == 2

        # Verify both sub-requests exist
        request_ids = [sr.param_values["request_id"] for sr in sub_requests]
        assert "async_req_12345" in request_ids
        assert "async_req_67890" in request_ids

    def test_save_multiple_sub_requests(self, db, polling_request_task):
        """Test that _save_request_data supports multiple sub-requests for the same task"""

        # Create a real SaaSConnector instance for testing
        from fides.api.models.connectionconfig import ConnectionConfig

        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_connector",
                "connection_type": "saas",
                "access": "read",
            },
        )

        connector = SaaSConnector(connection_config)

        # Save first sub-request
        first_data = {
            "request_id": "first_sub_123",
            "status": "initiated",
            "endpoint": "/users",
        }
        connector._save_request_data(polling_request_task, first_data)

        # Save second sub-request
        second_data = {
            "request_id": "second_sub_456",
            "status": "initiated",
            "endpoint": "/orders",
        }
        connector._save_request_data(polling_request_task, second_data)

        # Save third sub-request
        third_data = {
            "request_id": "third_sub_789",
            "status": "completed",
            "endpoint": "/profiles",
        }
        connector._save_request_data(polling_request_task, third_data)

        # Verify all three entries exist as separate sub-requests
        db.refresh(polling_request_task)
        sub_requests = (
            db.query(RequestTaskSubRequest)
            .filter(RequestTaskSubRequest.request_task_id == polling_request_task.id)
            .all()
        )

        assert len(sub_requests) == 3  # Three separate sub-requests

        # Verify each sub-request has the correct data
        request_ids = [sr.param_values["request_id"] for sr in sub_requests]
        assert "first_sub_123" in request_ids
        assert "second_sub_456" in request_ids
        assert "third_sub_789" in request_ids

        # Verify all have different IDs
        ids = [sr.id for sr in sub_requests]
        assert len(set(ids)) == 3  # All unique IDs

    def test_save_sub_requests_multiple_tasks_separate_entries(
        self, db, in_processing_privacy_request
    ):
        """Test that different tasks get separate sub-request entries"""
        # Create two different tasks
        task1 = RequestTask.create(
            db=db,
            data={
                "privacy_request_id": in_processing_privacy_request.id,
                "action_type": ActionType.access,
                "status": "pending",
                "collection_address": "test_dataset:users",
                "dataset_name": "test_dataset",
                "collection_name": "users",
                "async_type": AsyncTaskType.polling,
            },
        )

        task2 = RequestTask.create(
            db=db,
            data={
                "privacy_request_id": in_processing_privacy_request.id,
                "action_type": ActionType.access,
                "status": "pending",
                "collection_address": "test_dataset:orders",
                "dataset_name": "test_dataset",
                "collection_name": "orders",
                "async_type": AsyncTaskType.polling,
            },
        )

        # Create connector
        from fides.api.models.connectionconfig import ConnectionConfig

        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_connector_multi",
                "connection_type": "saas",
                "access": "read",
            },
        )

        connector = SaaSConnector(connection_config)

        # Save multiple sub-requests for both tasks
        task1_data1 = {
            "request_id": "users_req_456",
            "endpoint": "/api/users",
            "batch": 1,
        }
        task1_data2 = {
            "request_id": "users_req_457",
            "endpoint": "/api/users",
            "batch": 2,
        }
        task2_data1 = {
            "request_id": "orders_req_789",
            "endpoint": "/api/orders",
            "batch": 1,
        }

        connector._save_request_data(task1, task1_data1)
        connector._save_request_data(task1, task1_data2)
        connector._save_request_data(task2, task2_data1)

        # Verify each task has its own sub-requests
        db.refresh(task1)
        db.refresh(task2)

        task1_sub_requests = (
            db.query(RequestTaskSubRequest)
            .filter(RequestTaskSubRequest.request_task_id == task1.id)
            .all()
        )

        task2_sub_requests = (
            db.query(RequestTaskSubRequest)
            .filter(RequestTaskSubRequest.request_task_id == task2.id)
            .all()
        )

        assert len(task1_sub_requests) == 2  # Task1 has 2 sub-requests
        assert len(task2_sub_requests) == 1  # Task2 has 1 sub-request

        # Verify task1 sub-requests
        task1_request_ids = [sr.param_values["request_id"] for sr in task1_sub_requests]
        assert "users_req_456" in task1_request_ids
        assert "users_req_457" in task1_request_ids

        # Verify task2 sub-requests
        assert task2_sub_requests[0].param_values["request_id"] == "orders_req_789"

        # Verify all sub-requests have unique IDs
        all_ids = [sr.id for sr in task1_sub_requests + task2_sub_requests]
        assert len(set(all_ids)) == 3  # All unique IDs
