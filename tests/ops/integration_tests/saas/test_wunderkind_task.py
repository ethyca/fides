import json
import random
from unittest import mock
from uuid import uuid4

import pytest

from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
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
@pytest.mark.integration_wunderkind
def test_wunderkind_connection_test(
    wunderkind_connection_config,
) -> None:
    get_connector(wunderkind_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_wunderkind
@pytest.mark.asyncio
async def test_wunderkind_consent_request_task(
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
) -> None:
    """Full consent request based on the Wunderkind SaaS config"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "wunderkind_instance"

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([wunderkind_dataset_config]),
        [wunderkind_connection_config],
        {"email": wunderkind_identity_email},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    wunderkind_logs = execution_logs.filter_by(collection_name=dataset_name).order_by(
        "created_at"
    )
    assert wunderkind_logs.count() == 2

    assert [log.status for log in wunderkind_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in wunderkind_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent


@pytest.mark.integration_saas
@pytest.mark.integration_wunderkind
@pytest.mark.asyncio
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_wunderkind_consent_preparedw_requests(
    mocked_client_send,
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([wunderkind_dataset_config]),
        [wunderkind_connection_config],
        {"email": wunderkind_identity_email},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert saas_request_params.path == "/ccpa"
    query_params = mocked_client_send.call_args[0][0].query_params
    assert query_params["id_type"] == "email"
    assert query_params["id_value"] == wunderkind_identity_email
    assert query_params["consent"] == "1YN"
    assert (
        query_params["website_id"] == wunderkind_connection_config.secrets["website_id"]
    )
