import pytest
from sqlalchemy.orm import Query

from fides.api.models.privacy_request.request_task import RequestTask, TraversalDetails
from fides.api.schemas.privacy_request import ActionType, ExecutionLogStatus


@pytest.fixture
def request_task_data(privacy_request):
    return {
        "action_type": ActionType.access,
        "status": "pending",
        "privacy_request_id": privacy_request.id,
        "collection_address": "test_dataset:test_collection",
        "dataset_name": "test_dataset",
        "collection_name": "test_collection",
        "upstream_tasks": ["__ROOT__:__ROOT__"],
        "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
        "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
    }


def test_traversal_details_initialization():
    # Test initialization with all fields
    traversal_details = TraversalDetails(
        dataset_connection_key="test_connection_key",
        incoming_edges=[("node1", "node2")],
        outgoing_edges=[("node2", "node3")],
        input_keys=["key1", "key2"],
        skipped_nodes=[("node3", "node4")],
    )

    assert traversal_details.dataset_connection_key == "test_connection_key"
    assert traversal_details.incoming_edges == [("node1", "node2")]
    assert traversal_details.outgoing_edges == [("node2", "node3")]
    assert traversal_details.input_keys == ["key1", "key2"]
    assert traversal_details.skipped_nodes == [("node3", "node4")]


def test_traversal_details_optional_fields():
    # Test initialization without optional fields
    traversal_details = TraversalDetails(
        dataset_connection_key="test_connection_key",
        incoming_edges=[("node1", "node2")],
        outgoing_edges=[("node2", "node3")],
        input_keys=["key1", "key2"],
    )

    assert traversal_details.dataset_connection_key == "test_connection_key"
    assert traversal_details.incoming_edges == [("node1", "node2")]
    assert traversal_details.outgoing_edges == [("node2", "node3")]
    assert traversal_details.input_keys == ["key1", "key2"]
    assert (
        traversal_details.skipped_nodes is None
    )  # Optional field should default to None


def test_create_empty_traversal():
    # Test the create_empty_traversal method
    connection_key = "empty_connection_key"
    traversal_details = TraversalDetails.create_empty_traversal(connection_key)

    assert traversal_details.dataset_connection_key == connection_key
    assert traversal_details.incoming_edges == []
    assert traversal_details.outgoing_edges == []
    assert traversal_details.input_keys == []
    assert traversal_details.skipped_nodes == []


def test_create_request_task(db, privacy_request, request_task_data):
    # Create a RequestTask
    request_task = RequestTask.create(db, data=request_task_data)

    # Query the RequestTask
    retrieved_task = db.query(RequestTask).filter_by(id=request_task.id).first()
    assert retrieved_task is not None
    assert retrieved_task.privacy_request_id == privacy_request.id
    assert retrieved_task.status == ExecutionLogStatus.pending
    assert retrieved_task.traversal_details is None
    assert retrieved_task.action_type == ActionType.access
    assert retrieved_task.collection_address == "test_dataset:test_collection"
    assert retrieved_task.traversal_details is None
    assert retrieved_task.is_root_task is False
    assert retrieved_task.is_terminator_task is False

    request_task.delete(db)


def test_request_task_update_status(db, request_task):
    assert request_task.status == ExecutionLogStatus.pending
    # Update the status of the RequestTask
    request_task.update_status(db, ExecutionLogStatus.complete)

    assert request_task.status == ExecutionLogStatus.complete


def test_request_task_get_tasks_with_same_action_type(
    db, request_task, request_task_data
):
    same_actions = request_task.get_tasks_with_same_action_type(
        db, request_task.collection_address
    ).all()
    assert len(same_actions) == 1
    assert same_actions == [request_task]

    # Create a RequestTask with the same action_type
    request_task_2 = RequestTask.create(db, data=request_task_data)
    # Create a RequestTask with a different action_type
    request_task_data["action_type"] = ActionType.consent
    request_task_3 = RequestTask.create(db, data=request_task_data)

    # Query the RequestTask
    tasks = request_task.get_tasks_with_same_action_type(
        db, request_task.collection_address
    ).all()
    assert len(tasks) == 2
    assert request_task in tasks
    assert request_task_2 in tasks
    assert request_task_3 not in tasks

    request_task_2.delete(db)
    request_task_3.delete(db)


def test_request_task_get_pending_downstream_tasks(db, request_task):
    # Query the RequestTask
    pending_downstream_tasks = request_task.get_pending_downstream_tasks(db).all()
    assert len(pending_downstream_tasks) == 1
    assert pending_downstream_tasks[0].status == ExecutionLogStatus.pending
    assert pending_downstream_tasks[0].id != request_task.id


def test_request_task_upstream_tasks_complete(db, request_task):
    assert request_task.upstream_tasks_complete(db) is True

    upstream_tasks = request_task.upstream_tasks_objects(db).all()
    upstream_tasks[0].update_status(db, ExecutionLogStatus.pending)

    assert request_task.upstream_tasks_complete(db) is False


def test_request_task_running(request_task, monkeypatch):
    assert request_task.request_task_running() is False

    def mock_task_id(self):
        return "mock_celery_task_id"

    def mock_in_flight(task_ids):
        return task_ids == ["mock_celery_task_id"]

    monkeypatch.setattr(RequestTask, "get_cached_task_id", mock_task_id)
    monkeypatch.setattr(
        "fides.api.models.privacy_request.request_task.celery_tasks_in_flight",
        mock_in_flight,
    )

    assert request_task.request_task_running() is True


def test_request_task_can_queue_request_task(db, request_task, monkeypatch):
    assert request_task.can_queue_request_task(db) is True

    def mock_running(self, should_log=False):
        return True

    monkeypatch.setattr(RequestTask, "request_task_running", mock_running)

    assert request_task.can_queue_request_task(db) is False
