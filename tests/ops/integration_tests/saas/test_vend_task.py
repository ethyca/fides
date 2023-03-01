import random

import pytest
import requests

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_vend
def test_vend_connection_test(vend_connection_config) -> None:
    get_connector(vend_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_vend
@pytest.mark.asyncio
async def test_vend_access_request_task(
    db,
    policy,
    vend_connection_config,
    vend_dataset_config,
    vend_identity_email,
) -> None:
    """Full access request based on the Vend SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_vend_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": vend_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = vend_connection_config.get_saas_config().fides_key
    merged_graph = vend_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [vend_connection_config],
        {"email": vend_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "name",
            "id",
            "customer_code",
            "source_unique_id",
            "first_name",
            "last_name",
            "email",
            "year_to_date",
            "balance",
            "loyalty_balance",
            "on_account_limit",
            "note",
            "gender",
            "date_of_birth",
            "company_name",
            "do_not_email",
            "loyalty_email_sent",
            "phone",
            "mobile",
            "fax",
            "twitter",
            "website",
            "physical_address_1",
            "physical_address_2",
            "physical_suburb",
            "physical_city",
            "physical_postcode",
            "physical_country_id",
            "postal_address_1",
            "postal_address_2",
            "postal_suburb",
            "postal_city",
            "postal_state",
            "postal_country_id",
            "customer_group_id",
            "enable_loyalty",
            "custom_field_1",
            "custom_field_2",
            "custom_field_3",
            "custom_field_4",
            "created_at",
            "updated_at",
            "deleted_at",
            "customer_group_ids",
            "version",
            "postal_postcode",
            "time_until_deletion",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:sales"],
        min_size=1,
        keys=[
            "id",
            "outlet_id",
            "register_id",
            "user_id",
            "customer_id",
            "invoice_number",
            "source",
            "source_id",
            "complete_open_sequence_id",
            "accounts_transaction_id",
            "has_unsynced_on_account_payments",
            "status",
            "note",
            "short_code",
            "return_for",
            "return_ids",
            "total_loyalty",
            "created_at",
            "updated_at",
            "sale_date",
            "deleted_at",
            "line_items",
            "payments",
            "adjustments",
            "external_applications",
            "version",
            "taxes",
            "total_price",
            "total_tax",
            "receipt_number",
            "total_price_incl",
        ],
    )

    # verify we only returned data for our identity email
    customer = v[f"{dataset_name}:customer"][0]
    assert customer["email"] == vend_identity_email
    customer_id = customer["id"]

    for sale in v[f"{dataset_name}:sales"]:
        assert sale["customer_id"] == customer_id


@pytest.mark.integration_saas
@pytest.mark.integration_vend
@pytest.mark.asyncio
async def test_vend_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    vend_connection_config,
    vend_dataset_config,
    vend_erasure_identity_email,
    vend_create_erasure_data,
) -> None:
    """Full erasure request based on the Vend SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_vend_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": vend_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = vend_connection_config.get_saas_config().fides_key
    merged_graph = vend_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [vend_connection_config],
        {"email": vend_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "name",
            "id",
            "customer_code",
            "source_unique_id",
            "first_name",
            "last_name",
            "email",
            "year_to_date",
            "balance",
            "loyalty_balance",
            "on_account_limit",
            "note",
            "gender",
            "date_of_birth",
            "company_name",
            "do_not_email",
            "loyalty_email_sent",
            "phone",
            "mobile",
            "fax",
            "twitter",
            "website",
            "physical_address_1",
            "physical_address_2",
            "physical_suburb",
            "physical_city",
            "physical_postcode",
            "physical_country_id",
            "postal_address_1",
            "postal_address_2",
            "postal_suburb",
            "postal_city",
            "postal_state",
            "postal_country_id",
            "customer_group_id",
            "enable_loyalty",
            "custom_field_1",
            "custom_field_2",
            "custom_field_3",
            "custom_field_4",
            "created_at",
            "updated_at",
            "deleted_at",
            "customer_group_ids",
            "version",
            "postal_postcode",
            "time_until_deletion",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:sales"],
        min_size=0,
        keys=[
            "id",
            "outlet_id",
            "register_id",
            "user_id",
            "customer_id",
            "invoice_number",
            "source",
            "source_id",
            "complete_open_sequence_id",
            "accounts_transaction_id",
            "has_unsynced_on_account_payments",
            "status",
            "note",
            "short_code",
            "return_for",
            "return_ids",
            "total_loyalty",
            "created_at",
            "updated_at",
            "sale_date",
            "deleted_at",
            "line_items",
            "payments",
            "adjustments",
            "external_applications",
            "version",
            "taxes",
            "total_price",
            "total_tax",
            "receipt_number",
            "total_price_incl",
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [vend_connection_config],
        {"email": vend_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {f"{dataset_name}:customer": 1, f"{dataset_name}:sales": 0}

    vend_secrets = vend_connection_config.secrets
    headers = {"Authorization": f"Bearer {vend_secrets['token']}"}
    base_url = f"https://{vend_secrets['domain']}"

    # customer
    response = requests.get(
        url=f"{base_url}/api/2.0/search",
        headers=headers,
        params={"type": "customers", "email": vend_erasure_identity_email},
    )
    customer = response.json()["data"][0]

    assert customer["name"] == "MASKED MASKED"
    assert customer["first_name"] == "MASKED"
    assert customer["last_name"] == "MASKED"
    assert customer["email"] == vend_erasure_identity_email

    CONFIG.execution.masking_strict = masking_strict
