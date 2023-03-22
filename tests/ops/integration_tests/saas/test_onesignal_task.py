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
@pytest.mark.integration_onesignal
def test_onesignal_connection_test(onesignal_connection_config) -> None:
    get_connector(onesignal_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_onesignal
@pytest.mark.asyncio
async def test_onesignal_access_request_task(
    db,
    policy,
    onesignal_connection_config,
    onesignal_dataset_config,
    onesignal_identity_email,
) -> None:
    """Full access request based on the onesignal SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_onesignal_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": onesignal_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = onesignal_connection_config.get_saas_config().fides_key
    merged_graph = onesignal_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [onesignal_connection_config],
        {"email": onesignal_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:devices"],
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
            "external_user_id",
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:devices"][0]["identifier"] == onesignal_identity_email

@pytest.mark.integration_saas
@pytest.mark.integration_onesignal
@pytest.mark.asyncio
async def test_onesignal_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    onesignal_connection_config,
    onesignal_dataset_config,
    onesignal_erasure_identity_email,
    onesignal_create_erasure_data,
) -> None:
    """Full erasure request based on the onesignal SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_onesignal_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": onesignal_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = onesignal_connection_config.get_saas_config().fides_key
    merged_graph = onesignal_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [onesignal_connection_config],
        {"email": onesignal_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:devices"],
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
            "external_user_id",
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [onesignal_connection_config],
        {"email": onesignal_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:devices": 1,
    }

    onesignal_secrets = onesignal_connection_config.secrets    
    base_url = f"https://{onesignal_secrets['domain']}"
    headers = {}

    # user
    response = requests.get(
        url=f"{base_url}/api/v1/players/"f"{onesignal_secrets['player_id']}",
        headers=headers,
        params={"app_id": f"{onesignal_secrets['app_id']}"},
    )
    device_response=response.json()
    #check data is updated or not
    # assert device_response["tags"]["first_name"] == "MASKED"

    CONFIG.execution.masking_strict = masking_strict