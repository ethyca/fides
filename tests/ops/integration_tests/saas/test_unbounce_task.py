import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_unbounce
def test_unbounce_connection_test(unbounce_connection_config) -> None:
    get_connector(unbounce_connection_config).test_connection()

@pytest.mark.integration_saas
@pytest.mark.integration_unbounce
@pytest.mark.asyncio
async def test_unbounce_access_request_task(
    db,
    policy,
    unbounce_connection_config,
    unbounce_dataset_config,
    unbounce_identity_email,
) -> None:
    """Full access request based on the Unbounce SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_unbounce_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": unbounce_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = unbounce_connection_config.get_saas_config().fides_key
    merged_graph = unbounce_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [unbounce_connection_config],
        {"email": unbounce_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:pages"],
        min_size=1,
        keys=[
            "subAccountId",
            "integrations",
            "integrationsCount",
            "integrationsErrorsCount",
            "id",
            "url",
            "metadata",
            "createdAt",
            "name",
            "state",
            "lastPublishedAt",
            "variantsCount",
            "domain"
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:lead"],
        min_size=1,
        keys=[
            "created_at",
            "id",
            "extra_data",
            "form_data",
            "page_id",
            "variant_id",
            "metadata"
        ],
    )

    # verify we only returned data for our identity email
    for leads in v[f"{dataset_name}:lead"]:
        assert leads["form_data"]['email'] == unbounce_identity_email