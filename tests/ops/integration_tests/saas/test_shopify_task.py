from time import sleep

import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_shopify_connection_test(shopify_connection_config) -> None:
    get_connector(shopify_connection_config).test_connection()

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_shopify_access_request_task(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    shopify_connection_config,
    shopify_dataset_config,
    shopify_identity_email,
    # shopify_access_data,
) -> None:
    """Full access request based on the Shopify SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": shopify_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = shopify_connection_config.get_saas_config().fides_key
    merged_graph = shopify_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [shopify_connection_config],
        {"email": shopify_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customers"],
        min_size=1,
        keys=[
            "id",
            "email",
            "accepts_marketing",
            "created_at",
            "updated_at",
            "first_name",
            "last_name",
            "orders_count",
            "state",
            "total_spent",
            "last_order_id",
            "note",
            "verified_email",
            "multipass_identifier",
            "tax_exempt",
            "tags",
            "last_order_name",
            "currency",
            "phone",
            "accepts_marketing_updated_at",
            "marketing_opt_in_level",
            "tax_exemptions",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_orders"],
        min_size=1,
        keys=[
            "id",
            "admin_graphql_api_id",
            "app_id",
            "browser_ip",
            "buyer_accepts_marketing",
            "cancel_reason",
            "cancelled_at",
            "cart_token",
            "checkout_id",
            "checkout_token",
            "closed_at",
            "confirmed",
            "contact_email",
            "created_at",
            "currency",
            "current_subtotal_price",
            "current_total_discounts",
            "current_total_price",
            "current_total_tax",
            "customer_locale",
            "device_id",
            "discount_codes",
            "email",
            "estimated_taxes",
            "financial_status",
            "fulfillment_status",
            "landing_site",
            "landing_site_ref",
            "location_id",
            "name",
            "note",
            "note_attributes",
            "number",
            "order_number",
            "order_status_url",
            "payment_gateway_names",
            "phone",
            "presentment_currency",
            "processed_at",
            "reference",
            "referring_site",
            "source_identifier",
            "source_name",
            "source_url",
            "subtotal_price",
            "tags",
            "tax_lines",
            "taxes_included",
            "test",
            "token",
            "total_discounts",
            "total_line_items_price",
            "total_outstanding",
            "total_price",
            "total_tax",
            "total_tip_received",
            "total_weight",
            "updated_at",
            "user_id",
            "customer",
            "discount_applications",
            "payment_terms",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_addresses"],
        min_size=1,
        keys=[
            "id",
            "customer_id",
            "first_name",
            "last_name",
            "company",
            "address1",
            "address2",
            "city",
            "province",
            "country",
            "zip",
            "phone",
            "name",
            "province_code",
            "country_code",
            "country_name",
            "default",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_order_transactions"],
        min_size=1,
        keys=[
            "id",
            "order_id",
            "kind",
            "gateway",
            "status",
            "message",
            "created_at",
            "test",
            "authorization",
            "location_id",
            "user_id",
            "parent_id",
            "processed_at",
            "device_id",
            "error_code",
            "source_name",
            "amount",
            "currency",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blogs"],
        min_size=1,
        keys=[
            "id",
            "handle",
            "title",
            "updated_at",
            "commentable",
            "feedburner",
            "feedburner_location",
            "created_at",
            "template_suffix",
            "tags",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blog_articles"],
        min_size=1,
        keys=[
            "id",
            "title",
            "created_at",
            "body_html",
            "blog_id",
            "author",
            "user_id",
            "published_at",
            "updated_at",
            "summary_html",
            "template_suffix",
            "handle",
            "tags",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blog_article_comments"],
        min_size=1,
        keys=[
            "id",
            "body",
            "body_html",
            "author",
            "email",
            "status",
            "article_id",
            "blog_id",
            "created_at",
            "updated_at",
            "ip",
            "user_agent",
            "published_at",
        ],
    )

    for comment in v[f"{dataset_name}:blog_article_comments"]:
        assert comment["email"] == shopify_identity_email

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_shopify_erasure_request_task(
    db,
    privacy_request,
    erasure_policy_string_rewrite,
    shopify_connection_config,
    shopify_dataset_config,
    shopify_erasure_identity_email,
    dsr_version,
    request,
    shopify_erasure_data,
) -> None:
    """Full erasure request based on the Shopify SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity = Identity(**{"email": shopify_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = shopify_connection_config.get_saas_config().fides_key
    merged_graph = shopify_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [shopify_connection_config],
        {"email": shopify_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customers"],
        min_size=1,
        keys=[
            "id",
            "email",
            "accepts_marketing",
            "created_at",
            "updated_at",
            "first_name",
            "last_name",
            "orders_count",
            "state",
            "total_spent",
            "last_order_id",
            "note",
            "verified_email",
            "multipass_identifier",
            "tax_exempt",
            "tags",
            "last_order_name",
            "currency",
            "phone",
            "accepts_marketing_updated_at",
            "marketing_opt_in_level",
            "tax_exemptions",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_orders"],
        min_size=1,
        keys=[
            "id",
            "admin_graphql_api_id",
            "app_id",
            "browser_ip",
            "buyer_accepts_marketing",
            "cancel_reason",
            "cancelled_at",
            "cart_token",
            "checkout_id",
            "checkout_token",
            "closed_at",
            "confirmed",
            "contact_email",
            "created_at",
            "currency",
            "current_subtotal_price",
            "current_total_discounts",
            "current_total_price",
            "current_total_tax",
            "customer_locale",
            "device_id",
            "discount_codes",
            "email",
            "estimated_taxes",
            "financial_status",
            "fulfillment_status",
            "landing_site",
            "landing_site_ref",
            "location_id",
            "name",
            "note",
            "note_attributes",
            "number",
            "order_number",
            "order_status_url",
            "payment_gateway_names",
            "phone",
            "presentment_currency",
            "processed_at",
            "reference",
            "referring_site",
            "source_identifier",
            "source_name",
            "source_url",
            "subtotal_price",
            "tags",
            "tax_lines",
            "taxes_included",
            "test",
            "token",
            "total_discounts",
            "total_line_items_price",
            "total_outstanding",
            "total_price",
            "total_tax",
            "total_tip_received",
            "total_weight",
            "updated_at",
            "user_id",
            "customer",
            "discount_applications",
            "payment_terms",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_addresses"],
        min_size=1,
        keys=[
            "id",
            "customer_id",
            "first_name",
            "last_name",
            "company",
            "address1",
            "address2",
            "city",
            "province",
            "country",
            "zip",
            "phone",
            "name",
            "province_code",
            "country_code",
            "country_name",
            "default",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blogs"],
        min_size=1,
        keys=[
            "id",
            "handle",
            "title",
            "updated_at",
            "commentable",
            "feedburner",
            "feedburner_location",
            "created_at",
            "template_suffix",
            "tags",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blog_articles"],
        min_size=1,
        keys=[
            "id",
            "title",
            "created_at",
            "body_html",
            "blog_id",
            "author",
            "user_id",
            "published_at",
            "updated_at",
            "summary_html",
            "template_suffix",
            "handle",
            "tags",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blog_article_comments"],
        min_size=1,
        keys=[
            "id",
            "body",
            "body_html",
            "author",
            "email",
            "status",
            "article_id",
            "blog_id",
            "created_at",
            "updated_at",
            "ip",
            "user_agent",
            "published_at",
        ],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [shopify_connection_config],
        {"email": shopify_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:customers": 1,
        f"{dataset_name}:blogs": 0,
        f"{dataset_name}:customer_orders": 1,
        f"{dataset_name}:customer_addresses": 2,
        f"{dataset_name}:blog_articles": 0,
        f"{dataset_name}:blog_article_comments": 1,
        f"{dataset_name}:customer_order_transactions": 0,
    }

    sleep(30)  # wait for the data to settle on Shopify's side

    # Verifying data is actually updated
    shopify_secrets = shopify_connection_config.secrets
    base_url = f"https://{shopify_secrets['domain']}"
    headers = {"X-Shopify-Access-Token": f"{shopify_secrets['access_token']}"}
    customer_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/customers.json?email={shopify_erasure_identity_email}",
        headers=headers,
    )
    customer = customer_response.json()["customers"][0]
    customer_id = customer["id"]
    assert customer["first_name"] == "MASKED"
    assert customer["last_name"] == "MASKED"
    assert customer["default_address"]["first_name"] == "MASKED"
    assert customer["default_address"]["last_name"] == "MASKED"
    assert customer["default_address"]["name"] == "MASKED MASKED"

    customer_order_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/customers/{customer_id}/orders.json?status=any",
        headers=headers,
    )

    order = customer_order_response.json()["orders"][0]
    assert order["customer"]["first_name"] == "MASKED"
    assert order["customer"]["last_name"] == "MASKED"
    assert order["customer"]["default_address"]["first_name"] == "MASKED"
    assert order["customer"]["default_address"]["last_name"] == "MASKED"
    assert order["customer"]["default_address"]["name"] == "MASKED MASKED"

    customer_address_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/customers/{customer_id}/addresses.json",
        headers=headers,
    )

    address = customer_address_response.json()["addresses"][0]
    assert address["first_name"] == "MASKED"
    assert address["last_name"] == "MASKED"
    assert address["name"] == "MASKED MASKED"

    # Please note that Shopify doesn't allow comments filtering by email so we are getting comment_id by dataset instead and verifying that it is masked
    comment_id = v[f"{dataset_name}:blog_article_comments"][0]["id"]
    blog_article_comment_response = requests.get(
        url=f"{base_url}/admin/api/2022-07/comments/{comment_id}.json",
        headers=headers,
    )
    comment = blog_article_comment_response.json()["comment"]
    assert comment["author"] == "MASKED"

    CONFIG.execution.masking_strict = temp_masking

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_shopify_erasure_accepts_masking_task(
    db,
    privacy_request,
    erasure_policy_complete_mask,
    shopify_connection_config,
    shopify_dataset_config,
    shopify_erasure_identity_email,
    dsr_version,
    request,
    shopify_erasure_data,
) -> None:
    """
    Checks that all the values that can be masked on a Full erasure request
    can be accepted by the Shopify API

    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_complete_mask.id
    privacy_request.save(db)

    identity = Identity(**{"email": shopify_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = shopify_connection_config.get_saas_config().fides_key
    merged_graph = shopify_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_complete_mask,
        graph,
        [shopify_connection_config],
        {"email": shopify_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customers"],
        min_size=1,
        keys=[
            "id",
            "email",
            "accepts_marketing",
            "created_at",
            "updated_at",
            "first_name",
            "last_name",
            "orders_count",
            "state",
            "total_spent",
            "last_order_id",
            "note",
            "verified_email",
            "multipass_identifier",
            "tax_exempt",
            "tags",
            "last_order_name",
            "currency",
            "phone",
            "accepts_marketing_updated_at",
            "marketing_opt_in_level",
            "tax_exemptions",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_orders"],
        min_size=1,
        keys=[
            "id",
            "admin_graphql_api_id",
            "app_id",
            "browser_ip",
            "buyer_accepts_marketing",
            "cancel_reason",
            "cancelled_at",
            "cart_token",
            "checkout_id",
            "checkout_token",
            "closed_at",
            "confirmed",
            "contact_email",
            "created_at",
            "currency",
            "current_subtotal_price",
            "current_total_discounts",
            "current_total_price",
            "current_total_tax",
            "customer_locale",
            "device_id",
            "discount_codes",
            "email",
            "estimated_taxes",
            "financial_status",
            "fulfillment_status",
            "landing_site",
            "landing_site_ref",
            "location_id",
            "name",
            "note",
            "note_attributes",
            "number",
            "order_number",
            "order_status_url",
            "payment_gateway_names",
            "phone",
            "presentment_currency",
            "processed_at",
            "reference",
            "referring_site",
            "shipping_address",
            "source_identifier",
            "source_name",
            "source_url",
            "subtotal_price",
            "tags",
            "tax_lines",
            "taxes_included",
            "test",
            "token",
            "total_discounts",
            "total_line_items_price",
            "total_outstanding",
            "total_price",
            "total_tax",
            "total_tip_received",
            "total_weight",
            "updated_at",
            "user_id",
            "customer",
            "discount_applications",
            "payment_terms",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customer_addresses"],
        min_size=1,
        keys=[
            "id",
            "customer_id",
            "first_name",
            "last_name",
            "company",
            "address1",
            "address2",
            "city",
            "province",
            "country",
            "zip",
            "phone",
            "name",
            "province_code",
            "country_code",
            "country_name",
            "default",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blogs"],
        min_size=1,
        keys=[
            "id",
            "handle",
            "title",
            "updated_at",
            "commentable",
            "feedburner",
            "feedburner_location",
            "created_at",
            "template_suffix",
            "tags",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blog_articles"],
        min_size=1,
        keys=[
            "id",
            "title",
            "created_at",
            "body_html",
            "blog_id",
            "author",
            "user_id",
            "published_at",
            "updated_at",
            "summary_html",
            "template_suffix",
            "handle",
            "tags",
            "admin_graphql_api_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:blog_article_comments"],
        min_size=1,
        keys=[
            "id",
            "body",
            "body_html",
            "author",
            "email",
            "status",
            "article_id",
            "blog_id",
            "created_at",
            "updated_at",
            "ip",
            "user_agent",
            "published_at",
        ],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_complete_mask,
        graph,
        [shopify_connection_config],
        {"email": shopify_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    if dsr_version == "use_dsr_3_0":
        assert x == {
            f"{dataset_name}:customers": 1,
            f"{dataset_name}:blogs": 0,
            f"{dataset_name}:customer_orders": 1,
            f"{dataset_name}:blog_articles": 0,
            f"{dataset_name}:blog_article_comments": 1,
            f"{dataset_name}:customer_order_transactions": 0,
        }
    else:
        assert x == {
            f"{dataset_name}:customers": 1,
            f"{dataset_name}:blogs": 0,
            f"{dataset_name}:customer_orders": 1,
            f"{dataset_name}:customer_addresses": 2,
            f"{dataset_name}:blog_articles": 0,
            f"{dataset_name}:blog_article_comments": 1,
            f"{dataset_name}:customer_order_transactions": 0,
        }

    sleep(30)  # wait for the data to settle on Shopify's side

    CONFIG.execution.masking_strict = temp_masking
