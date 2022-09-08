import logging
import random

import pytest

from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.ops.service.connectors import get_connector
from fidesops.ops.task import graph_task
from tests.ops.graph.graph_test_util import assert_rows_match

logger = logging.getLogger(__name__)


@pytest.mark.integration_saas
@pytest.mark.integration_datadog
def test_datadog_connection_test(datadog_connection_config) -> None:
    get_connector(datadog_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_datadog
@pytest.mark.asyncio
async def test_saas_access_request_task(
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
    identity = PrivacyRequestIdentity(**identity_kwargs)
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
