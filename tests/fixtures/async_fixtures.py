import uuid
from datetime import datetime, timedelta

from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.task.create_request_tasks import collect_tasks_fn, persist_initial_erasure_request_tasks, persist_new_access_request_tasks
import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.request_task import AsyncTaskType, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.privacy_request import ActionType, PrivacyRequestStatus



## Privacy Request Fixtures
@pytest.fixture
def pending_privacy_request(db, policy):
    """Create a privacy request in the pending state"""
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid.uuid4())}",
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.pending,
            "origin": "https://example.com/testing",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture
def approved_privacy_request(db, policy):
    """Create a privacy request in the approved state"""
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid.uuid4())}",
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.approved,
            "origin": "https://example.com/testing",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture
def in_processing_privacy_request(db, policy):
    """Create a privacy request in the in_processing state"""
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid.uuid4())}",
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.in_processing,
            "origin": "https://example.com/testing",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield privacy_request
    privacy_request.delete(db)

## Request Task Fixtures
@pytest.fixture
def polling_request_task(db, in_processing_privacy_request):
    """Create a request task that is awaiting processing and is a polling task"""
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.awaiting_processing,
            "privacy_request_id": in_processing_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
            "async_type": AsyncTaskType.polling,
        },
    )
    yield request_task
    request_task.delete(db)


@pytest.fixture
def in_progress_polling_request_task(db, in_processing_privacy_request):
    """Create a request task that is in progress and is a polling task"""
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.in_processing,
            "privacy_request_id": in_processing_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
            "async_type": AsyncTaskType.polling,
        },
    )
    yield request_task
    request_task.delete(db)


@pytest.fixture
def callback_request_task(db, in_processing_privacy_request):
    """Create a request task that is awaiting processing and is a callback task"""
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.awaiting_processing,
            "privacy_request_id": in_processing_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
            "async_type": AsyncTaskType.callback,
        },
    )
    yield request_task
    request_task.delete(db)


@pytest.fixture
def non_async_request_task(db, pending_privacy_request):
    """Create a request task that is awaiting processing but is not a polling task"""
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.awaiting_processing,
            "privacy_request_id": pending_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
        },
    )
    yield request_task
    request_task.delete(db)

## access graph fixtures
@pytest.fixture
def async_graph(
    saas_async_polling_example_dataset_config, db, privacy_request
):
    # Build proper async graph with persisted request tasks to test the connector
    async_graph = saas_async_polling_example_dataset_config.get_graph()
    graph = DatasetGraph(async_graph)
    traversal = Traversal(graph, {"email": "customer-1@example.com"})
    traversal_nodes = {}
    end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)
    persist_new_access_request_tasks(
        db, privacy_request, traversal, traversal_nodes, end_nodes, graph
    )
    persist_initial_erasure_request_tasks(
        db, privacy_request, traversal_nodes, end_nodes, graph
    )
