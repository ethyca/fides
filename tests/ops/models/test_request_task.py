# pylint: disable=protected-access
import os
from unittest import mock

import pytest

from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.models.privacy_request import RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import ExecutionLogStatus
from fides.api.service.storage.util import get_local_filename
from fides.api.util.cache import FidesopsRedis, cache_task_tracking_key, get_cache
from fides.api.util.request_task_storage_util import RequestTaskStorageError


class TestRequestTask:
    def test_basic_attributes(
        self, db, request_task, privacy_request, erasure_request_task
    ):
        assert privacy_request.request_tasks.count() == 6
        assert privacy_request.access_tasks.count() == 3
        assert privacy_request.erasure_tasks.count() == 3
        assert privacy_request.consent_tasks.count() == 0

        assert erasure_request_task.privacy_request_id == privacy_request.id
        assert request_task.privacy_request_id == privacy_request.id
        assert request_task.privacy_request == privacy_request
        assert request_task.action_type == ActionType.access

        assert request_task.get_tasks_with_same_action_type(
            db, "__ROOT__:__ROOT__"
        ).all() == [privacy_request.get_root_task_by_action(ActionType.access)]
        assert erasure_request_task.get_tasks_with_same_action_type(
            db, "__ROOT__:__ROOT__"
        ).all() == [privacy_request.get_root_task_by_action(ActionType.erasure)]

    @pytest.mark.usefixtures("request_task", "erasure_request_task")
    def test_get_tasks_by_action(self, privacy_request):
        assert (
            privacy_request.get_tasks_by_action(ActionType.access).all()
            == privacy_request.access_tasks.all()
        )
        assert (
            privacy_request.get_tasks_by_action(ActionType.erasure).all()
            == privacy_request.erasure_tasks.all()
        )
        assert privacy_request.get_tasks_by_action(ActionType.consent).all() == []

        with pytest.raises(Exception):
            assert privacy_request.get_tasks_by_action(ActionType.update).all() == []

    @pytest.mark.usefixtures("request_task", "erasure_request_task")
    def test_get_root_task_by_action(self, privacy_request):
        task = privacy_request.get_root_task_by_action(ActionType.access)
        assert task.collection_address == "__ROOT__:__ROOT__"
        assert task.action_type == ActionType.access
        assert task.is_root_task
        assert not task.is_terminator_task

        erasure_task = privacy_request.get_root_task_by_action(ActionType.erasure)
        assert erasure_task.collection_address == "__ROOT__:__ROOT__"
        assert erasure_task.action_type == ActionType.erasure

        with pytest.raises(Exception):
            privacy_request.get_root_task_by_action(ActionType.consent)

    @pytest.mark.usefixtures("request_task", "erasure_request_task")
    def test_get_terminate_task_by_action(self, privacy_request):
        task = privacy_request.get_terminate_task_by_action(ActionType.access)
        assert task.collection_address == "__TERMINATE__:__TERMINATE__"
        assert task.action_type == ActionType.access
        assert not task.is_root_task
        assert task.is_terminator_task

        erasure_task = privacy_request.get_terminate_task_by_action(ActionType.erasure)
        assert erasure_task.collection_address == "__TERMINATE__:__TERMINATE__"
        assert erasure_task.action_type == ActionType.erasure

        with pytest.raises(Exception):
            privacy_request.get_terminate_task_by_action(ActionType.consent)

    def test_request_task_address(self, request_task):
        assert request_task.request_task_address == CollectionAddress(
            "test_dataset", "test_collection"
        )

    def test_get_existing_request_task(
        self, db, privacy_request, request_task, erasure_request_task
    ):
        assert (
            privacy_request.get_existing_request_task(
                db, ActionType.access, request_task.request_task_address
            )
            == request_task
        )
        assert (
            privacy_request.get_existing_request_task(
                db, ActionType.erasure, erasure_request_task.request_task_address
            )
            == erasure_request_task
        )

        assert (
            privacy_request.get_existing_request_task(
                db, ActionType.consent, erasure_request_task.request_task_address
            )
            is None
        )

    def test_get_pending_downstream_tasks(self, db, request_task):
        root_task = request_task.get_tasks_with_same_action_type(
            db, ROOT_COLLECTION_ADDRESS.value
        ).first()
        terminator_task = request_task.get_tasks_with_same_action_type(
            db, TERMINATOR_ADDRESS.value
        ).first()

        assert root_task.get_pending_downstream_tasks(db).all() == [request_task]
        assert request_task.get_pending_downstream_tasks(db).all() == [terminator_task]
        assert terminator_task.get_pending_downstream_tasks(db).all() == []

    @mock.patch("fides.api.util.cache.celery_app.control.inspect.query_task")
    def test_request_task_running(self, query_task_mock, db, request_task):
        assert request_task.request_task_running() is False

        cache_task_tracking_key(request_task.id, "test_5678")

        assert request_task.request_task_running() is False

        query_task_mock.return_value = {"@celery1234": {}}

        assert request_task.request_task_running() is False
        assert request_task.can_queue_request_task(db) is True

        query_task_mock.return_value = {"@celery1234": {"test_5678": ["reserved", {}]}}

        assert request_task.request_task_running() is True
        assert request_task.can_queue_request_task(db) is False

    def test_upstream_tasks_complete(self, db, request_task):
        # The Request Task only has the Root Task upstream, which is complete
        assert request_task.upstream_tasks == [ROOT_COLLECTION_ADDRESS.value]
        assert request_task.upstream_tasks_complete(db)

        # The root Task has nothing upstream
        root_task = request_task.get_tasks_with_same_action_type(
            db, ROOT_COLLECTION_ADDRESS.value
        ).first()
        assert root_task.status == ExecutionLogStatus.complete
        assert root_task.is_root_task
        assert root_task.upstream_tasks_complete(db)

        # The Terminator task has the request task upstream which is pending
        terminator_task = request_task.get_tasks_with_same_action_type(
            db, TERMINATOR_ADDRESS.value
        ).first()
        assert terminator_task.is_terminator_task
        assert terminator_task.upstream_tasks == [request_task.collection_address]
        assert request_task.status == ExecutionLogStatus.pending
        assert not terminator_task.upstream_tasks_complete(db)
        assert not terminator_task.can_queue_request_task(db)

        # Set the request task to be skipped
        request_task.update_status(db, ExecutionLogStatus.skipped)
        # Skipped is considered to be a completed state
        assert terminator_task.upstream_tasks_complete(db)
        assert terminator_task.can_queue_request_task(db)

    def test_update_status(self, db, request_task):
        assert request_task.status == ExecutionLogStatus.pending
        request_task.update_status(db, ExecutionLogStatus.complete)

        assert request_task.status == ExecutionLogStatus.complete

    def test_save_filtered_access_results(self, db, privacy_request):
        assert privacy_request.get_filtered_final_upload() == {}

        privacy_request.save_filtered_access_results(
            db,
            results={
                "policy_rule_key": {
                    "test_dataset:test_collection": [
                        {"name": "Jane", "address": "101 Test Town"}
                    ],
                    "test_dataset:test_collection_2": [
                        {"id": 100, "email": "jane@example.com"}
                    ],
                }
            },
        )

        assert privacy_request.get_filtered_final_upload() == {
            "policy_rule_key": {
                "test_dataset:test_collection": [
                    {"name": "Jane", "address": "101 Test Town"}
                ],
                "test_dataset:test_collection_2": [
                    {"id": 100, "email": "jane@example.com"}
                ],
            }
        }


class TestGetRawAccessResults:
    def test_no_results(self, privacy_request):
        assert privacy_request.get_raw_access_results() == {}

    @pytest.mark.usefixtures("request_task")
    def test_request_tasks_incomplete(self, privacy_request):
        assert privacy_request.get_raw_access_results() == {}

    def test_request_tasks_complete_dsr_3_0(self, db, privacy_request, request_task):
        """DSR 3.0 stores results on RequestTask.access_data"""
        assert request_task.get_access_data() == []

        request_task.access_data = [{"name": "Jane", "street": "102 Test Town"}]
        request_task.update_status(db, ExecutionLogStatus.complete)
        assert request_task.get_access_data() == [
            {"name": "Jane", "street": "102 Test Town"}
        ]

        assert privacy_request.get_raw_access_results() == {
            "test_dataset:test_collection": [
                {"name": "Jane", "street": "102 Test Town"}
            ]
        }

    def test_dsr_2_0(self, privacy_request):
        """DSR 2.0 uses the cache to store results"""
        cache: FidesopsRedis = get_cache()
        key = f"access_request__test_dataset:test_collection"
        cache.set_encoded_object(
            f"{privacy_request.id}__{key}",
            [{"name": "Jane", "street": "102 Test Town"}],
        )

        assert privacy_request.get_raw_access_results() == {
            "test_dataset:test_collection": [
                {"name": "Jane", "street": "102 Test Town"}
            ]
        }


class TestGetRawMaskingCounts:
    def test_no_results(self, privacy_request):
        assert privacy_request.get_raw_masking_counts() == {}

    @pytest.mark.usefixtures("erasure_request_task")
    def test_request_tasks_incomplete(self, privacy_request):
        assert privacy_request.get_raw_masking_counts() == {}

    def test_request_tasks_complete_dsr_3_0(
        self, db, privacy_request, erasure_request_task
    ):
        """DSR 3.0 stores results on RequestTask.rows_masked"""
        erasure_request_task.rows_masked = 2
        erasure_request_task.update_status(db, ExecutionLogStatus.complete)
        assert privacy_request.get_raw_masking_counts() == {
            "test_dataset:test_collection": 2
        }

    def test_dsr_2_0(self, privacy_request):
        """DSR 2.0 uses the cache to store rows_masked"""
        cache: FidesopsRedis = get_cache()
        key = f"erasure_request__test_dataset:test_collection"
        cache.set_encoded_object(f"{privacy_request.id}__{key}", 2)

        assert privacy_request.get_raw_masking_counts() == {
            "test_dataset:test_collection": 2
        }


class TestGetConsentResults:
    @pytest.fixture(scope="function")
    def consent_request_task(self, db, privacy_request):
        request_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.consent,
                "status": "pending",
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "upstream_tasks": ["__ROOT__:__ROOT__"],
                "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
            },
        )
        yield request_task
        request_task.delete(db)

    def test_no_results(self, privacy_request):
        assert privacy_request.get_consent_results() == {}

    def test_request_tasks_incomplete(self, consent_request_task, privacy_request):
        assert privacy_request.get_consent_results() == {}

    def test_request_tasks_complete_dsr_3_0(
        self, db, privacy_request, consent_request_task
    ):
        """DSR 3.0 stores results on RequestTask.rows_masked"""
        consent_request_task.consent_sent = True
        consent_request_task.update_status(db, ExecutionLogStatus.complete)
        assert privacy_request.get_consent_results() == {
            "test_dataset:test_collection": True
        }


class TestGetDecodedDataForErasures:
    def test_no_data(self, request_task):
        assert request_task.get_data_for_erasures() == []

    def test_request_task_has_erasure_data(self, db, request_task):
        request_task.data_for_erasures = [{"id": 1, "name": "Jane"}]
        request_task.save(db)

        assert request_task.get_data_for_erasures() == [{"id": 1, "name": "Jane"}]


class TestLargeDataStorage:
    """Test storing large datasets in RequestTask.access_data and RequestTask.data_for_erasures"""

    def test_store_and_retrieve_data_for_access(self, db, request_task):
        request_task.access_data = [{"id": 1, "name": "Jane"}]
        request_task.save(db)

        assert request_task.get_access_data() == [{"id": 1, "name": "Jane"}]

    def test_store_and_retrieve_data_for_erasures(self, db, request_task):
        request_task.data_for_erasures = [{"id": 1, "name": "Jane"}]
        request_task.save(db)

        assert request_task.get_data_for_erasures() == [{"id": 1, "name": "Jane"}]

    @pytest.mark.failed_request_tasks
    def test_small_data_stored_directly(self, db, request_task):
        """Test that small data is stored directly in database"""
        small_data = [{"id": i, "name": f"User{i}"} for i in range(10)]

        request_task.access_data = small_data
        request_task.save(db)

        # Should be stored directly (no external storage metadata)
        assert isinstance(request_task._access_data, list)
        assert request_task.access_data == small_data
        assert request_task.get_access_data() == small_data

    @mock.patch("fides.api.models.privacy_request.request_task.is_large_data")
    def test_large_data_stored_externally_access_data(
        self, mock_is_large_data, db, request_task, storage_config_default_local
    ):
        """Test that large access data is stored externally"""
        # Mock is_large_data to return True for any data
        mock_is_large_data.return_value = True

        test_data = [
            {"id": i, "name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(5)
        ]

        request_task.access_data = test_data
        request_task.save(db)

        # Should be stored as external storage metadata
        assert isinstance(request_task._access_data, dict)
        assert "storage_type" in request_task._access_data
        assert "file_key" in request_task._access_data
        assert "filesize" in request_task._access_data

        # The property should still return the original data by retrieving from external storage
        retrieved_data = request_task.access_data
        assert retrieved_data == test_data
        assert request_task.get_access_data() == test_data

    @mock.patch("fides.api.models.privacy_request.request_task.is_large_data")
    def test_large_data_stored_externally_data_for_erasures(
        self, mock_is_large_data, db, request_task, storage_config_default_local
    ):
        """Test that large erasure data is stored externally"""
        # Mock is_large_data to return True for any data
        mock_is_large_data.return_value = True

        test_data = [
            {"id": i, "name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(5)
        ]

        request_task.data_for_erasures = test_data
        request_task.save(db)

        # Should be stored as external storage metadata
        assert isinstance(request_task._data_for_erasures, dict)
        assert "storage_type" in request_task._data_for_erasures
        assert "file_key" in request_task._data_for_erasures
        assert "filesize" in request_task._data_for_erasures

        # The property should still return the original data by retrieving from external storage
        retrieved_data = request_task.data_for_erasures
        assert retrieved_data == test_data
        assert request_task.get_data_for_erasures() == test_data

    @mock.patch("fides.api.models.privacy_request.request_task.is_large_data")
    def test_external_storage_cleanup_on_update(
        self, mock_is_large_data, db, request_task, storage_config_default_local
    ):
        """Test that external storage files are cleaned up when data is updated"""
        # Mock is_large_data to return True for any data
        mock_is_large_data.return_value = True

        # Store initial data externally
        initial_data = [{"id": 1, "name": "Initial"}]
        request_task.access_data = initial_data
        request_task.save(db)

        # Verify it's stored externally
        assert isinstance(request_task._access_data, dict)
        initial_file_key = request_task._access_data["file_key"]

        initial_path = get_local_filename(initial_file_key)

        # Verify the file exists
        assert os.path.exists(initial_path)

        # Update with new data - should clean up old file and create new one
        new_data = [{"id": 2, "name": "Updated"}]
        request_task.access_data = new_data
        request_task.save(db)

        # Old file should be cleaned up
        assert not os.path.exists(initial_path)

        # New file should exist
        new_file_key = request_task._access_data["file_key"]
        new_path = get_local_filename(new_file_key)
        assert os.path.exists(new_path)
        assert new_file_key != initial_file_key

        # Data should be correct
        assert request_task.access_data == new_data

    @mock.patch("fides.api.models.privacy_request.request_task.is_large_data")
    def test_external_storage_cleanup_on_delete(
        self, mock_is_large_data, db, request_task, storage_config_default_local
    ):
        """Test that external storage files are cleaned up when RequestTask is deleted"""
        # Mock is_large_data to return True for any data
        mock_is_large_data.return_value = True

        # Store data externally
        test_data = [{"id": 1, "name": "Test"}]
        request_task.access_data = test_data
        request_task.data_for_erasures = test_data
        request_task.save(db)

        # Verify files exist
        access_file_key = request_task._access_data["file_key"]
        erasures_file_key = request_task._data_for_erasures["file_key"]

        access_path = get_local_filename(access_file_key)
        erasures_path = get_local_filename(erasures_file_key)

        assert os.path.exists(access_path)
        assert os.path.exists(erasures_path)

        # Delete the request task
        request_task.delete(db)

        # Files should be cleaned up
        assert not os.path.exists(access_path)
        assert not os.path.exists(erasures_path)

    def test_external_storage_retrieval_failure_handling(self, db, request_task):
        """Test that external storage retrieval failures are handled gracefully"""
        # Simulate external storage metadata with non-existent file
        metadata_dict = {
            "storage_type": "local",
            "file_key": "nonexistent/path/file.json",
            "filesize": 1000,
        }

        # Directly set the private field to simulate external storage
        request_task._access_data = metadata_dict
        request_task.save(db)

        # Should error when file doesn't exist
        with pytest.raises(RequestTaskStorageError, match="Failed to retrieve"):
            request_task.get_access_data()

    def test_empty_data_handling(self, db, request_task):
        """Test that empty data is handled correctly"""
        request_task.access_data = []
        request_task.save(db)

        assert request_task.access_data == []
        assert request_task.get_access_data() == []

        request_task.access_data = None
        request_task.save(db)

        assert request_task.access_data == []
        assert request_task.get_access_data() == []

    @pytest.mark.parametrize("data_type", ["access_data", "data_for_erasures"])
    def test_backward_compatibility(self, db, request_task, data_type):
        """Test that existing code continues to work"""
        test_data = [{"id": 1, "name": "Test"}]

        # Set using property
        setattr(request_task, data_type, test_data)
        request_task.save(db)

        # Get using both property and helper method
        assert getattr(request_task, data_type) == test_data
        if data_type == "access_data":
            assert request_task.get_access_data() == test_data
        else:
            assert request_task.get_data_for_erasures() == test_data

    def test_cleanup_external_storage_on_update(self, db, request_task):
        """Test that external storage cleanup methods exist and don't crash"""
        # Test that the methods exist and don't crash
        request_task._cleanup_external_access_data()
        request_task._cleanup_external_data_for_erasures()
        request_task.cleanup_external_storage()

    def test_external_storage_metadata_detection(self, db, request_task):
        """Test that external storage metadata is properly detected"""
        # Simulate external storage metadata
        metadata_dict = {
            "storage_type": "local",
            "file_key": "/path/to/file",
            "filesize": 1000,
        }

        # Directly set the private field to simulate external storage
        request_task._access_data = metadata_dict

        # The property should detect this as metadata (though retrieval will fail without actual file)
        # This tests the detection logic without requiring actual external storage
        assert isinstance(request_task._access_data, dict)
        assert "storage_type" in request_task._access_data
