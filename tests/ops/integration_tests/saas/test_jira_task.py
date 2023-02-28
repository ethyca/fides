import random
import time

import pytest
import requests

from time import sleep
from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match
from requests.auth import HTTPBasicAuth

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_jira
def test_jira_connection_test(jira_connection_config) -> None:
    get_connector(jira_connection_config).test_connection()

@pytest.mark.integration_saas
@pytest.mark.integration_jira
@pytest.mark.asyncio
async def test_jira_access_request_task(
    db,
    policy,
    jira_connection_config,
    jira_dataset_config,
    jira_identity_email,
    # jira_user_name,
) -> None:
    """Full access request based on the jira SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_jira_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": jira_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = jira_connection_config.get_saas_config().fides_key
    merged_graph = jira_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [jira_connection_config],
        {"email": jira_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customers"],
        min_size=1,
        keys=[
            "self",
            "accountId",
            "accountType",
            "emailAddress",
            "avatarUrls",
            "displayName",
            "active",
            "locale",
        ],
    )

    # verify we only returned data for our identity email
    # assert v[f"{dataset_name}:customers"][0]["displayName"] == jira_user_name
    user_id = v[f"{dataset_name}:customers"][0]["accountId"]


@pytest.mark.integration_saas
@pytest.mark.integration_jira
@pytest.mark.asyncio
async def test_jira_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    jira_connection_config,
    jira_dataset_config,
    jira_erasure_identity_email,
    jira_create_erasure_data,
) -> None:
    """Full erasure request based on the jira SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_jira_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": jira_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = jira_connection_config.get_saas_config().fides_key
    merged_graph = jira_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    
    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [jira_connection_config],
        {"email": jira_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customers"],
        min_size=1,
        keys=[
            "self",
            "accountId",
            "accountType",
            "emailAddress",
            "avatarUrls",
            "displayName",
            "active",
            "locale",
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [jira_connection_config],
        {"email": jira_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:customers": 1,
    }

    jira_secrets = jira_connection_config.secrets
    base_url = f"https://{jira_secrets['domain']}"

    # user
    response = requests.get(
        url=f"{base_url}/rest/api/3/user/search",
        params={"query": jira_erasure_identity_email},
        auth=HTTPBasicAuth(
            f"{jira_secrets['username']}", f"{jira_secrets['api_key']}"
        ),
    )
    # Since user is deleted, it won't return data
    assert response.json() is None

    CONFIG.execution.masking_strict = masking_strict