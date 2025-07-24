from typing import Any, Dict, List
from unittest import mock

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import TraversalError
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.task.graph_runners import access_runner, erasure_runner
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.api.util.collection_util import Row
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match


def erasure_execution_logs(
    db: Session, privacy_request: PrivacyRequest
) -> List[ExecutionLog]:
    """Returns the erasure execution logs for the given privacy request ordered by created_at"""
    return (
        db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request.id, action_type=ActionType.erasure
        )
        .order_by("created_at")
        .all()
    )


# custom override functions to facilitate testing
@register("read_no_op", [SaaSRequestType.READ])
def read_no_op(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    return [{f"{node.address.collection}_id": 1}]


@register("delete_no_op", [SaaSRequestType.DELETE])
def delete_no_op(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    return 1


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.usefixtures("use_dsr_2_0")
async def test_saas_erasure_order_request_task(
    db,
    policy,
    privacy_request,
    erasure_policy_complete_mask,
    saas_erasure_order_connection_config,
    saas_erasure_order_dataset_config,
) -> None:
    """This test uses DSR 2.0 specifically. Equivalent concept for DSR 3.0 tested
    in test_create_request_tasks.py"""
    privacy_request.policy_id = erasure_policy_complete_mask.id
    privacy_request.save(db)

    identity_attribute = "email"
    identity_value = "test@ethyca.com"
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = saas_erasure_order_connection_config.get_saas_config().fides_key
    merged_graph = saas_erasure_order_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner(
        privacy_request,
        erasure_policy_complete_mask,
        graph,
        [saas_erasure_order_connection_config],
        {"email": "test@ethyca.com"},
        db,
    )

    assert_rows_match(v[f"{dataset_name}:orders"], min_size=1, keys=["orders_id"])
    assert_rows_match(v[f"{dataset_name}:refunds"], min_size=1, keys=["refunds_id"])
    assert_rows_match(v[f"{dataset_name}:labels"], min_size=1, keys=["labels_id"])
    assert_rows_match(v[f"{dataset_name}:products"], min_size=1, keys=["products_id"])
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

    x = erasure_runner(
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
        f"{dataset_name}:products": 0,
        f"{dataset_name}:orders_to_refunds": 1,
        f"{dataset_name}:refunds_to_orders": 1,
    }

    # Retrieve the erasure logs ordered by `created_at` and verify that the erasures started and ended in the expected order (no overlaps)
    assert [
        (log.collection_name, log.status.value)
        for log in erasure_execution_logs(db, privacy_request)
    ] == [
        ("products", "in_processing"),
        ("products", "complete"),
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


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.usefixtures("use_dsr_2_0")
async def test_saas_erasure_order_request_task_with_cycle(
    db,
    privacy_request,
    erasure_policy_complete_mask,
    saas_erasure_order_config,
    saas_erasure_order_connection_config,
    saas_erasure_order_dataset_config,
) -> None:
    """This test uses DSR 2.0 specifically. Equivalent concept for DSR 3.0 tested
    in test_create_request_tasks.py"""
    privacy_request.policy_id = erasure_policy_complete_mask.id
    privacy_request.save(db)

    identity_attribute = "email"
    identity_value = "test@ethyca.com"
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    # add a dependency on labels to be erased before orders to create a non-traversable cycle
    # this won't affect the access traversal
    dataset_name = saas_erasure_order_connection_config.get_saas_config().fides_key
    saas_erasure_order_config["endpoints"][0]["erase_after"].append(
        f"{dataset_name}.labels"
    )
    saas_erasure_order_connection_config.update(
        db, data={"saas_config": saas_erasure_order_config}
    )
    merged_graph = saas_erasure_order_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner(
        privacy_request,
        erasure_policy_complete_mask,
        graph,
        [saas_erasure_order_connection_config],
        {"email": "test@ethyca.com"},
        db,
    )

    assert_rows_match(v[f"{dataset_name}:orders"], min_size=1, keys=["orders_id"])
    assert_rows_match(v[f"{dataset_name}:refunds"], min_size=1, keys=["refunds_id"])
    assert_rows_match(v[f"{dataset_name}:labels"], min_size=1, keys=["labels_id"])
    assert_rows_match(v[f"{dataset_name}:products"], min_size=1, keys=["products_id"])
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

    with pytest.raises(TraversalError) as exc:
        erasure_runner(
            privacy_request,
            erasure_policy_complete_mask,
            graph,
            [saas_erasure_order_connection_config],
            identity_kwargs,
            get_cached_data_for_erasures(privacy_request.id),
            db,
        )

    assert (
        f"The values for the `erase_after` fields caused a cycle in the following collections"
        in str(exc.value)
    )


@pytest.mark.integration_saas
@pytest.mark.asyncio
@mock.patch("fides.api.service.connectors.saas_connector.SaaSConnector.mask_data")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_saas_erasure_order_request_task_resume_from_error(
    mock_mask_data,
    db,
    policy,
    erasure_policy_complete_mask,
    saas_erasure_order_connection_config,
    saas_erasure_order_dataset_config,
    privacy_request,
    dsr_version,
    request,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # Policy needs to actually be set correctly on the privacy request for 3.0 testing
    privacy_request.policy_id = erasure_policy_complete_mask.id
    privacy_request.save(db)

    identity_attribute = "email"
    identity_value = "test@ethyca.com"
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = saas_erasure_order_connection_config.get_saas_config().fides_key
    merged_graph = saas_erasure_order_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_complete_mask,  # If we are doing an erasure request next, this needs to be accurate for DSR 3.0
        graph,
        [saas_erasure_order_connection_config],
        {"email": "test@ethyca.com"},
        db,
    )

    assert_rows_match(v[f"{dataset_name}:orders"], min_size=1, keys=["orders_id"])
    assert_rows_match(v[f"{dataset_name}:refunds"], min_size=1, keys=["refunds_id"])
    assert_rows_match(v[f"{dataset_name}:labels"], min_size=1, keys=["labels_id"])
    assert_rows_match(v[f"{dataset_name}:products"], min_size=1, keys=["products_id"])
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

    # mock the mask_data function so we can force an exception on the "refunds_to_orders"
    # collection to simulate resuming from error
    def side_effect(node, policy, privacy_request, request_task, rows):
        if node.address.collection == "refunds_to_orders":
            raise Exception("Error executing refunds_to_orders task")
        request_task.rows_masked = 1
        if request_task.id:
            # DSR 3.0 needs to save this to the request task
            session = Session.object_session(request_task)
            request_task.save(session)
        return 1

    mock_mask_data.side_effect = side_effect

    if dsr_version == "use_dsr_2_0":
        with pytest.raises(Exception):
            erasure_runner_tester(
                privacy_request,
                erasure_policy_complete_mask,
                graph,
                [saas_erasure_order_connection_config],
                identity_kwargs,
                get_cached_data_for_erasures(privacy_request.id),
                db,
            )
    else:
        erasure_runner_tester(
            privacy_request,
            erasure_policy_complete_mask,
            graph,
            [saas_erasure_order_connection_config],
            identity_kwargs,
            get_cached_data_for_erasures(privacy_request.id),
            db,
        )

    # "fix" the refunds_to_orders collection and resume the erasure
    def side_effect(node, policy, privacy_request, request_task, rows):
        request_task.rows_masked = 1
        if request_task.id:
            session = Session.object_session(request_task)
            request_task.save(session)
        return 1

    mock_mask_data.side_effect = side_effect

    x = erasure_runner_tester(
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
        f"{dataset_name}:products": 0,
        f"{dataset_name}:orders_to_refunds": 1,
        f"{dataset_name}:refunds_to_orders": 1,
    }

    if dsr_version == "use_dsr_2_0":
        assert [
            (log.collection_name, log.status.value)
            for log in erasure_execution_logs(db, privacy_request)
        ] == [
            ("products", "in_processing"),
            ("products", "complete"),
            ("orders_to_refunds", "in_processing"),
            ("orders_to_refunds", "complete"),
            ("refunds_to_orders", "in_processing"),
            ("refunds_to_orders", "error"),
            ("refunds_to_orders", "in_processing"),
            ("refunds_to_orders", "complete"),
            ("orders", "in_processing"),
            ("orders", "complete"),
            ("refunds", "in_processing"),
            ("refunds", "complete"),
            ("labels", "in_processing"),
            ("labels", "complete"),
        ], "Cached collections were not re-executed after resuming the privacy request from errored state"
    else:
        ordered_logs = [
            (el.collection_name, el.status.value)
            for el in db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id == privacy_request.id,
                ExecutionLog.action_type == ActionType.erasure,
            )
            .order_by(ExecutionLog.collection_name, ExecutionLog.created_at)
            .all()
        ]
        assert ordered_logs == [
            ("labels", "in_processing"),
            ("labels", "complete"),
            ("orders", "in_processing"),
            ("orders", "complete"),
            ("orders_to_refunds", "in_processing"),
            ("orders_to_refunds", "complete"),
            ("products", "in_processing"),
            ("products", "complete"),
            ("refunds", "in_processing"),
            ("refunds", "complete"),
            ("refunds_to_orders", "in_processing"),
            ("refunds_to_orders", "error"),
            ("refunds_to_orders", "in_processing"),
            ("refunds_to_orders", "complete"),
        ]
