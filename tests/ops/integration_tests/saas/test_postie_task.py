import random
import time

import pytest
import requests

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_postie
def test_postie_connection_test(postie_connection_config) -> None:
    get_connector(postie_connection_config).test_connection()

@pytest.mark.integration_saas
@pytest.mark.integration_postie
@pytest.mark.asyncio
async def test_postie_access_request_task(
    db,
    policy,
    postie_connection_config,
    postie_dataset_config,
    postie_identity_email,
) -> None:
    """Full access request based on the postie SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_postie_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": postie_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = postie_connection_config.get_saas_config().fides_key
    merged_graph = postie_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [postie_connection_config],
        {"email": postie_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:ccpa_members"],
        min_size=1,
        keys=[
            "id",
            "type",
        ],
    )

    # verify we only returned data for our identity email
    # assert v[f"{dataset_name}:users"][0]["email"] == postie_identity_email
    # user_id = v[f"{dataset_name}:users"][0]["id"]
