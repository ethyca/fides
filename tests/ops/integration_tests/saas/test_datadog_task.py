import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_datadog
def test_datadog_connection_test(datadog_connection_config) -> None:
    get_connector(datadog_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_datadog
@pytest.mark.asyncio
async def test_datadog_access_request_task_with_email(
    db,
    policy,
    datadog_connection_config,
    datadog_dataset_config,
    datadog_identity_email,
    datadog_access_data,
) -> None:
    """Full access request based on the Datadog SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_datadog_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = datadog_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = datadog_connection_config.get_saas_config().fides_key
    merged_graph = datadog_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [datadog_connection_config],
        {"email": datadog_identity_email},
        db,
    )
    key = f"{dataset_name}:events"

    assert_rows_match(
        v[key],
        min_size=1,
        keys=[
            "attributes",
            "type",
            "id",
        ],
    )

    for item in v[key]:
        assert_rows_match(
            [item["attributes"]],
            min_size=1,
            keys=[
                "status",
                "timestamp",
                "message",
                "tags",
            ],
        )

    for item in v[key]:
        assert datadog_identity_email in item["attributes"]["message"]


@pytest.mark.integration_saas
@pytest.mark.integration_datadog
@pytest.mark.asyncio
async def test_datadog_access_request_task_with_phone_number(
    db,
    policy,
    datadog_connection_config,
    datadog_dataset_config,
    datadog_identity_email,
    datadog_identity_phone_number,
    datadog_access_data,
) -> None:
    """Full access request based on the Datadog SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_datadog_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "phone_number"
    identity_value = datadog_identity_phone_number
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = datadog_connection_config.get_saas_config().fides_key
    merged_graph = datadog_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [datadog_connection_config],
        {"phone_number": datadog_identity_phone_number},
        db,
    )
    key = f"{dataset_name}:events"

    assert_rows_match(
        v[key],
        min_size=1,
        keys=[
            "attributes",
            "type",
            "id",
        ],
    )

    for item in v[key]:
        assert_rows_match(
            [item["attributes"]],
            min_size=1,
            keys=[
                "status",
                "timestamp",
                "message",
                "tags",
            ],
        )

    for item in v[key]:
        assert datadog_identity_phone_number in item["attributes"]["message"]
