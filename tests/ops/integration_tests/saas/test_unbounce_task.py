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
    """Full access request based on the unbounce SaaS config"""

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

    # assert_rows_match(
    #     v[f"{dataset_name}:all_leads"],
    #     min_size=1,
    #     keys=[
    #         "created_at",
    #         "id",
    #         "extra_data",
    #         "form_data",
    #         "page_id",
    #         "variant_id",
    #         "metadata",
    #     ],
    # )

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
            "metadata",
        ],
    )

    # verify we only returned data for our identity email
    unbounce_secrets = unbounce_connection_config.secrets
    # for lead_list in v[f"{dataset_name}:lead"]:
    #     assert lead_list["page_id"] == f"{unbounce_secrets['page_id']}"
    assert v[f"{dataset_name}:lead"][0]["id"] == f"{unbounce_secrets['lead_id']}"