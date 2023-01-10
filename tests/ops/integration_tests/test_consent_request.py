from uuid import uuid4

import pytest

from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fides.api.ops.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from fides.api.ops.task import graph_task


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consent_request_task(
    db,
    consent_policy,
    base_saas_connection_config,
    base_saas_dataset_config,
) -> None:

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        executable_consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([base_saas_dataset_config]),
        [base_saas_connection_config],
        {"email": "customer-1@example.com"},
        db,
    )

    assert v == {
        "mandril_test:mandril_test": True
    }, "graph has one node, and mocked request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    mandril_logs = execution_logs.filter_by(collection_name="mandril_test").order_by(
        "created_at"
    )
    assert mandril_logs.count() == 2

    assert [log.status for log in mandril_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in mandril_logs:
        assert log.dataset_name == "mandril_test"
        assert (
            log.collection_name == "mandril_test"
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent
