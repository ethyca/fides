import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import get_config
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.cache_secrets_helper import clear_cache_identities
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

CONFIG = get_config()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_yotpo_loyalty_connection_test(yotpo_loyalty_connection_config) -> None:
    get_connector(yotpo_loyalty_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_yotpo_loyalty_access_request_task_with_email(
    db,
    privacy_request,
    policy,
    dsr_version,
    request,
    yotpo_loyalty_connection_config,
    yotpo_loyalty_dataset_config,
    yotpo_loyalty_identity_email,
) -> None:
    """Full access request based on the Yotpo Loyalty & Referrals SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": yotpo_loyalty_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = yotpo_loyalty_connection_config.get_saas_config().fides_key
    merged_graph = yotpo_loyalty_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [yotpo_loyalty_connection_config],
        {"email": yotpo_loyalty_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
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
            "vip_tier_upgrade_requirements",
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:customer"][0]["email"] == yotpo_loyalty_identity_email


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_yotpo_loyalty_access_request_task_with_phone_number(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    yotpo_loyalty_connection_config,
    yotpo_loyalty_dataset_config,
    yotpo_loyalty_identity_phone_number,
) -> None:
    """Full access request based on the Yotpo Loyalty & Referrals SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    # Privacy request fixture caches email and phone identities - clearing this first -
    clear_cache_identities(privacy_request.id)

    identity = Identity(**{"phone_number": yotpo_loyalty_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = yotpo_loyalty_connection_config.get_saas_config().fides_key
    merged_graph = yotpo_loyalty_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [yotpo_loyalty_connection_config],
        {"phone_number": yotpo_loyalty_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
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
            "vip_tier_upgrade_requirements",
        ],
    )

    # verify we only returned data for our identity phone number
    assert (
        v[f"{dataset_name}:customer"][0]["phone_number"]
        == yotpo_loyalty_identity_phone_number
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_yotpo_loyalty_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    erasure_policy_string_rewrite,
    yotpo_loyalty_connection_config,
    yotpo_loyalty_dataset_config,
    yotpo_loyalty_erasure_identity_email,
    yotpo_loyalty_erasure_data,
    yotpo_loyalty_test_client,
) -> None:
    """Full erasure request based on the Yotpo Loyalty & Referrals SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    identity = Identity(**{"email": yotpo_loyalty_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = yotpo_loyalty_connection_config.get_saas_config().fides_key
    merged_graph = yotpo_loyalty_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [yotpo_loyalty_connection_config],
        {"email": yotpo_loyalty_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
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
            "vip_tier_upgrade_requirements",
        ],
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [yotpo_loyalty_connection_config],
        {"email": yotpo_loyalty_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {f"{dataset_name}:customer": 1}

    poll_for_existence(
        yotpo_loyalty_test_client.get_customer,
        (yotpo_loyalty_erasure_identity_email,),
        existence_desired=False,
    )

    CONFIG.execution.masking_strict = masking_strict
