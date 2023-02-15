import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.asyncio
async def test_saas_erasure_order_request_task(
    db,
    policy,
    erasure_policy_complete_mask,
    saas_erasure_order_connection_config,
    saas_erasure_order_dataset_config,
) -> None:
    privacy_request = PrivacyRequest(
        id=f"test_saas_erasure_order_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = "test@ethyca.com"
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = saas_erasure_order_connection_config.get_saas_config().fides_key
    merged_graph = saas_erasure_order_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [saas_erasure_order_connection_config],
        {"email": "test@ethyca.com"},
        db,
    )

    assert_rows_match(v[f"{dataset_name}:orders"], min_size=1, keys=["orders_id"])
    assert_rows_match(v[f"{dataset_name}:refunds"], min_size=1, keys=["refunds_id"])
    assert_rows_match(v[f"{dataset_name}:labels"], min_size=1, keys=["labels_id"])
    assert_rows_match(
        v[f"{dataset_name}:orders_to_refunds"],
        min_size=1,
        keys=["orders_to_refunds_id"],
    )
    assert_rows_match(
        v[f"{dataset_name}:refunds_to_orders"],
        min_size=1,
        keys=["refunds_to_orders_id"],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_complete_mask,
        graph,
        [saas_erasure_order_connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:orders": 1,
        f"{dataset_name}:refunds": 1,
        f"{dataset_name}:labels": 1,
        f"{dataset_name}:orders_to_refunds": 1,
        f"{dataset_name}:refunds_to_orders": 1,
    }

    # Retrieve the erasure logs ordered by `created_at` and verify that the erasures started and ended in the expected order (no overlaps)
    execution_logs = (
        db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request.id, action_type=ActionType.erasure
        )
        .order_by("created_at")
    )

    assert [(log.collection_name, log.status.value) for log in execution_logs] == [
        ("orders_to_refunds", "in_processing"),
        ("orders_to_refunds", "complete"),
        ("refunds_to_orders", "in_processing"),
        ("refunds_to_orders", "complete"),
        ("orders", "in_processing"),
        ("orders", "complete"),
        ("refunds", "in_processing"),
        ("refunds", "complete"),
        ("labels", "in_processing"),
        ("labels", "complete"),
    ]

    CONFIG.execution.masking_strict = temp_masking
