import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import get_config
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.cache_secrets_helper import clear_cache_identities

CONFIG = get_config()

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_kustomer_connection_test(kustomer_connection_config) -> None:
    get_connector(kustomer_connection_config).test_connection()

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_kustomer_access_request_task_with_email(
    db,
    policy,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_identity_email,
    privacy_request,
    request,
    dsr_version,
) -> None:
    """Full access request based on the Kustomer SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": kustomer_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
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

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_kustomer_access_request_task_with_non_existent_email(
    db,
    policy,
    kustomer_connection_config,
    kustomer_dataset_config,
    privacy_request,
    dsr_version,
    request,
    kustomer_non_existent_identity_email,
) -> None:
    """Access request that returns a 404 but succeeds"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": kustomer_non_existent_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [kustomer_connection_config],
        {"email": kustomer_non_existent_identity_email},
        db,
    )

    # verify the request succeeded but no information was returned
    assert len(v[f"{dataset_name}:customer"]) == 0

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_kustomer_access_request_task_with_phone_number(
    db,
    policy,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_identity_phone_number,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full access request based on the Kustomer SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    clear_cache_identities(privacy_request.id)

    identity = Identity(**{"phone_number": kustomer_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
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

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_kustomer_erasure_request_task(
    db,
    erasure_policy_string_rewrite,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_erasure_identity_email,
    kustomer_create_erasure_data,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full erasure request based on the Kustomer SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    identity = Identity(**{"email": kustomer_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
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

    x = erasure_runner_tester(
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

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_kustomer_erasure_request_task_non_existent_email(
    db,
    privacy_request,
    erasure_policy_string_rewrite,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_non_existent_identity_email,
    kustomer_create_erasure_data,
    dsr_version,
    request,
) -> None:
    """Full erasure request based on the Kustomer SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity = Identity(**{"email": kustomer_non_existent_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [kustomer_connection_config],
        {"email": kustomer_non_existent_identity_email},
        db,
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [kustomer_connection_config],
        {"email": kustomer_non_existent_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {f"{dataset_name}:customer": 0}

    CONFIG.execution.masking_strict = masking_strict
