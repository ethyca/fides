import pytest

from fides.api.models.manual_task import (
    ManualTaskInstance,
    ManualTaskSubmission,
    StatusType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
from fides.api.task.task_resources import TaskResources


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
    db, erasure_policy, connection_with_manual_erasure_task, erasure_privacy_request
):
    """Ensure ManualTaskGraphTask.erasure_request pauses until submissions then completes"""
    connection_config, manual_task, manual_config, field = (
        connection_with_manual_erasure_task
    )

    # Build request task & resources
    request_task = _build_request_task(db, erasure_privacy_request, connection_config)
    resources = _build_task_resources(
        db, erasure_privacy_request, erasure_policy, connection_config, request_task
    )

    graph_task = ManualTaskGraphTask(resources)

    # First execution should pause the request and return None (AwaitingAsyncTaskCallback handled internally)
    initial_result = graph_task.erasure_request([], 0)
    assert initial_result is None

    db.refresh(erasure_privacy_request)
    assert erasure_privacy_request.status == PrivacyRequestStatus.requires_input

    # There should now be a ManualTaskInstance
    instance: ManualTaskInstance = (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.entity_id == erasure_privacy_request.id,
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
