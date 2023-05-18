import json
from unittest import mock
from uuid import uuid4

import pytest

from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.schemas.saas.saas_config import SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.ops.service.connectors import SaaSConnector, get_connector
from fides.api.ops.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from fides.api.ops.task import graph_task


@pytest.mark.integration_saas
@pytest.mark.integration_rudder_stack
def test_rudder_stack_connection_test(
    rudder_stack_connection_config,
) -> None:
    get_connector(rudder_stack_connection_config).test_connection()
@pytest.mark.integration_saas
@pytest.mark.integration_rudder_stack
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_rudder_stack_data")
async def test_rudder_stack_consent_request_task_new_workflow(
    db,
    consent_policy,
    rudder_stack_connection_config,
    rudder_stack_dataset_config,
    rudder_stack_identity_email,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
) -> None:
    """Full consent request based on the Rudder Stack SaaS config
    with new workflow where preferences are saved w.r.t privacy notices

    Assert that only relevant preferences get "complete" log, others get "skipped"
    """
    rudder_stack_connection_config.system_id = system.id
    rudder_stack_connection_config.save(db)

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    # This preference is relevant on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference is not relevant on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": rudder_stack_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "rudder_stack_instance"

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([rudder_stack_dataset_config]),
        [rudder_stack_connection_config],
        {"email": rudder_stack_identity_email},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    rudder_stack_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert rudder_stack_logs.count() == 2

    assert [log.status for log in rudder_stack_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in rudder_stack_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    connector = SaaSConnector(rudder_stack_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/v2/regulations",
        body=json.dumps({"email": rudder_stack_identity_email}),
    )
    response = connector.create_client().send(request)
    body = response.json()
    assert body == [], "Verify email has been removed from allowlist"

    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/v2/regulations",
        headers=[{
            'Content-type ': 'application/json'
        }],
        body=json.dumps({
            "regulationType": "suppress",
            "destinationIds": [
                "27OeyCriZ4vGFiOFPihSMgr0Nt1"
            ],
            "users": [
                {
                    "userId": "54321",
                    "phone": "+123456789",
                    "email": rudder_stack_identity_email
                }
            ]
        }),
    )
    response = connector.create_client().send(request)
    body = response.json()[0]
    assert (
        body['attributes']["email"] == rudder_stack_identity_email
    ), "Verify email has been added to denylist"
    #assert body["detail"] == "Added manually via the the API"

    # Assert affected system status of "complete" is cached for consent reporting.
    # Secondary user ids added to this preference.
    assert privacy_preference_history.affected_system_status == {
        rudder_stack_connection_config.system_key: ExecutionLogStatus.complete.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "email": rudder_stack_identity_email
    }

    # Assert that preferences that aren't relevant for the given system show the system as skipped
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        rudder_stack_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids


