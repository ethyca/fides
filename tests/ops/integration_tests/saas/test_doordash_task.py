import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_doordash
def test_doordash_connection_test(doordash_connection_config) -> None:
    get_connector(doordash_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_doordash
@pytest.mark.asyncio
async def test_doordash_access_request_task(
    db,
    policy,
    doordash_connection_config,
    doordash_dataset_config,
    doordash_identity_email,
    connection_config,
    doordash_postgres_dataset_config,
    doordash_postgres_db,
) -> None:
    """Full access request based on the Doordash SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_doordash_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = doordash_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = doordash_connection_config.get_saas_config().fides_key
    merged_graph = doordash_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, doordash_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [doordash_connection_config, connection_config],
        {"email": doordash_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:deliveries"],
        min_size=1,
        keys=[
            "external_delivery_id",
            "currency",
            "delivery_status",
            "fee",
            "pickup_address",
            "pickup_phone_number",
            "pickup_instructions",
            "pickup_reference_tag",
            "dropoff_address",
            "dropoff_business_name",
            "dropoff_phone_number",
            "dropoff_instructions",
            "dropoff_contact_given_name",
            "dropoff_contact_family_name",
            "dropoff_contact_send_notifications",
            "order_value",
            "cancellation_reason",
            "updated_at",
            "pickup_time_estimated",
            "dropoff_time_estimated",
            "support_reference",
            "tracking_url",
            "contactless_dropoff",
            "action_if_undeliverable",
            "tip",
            "order_contains",
        ],
    )
