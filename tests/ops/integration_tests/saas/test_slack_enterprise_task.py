import random

import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task import graph_task
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
def test_slack_enterprise_connection_test(slack_enterprise_connection_config) -> None:
    get_connector(slack_enterprise_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.asyncio
async def test_slack_enterprise_access_request_task(
    db,
    policy,
    slack_enterprise_connection_config,
    slack_enterprise_dataset_config,
    slack_enterprise_identity_email,
) -> None:
    """Full access request based on the Slack Enterprise SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_slack_enterprise_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = slack_enterprise_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)
    dataset_name = slack_enterprise_connection_config.get_saas_config().fides_key
    merged_graph = slack_enterprise_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [slack_enterprise_connection_config],
        {identity_attribute: slack_enterprise_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "id",
            "team_id",
            "name",
            "deleted",
            "color",
            "real_name",
            "tz",
            "tz_label",
            "tz_offset",
            "profile",
            "is_admin",
            "is_owner",
            "is_primary_owner",
            "is_restricted",
            "is_ultra_restricted",
            "is_bot",
            "is_app_user",
            "updated",
            "is_email_confirmed",
            "who_can_share_contact_card",
        ],
    )

    user = v[f"{dataset_name}:user"][0]
    assert user["profile"]["email"] == slack_enterprise_identity_email
