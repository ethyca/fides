import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_shippo
def test_shippo_connection_test(shippo_connection_config) -> None:
    get_connector(shippo_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_shippo
@pytest.mark.asyncio
async def test_shippo_access_request_task(
    db,
    policy,
    shippo_connection_config,
    shippo_dataset_config,
    shippo_identity_email,
) -> None:
    """Full access request based on the Shippo SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_shippo_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": shippo_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = shippo_connection_config.get_saas_config().fides_key
    merged_graph = shippo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [shippo_connection_config],
        {"email": shippo_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:addresses"],
        min_size=1,
        keys=[
            "object_created",
            "object_updated",
            "object_id",
            "is_complete",
            "validation_results",
            "object_owner",
            "name",
            "company",
            "street_no",
            "street1",
            "street2",
            "street3",
            "city",
            "state",
            "zip",
            "country",
            "longitude",
            "latitude",
            "phone",
            "email",
            "is_residential",
            "metadata",
            "test",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:orders"],
        min_size=1,
        keys=[
            "object_id",
            "order_number",
            "order_status",
            "placed_at",
            "object_owner",
            "to_address",
            "from_address",
            "shop_app",
            "weight",
            "weight_unit",
            "transactions",
            "total_tax",
            "total_price",
            "subtotal_price",
            "currency",
            "shipping_method",
            "shipping_cost",
            "shipping_cost_currency",
            "line_items",
            "notes",
            "test",
        ],
    )

    # verify we only returned data for our identity email

    for address in v[f"{dataset_name}:addresses"]:
        assert address["email"] == shippo_identity_email

    for order in v[f"{dataset_name}:orders"]:
        assert order["object_owner"] == shippo_identity_email
