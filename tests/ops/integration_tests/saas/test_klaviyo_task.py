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
@pytest.mark.integration_klaviyo
def test_klaviyo_connection_test(klaviyo_connection_config) -> None:
    get_connector(klaviyo_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_klaviyo
@pytest.mark.asyncio
async def test_klaviyo_access_request_task(
    db,
    policy,
    klaviyo_connection_config,
    klaviyo_dataset_config,
    klaviyo_identity_email,
) -> None:
    """Full access request based on the klaviyo SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_klaviyo_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": klaviyo_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = klaviyo_connection_config.get_saas_config().fides_key
    merged_graph = klaviyo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [klaviyo_connection_config],
        {"email": klaviyo_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:profiles"],
        min_size=1,
        keys=[
            "type",
            "id",
            "attributes",
            "links",
            "relationships"
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:profiles"][0]['attributes']["email"] == klaviyo_identity_email
    user_id = v[f"{dataset_name}:profiles"][0]["id"]


@pytest.mark.integration_saas
@pytest.mark.integration_klaviyo
@pytest.mark.asyncio
async def test_klaviyo_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    klaviyo_connection_config,
    klaviyo_dataset_config,
    klaviyo_erasure_identity_email,
    klaviyo_create_erasure_data,
) -> None:
    """Full erasure request based on the klaviyo SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_klaviyo_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": klaviyo_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = klaviyo_connection_config.get_saas_config().fides_key
    merged_graph = klaviyo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [klaviyo_connection_config],
        {"email": klaviyo_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:profiles"],
        min_size=1,
        keys=[
            "type",
            "id",
            "attributes",
            "links",
            "relationships"
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [klaviyo_connection_config],
        {"email": klaviyo_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:profiles": 1,
    }

    klaviyo_secrets = klaviyo_connection_config.secrets
    base_url = f"https://{klaviyo_secrets['domain']}"
    headers = {
        "Authorization": f"Klaviyo-API-Key {klaviyo_secrets['api_key']}",
        "revision": klaviyo_secrets['revision']
    }

    # user
    response = requests.get(
        url=f"{base_url}/api/profiles",
        headers=headers,
        params={"filter": "equals(email,'"+klaviyo_erasure_identity_email+"')"},
    )
    # Since user is deleted, it won't be available so response is 404
    assert response.status_code == 200

    CONFIG.execution.masking_strict = masking_strict
