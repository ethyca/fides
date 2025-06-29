import pytest

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.graph.config import CollectionAddress
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskConfigurationType,
    ManualTaskEntityType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskParentEntityType,
    ManualTaskSubmission,
    ManualTaskType,
    StatusType,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
from fides.api.task.task_resources import TaskResources


@pytest.fixture
def erasure_policy(db):
    """Create a minimal policy used for erasure tests"""
    return Policy.create(
        db=db,
        data={
            "name": "Test Erasure Policy",
            "key": "test_erasure_policy",
        },
    )


@pytest.fixture
def connection_with_manual_erasure_task(db):
    """Create a connection config with an erasure manual task and one text field"""
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "erasure_test_connection",
            "connection_type": ConnectionType.postgres,
            "name": "Erasure Test Connection",
            "access": AccessLevel.write,
            "secrets": {
                "host": "localhost",
                "port": 5432,
                "user": "test",
                "password": "test",
                "dbname": "test",
            },
        },
    )

    manual_task = ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": connection_config.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )

    manual_config = ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.erasure_privacy_request,
            "version": 1,
            "is_current": True,
        },
    )

    field = ManualTaskConfigField.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_key": "confirm_erasure",
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {
                "label": "Confirmation",
                "required": True,
            },
        },
    )

    yield connection_config, manual_task, manual_config, field


def _build_request_task(db, privacy_request, connection_config):
    """Helper to create a minimal RequestTask for the manual_data collection"""
    collection_address = f"{connection_config.key}:manual_data"
    return RequestTask.create(
        db=db,
        data={
            "privacy_request_id": privacy_request.id,
            "collection_address": collection_address,
            "dataset_name": connection_config.key,
            "collection_name": "manual_data",
            "action_type": ActionType.erasure.value,
            "status": ExecutionLogStatus.pending.value,
            "upstream_tasks": [],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
            "collection": {
                "name": "manual_data",
                "fields": [],
                "after": [],
                "erase_after": [],
                "grouped_inputs": [],
                "data_categories": [],
            },
            "traversal_details": {
                "dataset_connection_key": connection_config.key,
                "incoming_edges": [],
                "outgoing_edges": [],
                "input_keys": [],
            },
        },
    )


def _build_task_resources(db, privacy_request, policy, connection_config, request_task):
    """Helper to build TaskResources object"""
    return TaskResources(
        request=privacy_request,
        policy=policy,
        connection_configs=[connection_config],
        privacy_request_task=request_task,
        session=db,
    )


def test_manual_task_erasure_flow(
    db, erasure_policy, connection_with_manual_erasure_task
):
    """Ensure ManualTaskGraphTask.erasure_request pauses until submissions then completes"""
    connection_config, manual_task, manual_config, field = (
        connection_with_manual_erasure_task
    )

    # Create privacy request
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": "manual_erasure_test_123",
            "started_processing_at": None,
            "status": PrivacyRequestStatus.pending,
            "policy_id": erasure_policy.id,
        },
    )

    # Build request task & resources
    request_task = _build_request_task(db, privacy_request, connection_config)
    resources = _build_task_resources(
        db, privacy_request, erasure_policy, connection_config, request_task
    )

    graph_task = ManualTaskGraphTask(resources)

    # First execution should pause awaiting input
    with pytest.raises(AwaitingAsyncTaskCallback):
        graph_task.erasure_request([], 0)

    db.refresh(privacy_request)
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # There should now be a ManualTaskInstance
    instance: ManualTaskInstance = (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.entity_id == privacy_request.id,
            ManualTaskInstance.task_id == manual_task.id,
        )
        .first()
    )
    assert instance is not None
    assert instance.status == StatusType.pending

    # Submit required field
    ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_id": field.id,
            "instance_id": instance.id,
            "data": {"value": "erasure confirmed"},
        },
    )

    # Mark instance completed
    instance.status = StatusType.completed
    instance.save(db)

    # Retry erasure_request – should now complete and return 0
    result = graph_task.erasure_request([], 0)
    assert result == 0

    # RequestTask.rows_masked should be 0
    db.refresh(request_task)
    assert request_task.rows_masked == 0
