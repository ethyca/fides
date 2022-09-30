import random
import time

import pytest
import requests

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.ctl.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_marketo
@pytest.mark.asyncio
async def test_marketo_access_request_task(
    db,
    policy,
    marketo_connection_config,
    marketo_dataset_config,
    marketo_identity_email,
) -> None:
    """Full access request based on the Marketo SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_marketo_access_request_task_{random.randint(0, 1000)}"
    )
    identity_kwargs = {"email": marketo_identity_email}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = marketo_connection_config.get_saas_config().fides_key
    merged_graph = marketo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [marketo_connection_config],
        identity_kwargs,
        db,
    )
