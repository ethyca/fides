import random
import time

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
@pytest.mark.integration_yotpo
def test_yotpo_connection_test(yotpo_connection_config) -> None:
    get_connector(yotpo_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_yotpo
@pytest.mark.asyncio
async def test_yotpo_access_request_task(
    db,
    policy,
    yotpo_connection_config,
    yotpo_dataset_config,
    yotpo_identity_email,
) -> None:
    """Full access request based on the yotpo SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_yotpo_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": yotpo_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = yotpo_connection_config.get_saas_config().fides_key
    merged_graph = yotpo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [yotpo_connection_config],
        {"email": yotpo_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:get_utoken_(core)"],
        min_size=1,
        keys=[
            "access_token",
        ],
    )


    assert_rows_match(
        v[f"{dataset_name}:customer_(core)"],
        min_size=1,
        keys=[
            "external_id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "gender",
            "account_created_at",
            "account_status",
            "default_language",
            "default_currency",
            "tags",
            "address",
            "custom_properties",
            "accepts_email_marketing",
            "accepts_sms_marketing",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customers_(loyalty)"],
        min_size=1,
        keys=[
            "total_spend_cents",
            "total_purchases",
            "perks_redeemed",
            "last_purchase_at",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "points_balance",
            "points_earned",
            "last_seen_at",
            "thirty_party_id",
            "third_party_id",
            "pos_account_id",
            "has_store_account",
            "credit_balance",
            "credit_balance_in_customer_currency",
            "opt_in",
            "opted_in_at",
            "points_expire_at",
            "vip_tier_actions_completed",
            "vip_tier_upgrade_requirements"
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:customer_(core)"][0]["email"] == yotpo_identity_email
    external_id = v[f"{dataset_name}:customer_(core)"][0]["external_id"]


@pytest.mark.integration_saas
@pytest.mark.integration_yotpo
@pytest.mark.asyncio
async def test_yotpo_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    yotpo_connection_config,
    yotpo_dataset_config,
    yotpo_erasure_identity_email,
    yotpo_erasure_external_id,
    yotpo_create_erasure_data,
    yotpo_create_access_token,
    yotpo_create_loyalty_user
) -> None:
    """Full erasure request based on the yotpo SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_yotpo_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": yotpo_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = yotpo_connection_config.get_saas_config().fides_key
    merged_graph = yotpo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [yotpo_connection_config],
        {"email": yotpo_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:get_utoken_(core)"],
        min_size=1,
        keys=[
            "access_token",
        ],
    )


    assert_rows_match(
        v[f"{dataset_name}:customer_(core)"],
        min_size=1,
        keys=[
            "external_id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "gender",
            "account_created_at",
            "account_status",
            "default_language",
            "default_currency",
            "tags",
            "address",
            "custom_properties",
            "accepts_email_marketing",
            "accepts_sms_marketing",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:customers_(loyalty)"],
        min_size=1,
        keys=[
            "total_spend_cents",
            "total_purchases",
            "perks_redeemed",
            "last_purchase_at",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "points_balance",
            "points_earned",
            "last_seen_at",
            "thirty_party_id",
            "third_party_id",
            "pos_account_id",
            "has_store_account",
            "credit_balance",
            "credit_balance_in_customer_currency",
            "opt_in",
            "opted_in_at",
            "points_expire_at",
            "vip_tier_actions_completed",
            "vip_tier_upgrade_requirements"
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [yotpo_connection_config],
        {"email": yotpo_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:get_utoken_(core)": 0,
        f"{dataset_name}:customer_(core)": 1,
        f"{dataset_name}:customers_(loyalty)": 1,
    }

    yotpo_secrets = yotpo_connection_config.secrets
    base_url = f"https://{yotpo_secrets['yopto_domain']}"
    loyalty_base_url = f"https://{yotpo_secrets['loyalty_api_domain']}"

    headers = {
        "X-Yotpo-Token": yotpo_create_access_token,
    }

    loyalty_headers = {
        "x-api-key": yotpo_secrets['x_api_key'],
        "x-guid": yotpo_secrets['x_guid'],
    }

    # user
    response = requests.get(
        url=f"{base_url}/core/v3/stores/{yotpo_secrets['app_key']}/customers",
        headers=headers,
        params={"external_ids": yotpo_erasure_external_id},
    )
    # Since user is deleted, it won't be available so response is 404
    assert response.status_code == 404

    # user
    loyalty_response = requests.get(
        url=f"{loyalty_base_url}/api/v2/customers/{yotpo_secrets['app_key']}/customers",
        headers=loyalty_headers,
        params={"customer_email": yotpo_erasure_identity_email},
    )
    # Since user is deleted, it won't be available so response is 404
    assert loyalty_response.status_code == 404

    CONFIG.execution.masking_strict = masking_strict
