import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from tests.conftest import access_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.cache_secrets_helper import clear_cache_identities


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_datadog_connection_test(datadog_connection_config) -> None:
    get_connector(datadog_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_datadog_access_request_task_with_email(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    datadog_connection_config,
    datadog_dataset_config,
    datadog_identity_email,
    datadog_access_data,
) -> None:
    """Full access request based on the Datadog SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_attribute = "email"
    identity_value = datadog_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = datadog_connection_config.get_saas_config().fides_key
    merged_graph = datadog_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [datadog_connection_config],
        {"email": datadog_identity_email},
        db,
    )
    key = f"{dataset_name}:events"

    assert_rows_match(
        v[key],
        min_size=1,
        keys=[
            "attributes",
            "type",
            "id",
        ],
    )

    for item in v[key]:
        assert_rows_match(
            [item["attributes"]],
            min_size=1,
            keys=[
                "status",
                "timestamp",
                "message",
                "tags",
            ],
        )

    for item in v[key]:
        assert datadog_identity_email in item["attributes"]["message"]


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_datadog_access_request_task_with_phone_number(
    db,
    dsr_version,
    request,
    policy,
    privacy_request,
    datadog_connection_config,
    datadog_dataset_config,
    datadog_identity_phone_number,
    datadog_access_data,
) -> None:
    """Full access request based on the Datadog SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    clear_cache_identities(privacy_request.id)

    identity_attribute = "phone_number"
    identity_value = datadog_identity_phone_number
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = datadog_connection_config.get_saas_config().fides_key
    merged_graph = datadog_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [datadog_connection_config],
        {"phone_number": datadog_identity_phone_number},
        db,
    )
    key = f"{dataset_name}:events"

    assert_rows_match(
        v[key],
        min_size=1,
        keys=[
            "attributes",
            "type",
            "id",
        ],
    )

    for item in v[key]:
        assert_rows_match(
            [item["attributes"]],
            min_size=1,
            keys=[
                "status",
                "timestamp",
                "message",
                "tags",
            ],
        )

    for item in v[key]:
        assert datadog_identity_phone_number in item["attributes"]["message"]
