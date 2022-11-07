import logging
import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from tests.ops.graph.graph_test_util import assert_rows_match

logger = logging.getLogger(__name__)


@pytest.mark.integration_saas
@pytest.mark.integration_recharge
def test_recharge_connection_test(recharge_connection_config) -> None:
    get_connector(recharge_connection_config).test_connection()


@pytest.mark.integration_recharge
@pytest.mark.asyncio
async def test_recharge_access_request_task(
    db,
    policy,
    recharge_connection_config,
    recharge_dataset_config,
    recharge_identity_email,
) -> None:
    """Full access request based on the recharge SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_recharge_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = recharge_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = recharge_connection_config.get_saas_config().fides_key
    merged_graph = recharge_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [recharge_connection_config],
        {"email": recharge_identity_email},
        db,
    )

    key = f'{dataset_name}:customers'
    assert_rows_match(
        v[key],
        min_size=1,
        keys=[
            "accepts_marketing",
            "billing_address1",
            "billing_address2",
            "billing_city",
            "billing_company",
            "billing_country",
            "billing_phone",
            "billing_province",
            "billing_zip",
            "created_at",
            "email",
            "first_charge_processed_at",
            "first_name",
            "has_card_error_in_dunning",
            "has_valid_payment_method",
            "hash",
            "id",
            "last_name",
            "number_active_subscriptions",
            "number_subscriptions",
            "phone",
            "processor_type",
            "reason_payment_method_not_valid",
            "shopify_customer_id",
            "status",
            "tax_exempt",
            "updated_at",
        ]
    )
    for item in v[key]:
        assert item['email'] == recharge_identity_email

    customer_id = v[key][0]['id']

    key = f'{dataset_name}:addresses'
    assert_rows_match(
        v[key],
        min_size=1,
        keys=[
            "address1",
            "address2",
            "cart_attributes",
            "cart_note",
            "city",
            "company",
            "country",
            "created_at",
            "customer_id",
            "discount_id",
            "first_name",
            "id",
            "last_name",
            "note_attributes",
            "original_shipping_lines",
            "phone",
            "presentment_currency",
            "province",
            "shipping_lines_override",
            "updated_at",
            "zip",
        ]
    )

    for item in v[key]:
        assert item['customer_id'] == customer_id
