import logging
import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import CONFIG
from tests.ops.graph.graph_test_util import assert_rows_match

logger = logging.getLogger(__name__)


@pytest.mark.integration_saas
@pytest.mark.integration_braintree
def test_braintree_connection_test(
    braintree_connection_config,
) -> None:
    get_connector(braintree_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_braintree
@pytest.mark.asyncio
async def test_braintree_access_request_task(
    db,
    policy,
    braintree_connection_config,
    braintree_dataset_config,
    braintree_identity_email,
    connection_config,
    braintree_postgres_dataset_config,
    braintree_postgres_db,
) -> None:
    """Full access request based on the Braintree Conversations SaaS config"""
    privacy_request = PrivacyRequest(
        id=f"test_braintree_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = braintree_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = braintree_connection_config.get_saas_config().fides_key
    merged_graph = braintree_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, braintree_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
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


@pytest.mark.integration_saas
@pytest.mark.integration_braintree
@pytest.mark.asyncio
async def test_braintree_erasure_request_task(
    db,
    policy,
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

    privacy_request = PrivacyRequest(
        id=f"test_braintree_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = braintree_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = braintree_connection_config.get_saas_config().fides_key
    merged_graph = braintree_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, braintree_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
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

    x = await graph_task.run_erasure(
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
