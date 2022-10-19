import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.ctl.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_domo
def test_domo_connection_test(domo_connection_config) -> None:
    get_connector(domo_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_domo
@pytest.mark.asyncio
async def test_domo_access_request_task(
    policy,
    domo_identity_email,
    domo_connection_config,
    domo_dataset_config,
    db,
) -> None:
    """Full access request based on the Domo SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_domo_access_request_task_{random.randint(0, 1000)}"
    )
    identity_kwargs = {"email": domo_identity_email}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = domo_connection_config.get_saas_config().fides_key
    merged_graph = domo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [domo_connection_config],
        identity_kwargs,
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=[
            "id",
            "title",
            "email",
            "role",
            "name",
            "department",
            "roleId",
            "createdAt",
            "updatedAt",
        ],
    )

    # verify we only returned data for our identity
    assert v[f"{dataset_name}:users"][0]["email"] == domo_identity_email