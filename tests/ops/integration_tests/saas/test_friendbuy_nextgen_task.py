import logging
from time import sleep

import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_friendbuy_nextgen_connection_test(
    friendbuy_nextgen_connection_config,
) -> None:
    get_connector(friendbuy_nextgen_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_friendbuy_nextgen_access_request_task(
    db,
    dsr_version,
    request,
    policy,
    privacy_request,
    friendbuy_nextgen_connection_config,
    friendbuy_nextgen_dataset_config,
    friendbuy_nextgen_identity_email,
    connection_config,
) -> None:
    """Full access request based on the Friendbuy Nextgen Conversations SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_attribute = "email"
    identity_value = friendbuy_nextgen_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = friendbuy_nextgen_connection_config.get_saas_config().fides_key
    merged_graph = friendbuy_nextgen_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [friendbuy_nextgen_connection_config, connection_config],
        {"email": friendbuy_nextgen_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "emails",
            "names",
            "customerIds",
            "ipAddresses",
            "languages",
            "userAgents",
            "colorDepths",
            "platforms",
            "screenSizes",
            "trackedEvents",
            "shares",
            "conversions",
        ],
    )


@pytest.mark.skip(reason="Temporarily disabled test")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_friendbuy_nextgen_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    friendbuy_nextgen_connection_config,
    friendbuy_nextgen_dataset_config,
    connection_config,
    erasure_policy_string_rewrite,
    friendbuy_nextgen_erasure_identity_email,
    friendbuy_nextgen_erasure_data,
) -> None:
    """Full erasure request based on the Friendbuy Nextgen SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity_attribute = "email"
    identity_value = friendbuy_nextgen_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = friendbuy_nextgen_connection_config.get_saas_config().fides_key
    merged_graph = friendbuy_nextgen_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    # Adding 30 seconds sleep because sometimes Friendbuy Nextgen system takes around 30 seconds for user to be available

    sleep(30)
    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [friendbuy_nextgen_connection_config, connection_config],
        {"email": friendbuy_nextgen_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "emails",
            "names",
            "customerIds",
            "ipAddresses",
            "languages",
            "userAgents",
            "colorDepths",
            "platforms",
            "screenSizes",
            "trackedEvents",
            "shares",
            "conversions",
        ],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [friendbuy_nextgen_connection_config],
        {"email": friendbuy_nextgen_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Verify masking request was issued for endpoints with delete actions
    assert x == {
        "friendbuy_nextgen_instance:user": 1,
    }

    CONFIG.execution.masking_strict = temp_masking
