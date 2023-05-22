import random

import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task import graph_task
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_kustomer
def test_kustomer_connection_test(kustomer_connection_config) -> None:
    get_connector(kustomer_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_kustomer
@pytest.mark.asyncio
async def test_kustomer_access_request_task_with_email(
    db,
    policy,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_identity_email,
) -> None:
    """Full access request based on the Kustomer SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_kustomer_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": kustomer_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [kustomer_connection_config],
        {"email": kustomer_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=["type", "id", "attributes", "relationships", "links"],
    )

    # verify we only returned data for our identity email
    assert (
        v[f"{dataset_name}:customer"][0]["attributes"]["emails"][0]["email"]
        == kustomer_identity_email
    )


@pytest.mark.integration_saas
@pytest.mark.integration_kustomer
@pytest.mark.asyncio
async def test_kustomer_access_request_task_with_phone_number(
    db,
    policy,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_identity_phone_number,
) -> None:
    """Full access request based on the Kustomer SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_kustomer_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"phone_number": kustomer_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [kustomer_connection_config],
        {"phone_number": kustomer_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=["type", "id", "attributes", "relationships", "links"],
    )

    # verify we only returned data for our identity phone number
    assert (
        v[f"{dataset_name}:customer"][0]["attributes"]["phones"][0]["phone"]
        == kustomer_identity_phone_number
    )


@pytest.mark.integration_saas
@pytest.mark.integration_kustomer
@pytest.mark.asyncio
async def test_kustomer_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_erasure_identity_email,
    kustomer_create_erasure_data,
) -> None:
    """Full erasure request based on the Kustomer SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_kustomer_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": kustomer_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [kustomer_connection_config],
        {"email": kustomer_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=["type", "id", "attributes", "relationships", "links"],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [kustomer_connection_config],
        {"email": kustomer_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {f"{dataset_name}:customer": 1}

    kustomer_secrets = kustomer_connection_config.secrets
    headers = {
        "Authorization": f"Bearer {kustomer_secrets['api_key']}",
    }
    base_url = f"https://{kustomer_secrets['domain']}"

    response = requests.get(
        url=f"{base_url}/v1/customers/email={kustomer_erasure_identity_email}",
        headers=headers,
    )

    assert response.status_code == 404

    CONFIG.execution.masking_strict = masking_strict
