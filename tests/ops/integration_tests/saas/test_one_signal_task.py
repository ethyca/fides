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
@pytest.mark.integration_one_signal
def test_one_signal_connection_test(one_signal_connection_config) -> None:
    get_connector(one_signal_connection_config).test_connection()
    
@pytest.mark.integration_saas
@pytest.mark.integration_one_signal
@pytest.mark.asyncio
async def test_one_signal_access_request_task(
    db,
    policy,
    one_signal_connection_config,
    one_signal_dataset_config,
    one_signal_identity_email,
) -> None:
    """Full access request based on the one_signal SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_one_signal_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": one_signal_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = one_signal_connection_config.get_saas_config().fides_key
    merged_graph = one_signal_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [one_signal_connection_config],
        {"email": one_signal_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:device"],
        min_size=1,
        keys=[
            "id",
            "identifier",
            "session_count",
            "language",
            "timezone",
            "game_version",
            "device_os",
            "device_type",
            "device_model",
            "ad_id",
            "tags",
            "last_active",
            "playtime",
            "amount_spent",
            "created_at",
            "invalid_identifier",
            "sdk",
            "test_type",
            "ip",
            "external_user_id"
        ],
    )

   
    # verify we only returned data for our identity email
    one_signal_secrets = one_signal_connection_config.secrets

    assert v[f"{dataset_name}:device"][0]["identifier"] == one_signal_identity_email

@pytest.mark.integration_saas
@pytest.mark.integration_one_signal
@pytest.mark.asyncio
async def test_one_signal_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    one_signal_connection_config,
    one_signal_dataset_config,
    one_signal_erasure_identity_email,
    one_signal_create_erasure_data,
) -> None:
    """Full erasure request based on the one_signal SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_one_signal_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": one_signal_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = one_signal_connection_config.get_saas_config().fides_key
    merged_graph = one_signal_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [one_signal_connection_config],
        {"email": one_signal_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:device"],
        min_size=1,
        keys=[
            "id",
            "identifier",
            "session_count",
            "language",
            "timezone",
            "game_version",
            "device_os",
            "device_type",
            "device_model",
            "ad_id",
            "tags",
            "last_active",
            "playtime",
            "amount_spent",
            "created_at",
            "invalid_identifier",
            "sdk",
            "test_type",
            "ip",
            "external_user_id"
        ],
    )

   

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [one_signal_connection_config],
        {"email": one_signal_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:device": 1
    }

    one_signal_secrets = one_signal_connection_config.secrets
    base_url = f"https://{one_signal_secrets['domain']}"
    
    headers = {"Authorization": f"basic {one_signal_secrets['api_key']}"}


    # device
    response = requests.get(
        url=f"{base_url}/api/v1/players/{one_signal_secrets['player_id']}",
        headers=headers,
        params={"app_id": one_signal_secrets['app_id']},
    )
    device_response=response.json()
    #check data is updated or not
    assert device_response["tags"]["first_name"] == "MASKED"

    CONFIG.execution.masking_strict = masking_strict
