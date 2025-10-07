from uuid import uuid4

import pytest

from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.request_task import (
    AsyncTaskType,
    RequestTaskSubRequest,
)
from fides.api.schemas.policy import ActionType


@pytest.mark.async_dsr
class TestRequestTaskSubRequest:
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
                "status": "pending",
            },
        )

        assert sub_request.request_task_id == polling_request_task.id
        assert sub_request.param_values == test_data
        assert sub_request.param_values["request_id"] == test_data["request_id"]
        assert sub_request.status == "pending"

    def test_request_task_relationship(self, db, polling_request_task):
        """Test the 1:N relationship between RequestTask and RequestTaskSubRequest"""
        test_data = {"request_id": "test_123", "api_version": "v1"}

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        # Refresh the request_task to load the relationship
        db.refresh(polling_request_task)

        # Test dynamic relationship - sub_requests returns a query object
        sub_requests = polling_request_task.sub_requests
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
                "status": "pending",
            },
        )

        # Update the data
        updated_data = {
            "request_id": "initial_123",
            "status": "completed",
            "result_url": "/api/results/123",
        }
        sub_request.param_values = updated_data
        sub_request.status = "completed"
        sub_request.save(db)

        # Verify update
        db.refresh(sub_request)
        assert sub_request.param_values == updated_data
        assert sub_request.param_values["status"] == "completed"
        assert sub_request.status == "completed"

    def test_multiple_sub_requests_per_task(self, db, polling_request_task):
        """Test that a RequestTask can have multiple sub-requests (1:N relationship)"""
        # Create multiple sub-requests for the same task
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "sub_req_1", "endpoint": "/users"},
                "status": "pending",
            },
        )

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "sub_req_2", "endpoint": "/orders"},
                "status": "pending",
            },
        )

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "sub_req_3", "endpoint": "/profiles"},
                "status": "completed",
            },
        )

        # Verify the task has multiple sub-requests
        db.refresh(polling_request_task)
        sub_requests = polling_request_task.sub_requests

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
                "status": "pending",
            },
        )

        data2 = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": task2.id,
                "param_values": {"request_id": "orders_456", "endpoint": "/orders"},
                "status": "pending",
            },
        )

        # Verify each task has its own sub-requests
        db.refresh(task1)
        db.refresh(task2)

        task1_sub_requests = task1.sub_requests
        task2_sub_requests = task2.sub_requests

        assert len(task1_sub_requests) == 1
        assert len(task2_sub_requests) == 1
        assert task1_sub_requests[0].param_values["request_id"] == "users_123"
        assert task2_sub_requests[0].param_values["request_id"] == "orders_456"
        assert data1.id != data2.id

    def test_sub_request_creation_with_minimal_data(self, db, polling_request_task):
        """Test creating RequestTaskSubRequest with minimal required data"""
        minimal_data = {"request_id": "minimal_123"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": minimal_data,
                "status": "pending",
            },
        )

        assert sub_request.request_task_id == polling_request_task.id
        assert sub_request.param_values == minimal_data
        assert sub_request.status == "pending"
        assert sub_request.id is not None

    def test_sub_request_creation_with_complex_param_values(
        self, db, polling_request_task
    ):
        """Test creating RequestTaskSubRequest with complex nested param_values"""
        complex_data = {
            "request_id": "complex_456",
            "metadata": {
                "endpoint": "/api/v1/users",
                "headers": {"Authorization": "Bearer token123"},
                "query_params": {"limit": 100, "offset": 0},
            },
            "timestamps": {
                "initiated_at": "2023-01-01T10:00:00Z",
                "updated_at": "2023-01-01T10:05:00Z",
            },
            "status_details": {
                "code": 200,
                "message": "Success",
                "retry_count": 0,
            },
        }

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": complex_data,
                "status": "completed",
            },
        )

        assert sub_request.param_values == complex_data
        assert sub_request.param_values["metadata"]["endpoint"] == "/api/v1/users"
        assert (
            sub_request.param_values["timestamps"]["initiated_at"]
            == "2023-01-01T10:00:00Z"
        )
        assert sub_request.status == "completed"

    def test_sub_request_get_correlation_id_helper(self, db, polling_request_task):
        """Test the get_correlation_id helper method"""
        test_data = {"request_id": "helper_test_789", "other_field": "value"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        assert sub_request.get_correlation_id() == "helper_test_789"

    def test_sub_request_get_correlation_id_no_request_id(
        self, db, polling_request_task
    ):
        """Test the get_correlation_id helper method when request_id is not present"""
        test_data = {"other_field": "value", "status": "pending"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        assert sub_request.get_correlation_id() is None

    def test_sub_request_get_correlation_id_empty_param_values(
        self, db, polling_request_task
    ):
        """Test the get_correlation_id helper method with empty param_values"""
        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {},
                "status": "pending",
            },
        )

        assert sub_request.get_correlation_id() is None

    def test_sub_request_update_status_helper(self, db, polling_request_task):
        """Test the update_status helper method"""
        test_data = {"request_id": "status_test_123"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        # Update status using helper method
        sub_request.update_status(db, "completed")

        # Verify the update
        db.refresh(sub_request)
        assert sub_request.status == "completed"

    def test_sub_request_update_status_multiple_updates(self, db, polling_request_task):
        """Test multiple status updates using the helper method"""
        test_data = {"request_id": "multi_status_456"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        # Multiple status updates
        sub_request.update_status(db, "processing")
        db.refresh(sub_request)
        assert sub_request.status == "processing"

        sub_request.update_status(db, "completed")
        db.refresh(sub_request)
        assert sub_request.status == "completed"

    def test_sub_request_database_constraints(self, db, polling_request_task):
        """Test database constraints and validation"""
        # Test that request_task_id is required
        with pytest.raises(
            Exception
        ):  # Should raise an exception for missing required field
            RequestTaskSubRequest.create(
                db,
                data={
                    "param_values": {"request_id": "test"},
                    "status": "pending",
                },
            )

    def test_sub_request_cascade_delete(self, db, in_processing_privacy_request):
        """Test that sub-requests are deleted when the parent RequestTask is deleted"""
        # Create a request task
        task = RequestTask.create(
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

        # Create sub-requests
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": task.id,
                "param_values": {"request_id": "cascade_test_1"},
                "status": "pending",
            },
        )

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": task.id,
                "param_values": {"request_id": "cascade_test_2"},
                "status": "pending",
            },
        )

        # Verify sub-requests exist
        db.refresh(task)
        sub_requests = task.sub_requests
        assert len(sub_requests) == 2

        # Delete the parent task
        task.delete(db)

        # Verify sub-requests are also deleted (cascade)
        remaining_sub_requests = (
            db.query(RequestTaskSubRequest)
            .filter(RequestTaskSubRequest.request_task_id == task.id)
            .all()
        )
        assert len(remaining_sub_requests) == 0

    def test_sub_request_query_by_status(self, db, polling_request_task):
        """Test querying sub-requests by status"""
        # Create sub-requests with different statuses
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "status_pending_1"},
                "status": "pending",
            },
        )

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "status_completed_1"},
                "status": "completed",
            },
        )

        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": {"request_id": "status_pending_2"},
                "status": "pending",
            },
        )

        # Query by status
        pending_sub_requests = (
            db.query(RequestTaskSubRequest)
            .filter(
                RequestTaskSubRequest.request_task_id == polling_request_task.id,
                RequestTaskSubRequest.status == "pending",
            )
            .all()
        )

        completed_sub_requests = (
            db.query(RequestTaskSubRequest)
            .filter(
                RequestTaskSubRequest.request_task_id == polling_request_task.id,
                RequestTaskSubRequest.status == "completed",
            )
            .all()
        )

        assert len(pending_sub_requests) == 2
        assert len(completed_sub_requests) == 1

        # Verify the correct request_ids
        pending_ids = [sr.get_correlation_id() for sr in pending_sub_requests]
        assert "status_pending_1" in pending_ids
        assert "status_pending_2" in pending_ids

        completed_ids = [sr.get_correlation_id() for sr in completed_sub_requests]
        assert "status_completed_1" in completed_ids

    def test_sub_request_param_values_mutation(self, db, polling_request_task):
        """Test that param_values can be mutated and changes are persisted"""
        initial_data = {"request_id": "mutation_test", "count": 0}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": initial_data,
                "status": "pending",
            },
        )

        # Mutate the param_values by creating a new dictionary
        updated_data = sub_request.param_values.copy()
        updated_data["count"] = 5
        updated_data["new_field"] = "added_value"
        sub_request.param_values = updated_data
        sub_request.save(db)

        # Verify the mutation was persisted
        db.refresh(sub_request)
        assert sub_request.param_values["count"] == 5
        assert sub_request.param_values["new_field"] == "added_value"
        assert sub_request.param_values["request_id"] == "mutation_test"

    def test_sub_request_access_data_storage(self, db, polling_request_task):
        """Test storing and retrieving access data in sub-requests"""
        test_data = {"request_id": "access_test_123"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        # Test initial state
        assert sub_request.get_access_data() == []

        # Set access data
        access_data = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]
        sub_request.access_data = access_data
        sub_request.save(db)

        # Verify access data was stored
        db.refresh(sub_request)
        retrieved_data = sub_request.get_access_data()
        assert len(retrieved_data) == 2
        assert retrieved_data[0]["name"] == "John Doe"
        assert retrieved_data[1]["email"] == "jane@example.com"

    def test_sub_request_rows_masked_tracking(self, db, polling_request_task):
        """Test tracking rows masked in sub-requests"""
        test_data = {"request_id": "masking_test_789"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        # Initially no rows masked
        assert sub_request.rows_masked is None

        # Set rows masked
        sub_request.rows_masked = 5
        sub_request.save(db)

        # Verify rows masked was stored
        db.refresh(sub_request)
        assert sub_request.rows_masked == 5

    def test_sub_request_external_storage_cleanup(self, db, polling_request_task):
        """Test that external storage cleanup works for sub-requests"""
        test_data = {"request_id": "cleanup_test_101"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        # Set some data to trigger external storage
        access_data = [{"id": 1, "data": "test"}]

        sub_request.access_data = access_data
        sub_request.save(db)

        # Verify data is stored
        db.refresh(sub_request)
        assert len(sub_request.get_access_data()) == 1

        # Test cleanup method
        sub_request.cleanup_external_storage()

        # Note: The actual cleanup behavior depends on the external storage implementation
        # This test ensures the method can be called without errors

    def test_sub_request_delete_with_cleanup(self, db, polling_request_task):
        """Test that delete method properly cleans up external storage"""
        test_data = {"request_id": "delete_test_202"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "pending",
            },
        )

        # Set some data
        sub_request.access_data = [{"id": 1, "data": "test"}]
        sub_request.save(db)

        # Verify sub-request exists
        db.refresh(sub_request)
        assert sub_request.id is not None

        # Delete the sub-request (should trigger cleanup)
        sub_request.delete(db)

        # Verify sub-request is deleted
        deleted_sub_request = (
            db.query(RequestTaskSubRequest)
            .filter(RequestTaskSubRequest.id == sub_request.id)
            .first()
        )
        assert deleted_sub_request is None

    def test_sub_request_comprehensive_data_storage(self, db, polling_request_task):
        """Test comprehensive data storage including all new fields"""
        test_data = {"request_id": "comprehensive_test_303"}

        sub_request = RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": polling_request_task.id,
                "param_values": test_data,
                "status": "completed",
            },
        )

        # Set all types of data
        access_data = [
            {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
            {"user_id": 2, "name": "Bob", "email": "bob@example.com"},
        ]

        sub_request.access_data = access_data
        sub_request.rows_masked = 2
        sub_request.save(db)

        # Verify all data is stored correctly
        db.refresh(sub_request)

        assert sub_request.get_correlation_id() == "comprehensive_test_303"
        assert sub_request.status == "completed"
        assert sub_request.rows_masked == 2

        retrieved_access_data = sub_request.get_access_data()
        assert len(retrieved_access_data) == 2
        assert retrieved_access_data[0]["name"] == "Alice"
        assert retrieved_access_data[1]["email"] == "bob@example.com"
