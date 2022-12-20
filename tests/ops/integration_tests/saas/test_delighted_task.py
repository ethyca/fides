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
@pytest.mark.integration_delighted
def test_delighted_connection_test(delighted_connection_config) -> None:
    get_connector(delighted_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_delighted
@pytest.mark.asyncio
async def test_delighted_access_request_task(
    policy,
    delighted_identity_email,
    delighted_connection_config,
    delighted_dataset_config,
    db,
) -> None:
    """Full access request based on the Delighted SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_delighted_access_request_task_{random.randint(0, 1000)}"
    )
    identity_kwargs = {"email": delighted_identity_email}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = delighted_connection_config.get_saas_config().fides_key
    merged_graph = delighted_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [delighted_connection_config],
        identity_kwargs,
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:people"],
        min_size=1,
        keys=[
            "id",
            "name",
            "email",
            "created_at",
            "last_sent_at",
            "last_responded_at",
            "next_survey_scheduled_at",
        ],
    )

    # verify we only returned data for our identity
    assert v[f"{dataset_name}:people"][0]["email"] == delighted_identity_email

    assert_rows_match(
        v[f"{dataset_name}:survey_response"],
        min_size=1,
        keys=[
            "id",
            "person",
            "survey_type",
            "score",
            "comment",
            "permalink"
            "created_at",
            "updated_at",
        ],
    )