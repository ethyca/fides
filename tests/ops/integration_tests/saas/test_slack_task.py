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
@pytest.mark.integration_slack
def test_slack_connection_test(slack_connection_config) -> None:
    get_connector(slack_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_slack
@pytest.mark.asyncio
async def test_saas_access_request_task(
    db,
    policy,
    slack_connection_config,
    slack_dataset_config,
    slack_identity_email,
) -> None:
    """Full access request based on the slack SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_slack_access_request_task_{random.randint(0, 250)}"
    )
    identity_attribute = "email"
    identity_value = slack_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)
    dataset_name = slack_connection_config.get_saas_config().fides_key
    merged_graph = slack_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [slack_connection_config],
        {identity_attribute: slack_identity_email},
        db,
    )
    key_user = f"{dataset_name}:users_lookup_By_Email"
    assert_rows_match(
        v[key_user],
        min_size=1,
        keys=[
            "id",
            "team_id",
            "name",
            "deleted",
            "real_name",
            "updated",
            "profile",
        ],
    )

    profile = v[key_user]["profile"]
    assert profile["email"] == slack_identity_email
