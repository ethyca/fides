import logging

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
def test_braintree_connection_test(
    braintree_connection_config,
) -> None:
    get_connector(braintree_connection_config).test_connection()

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_braintree_access_request_task(
    db,
    policy,
    dsr_version,
    request,
    braintree_connection_config,
    braintree_dataset_config,
    braintree_identity_email,
    connection_config,
    privacy_request,
    braintree_postgres_dataset_config,
    braintree_postgres_db,
) -> None:
    """Full access request based on the Braintree Conversations SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_attribute = "email"
    identity_value = braintree_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = braintree_connection_config.get_saas_config().fides_key
    merged_graph = braintree_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, braintree_postgres_dataset_config.get_graph()])

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [braintree_connection_config, connection_config],
        {"email": braintree_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=["id", "legacyId", "firstName", "lastName", "company", "createdAt"],
    )

    assert_rows_match(
        v[f"{dataset_name}:transactions"],
        min_size=1,
        keys=[
            "id",
            "legacyId",
            "amount",
            "paymentMethodSnapshot",
            "orderId",
            "status",
            "source",
            "createdAt",
        ],
    )

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_braintree_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    braintree_connection_config,
    braintree_dataset_config,
    connection_config,
    braintree_postgres_dataset_config,
    erasure_policy_string_rewrite,
    braintree_erasure_identity_email,
    braintree_erasure_data,
    braintree_postgres_erasure_db,
) -> None:
    """Full erasure request based on the Braintree SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity_attribute = "email"
    identity_value = braintree_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = braintree_connection_config.get_saas_config().fides_key
    merged_graph = braintree_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, braintree_postgres_dataset_config.get_graph()])

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [braintree_connection_config, connection_config],
        {"email": braintree_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=["id", "legacyId", "firstName", "lastName", "company", "createdAt"],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [braintree_connection_config, connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Verify masking request was issued for endpoints with update actions
    assert x == {
        "braintree_instance:customer": 1,
        "braintree_postgres:braintree_customers": 0,
        "braintree_instance:transactions": 0,
    }

    CONFIG.execution.masking_strict = temp_masking
