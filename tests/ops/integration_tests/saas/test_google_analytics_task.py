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
@pytest.mark.integration_google_analytics
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
def test_google_analytics_connection_test(
    google_analytics_connection_config,
) -> None:
    get_connector(google_analytics_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_google_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
async def test_google_analytics_consent_request_task(
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    google_analytics_user_id,
) -> None:
    """Full consent request based on the Google Analytics SaaS config"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"user_id": google_analytics_user_id})
    privacy_request.cache_identity(identity)

    dataset_name = "google_analytics_instance"

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config]),
        [google_analytics_connection_config],
        {"user_id": google_analytics_user_id},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    google_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert google_analytics_logs.count() == 2

    assert [log.status for log in google_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in google_analytics_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent


@pytest.mark.integration_saas
@pytest.mark.integration_google_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_google_analytics_consent_prepared_requests(
    mocked_client_send,
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    google_analytics_user_id,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"user_id": google_analytics_user_id})
    privacy_request.cache_identity(identity)

    await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config]),
        [google_analytics_connection_config],
        {"user_id": google_analytics_user_id},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert (
        saas_request_params.path
        == "/analytics/v3/userDeletion/userDeletionRequests:upsert"
    )
    body = mocked_client_send.call_args[0][0].body

    assert google_analytics_user_id in body
    assert google_analytics_connection_config.secrets["property_id"] in body
