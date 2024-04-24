import logging
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

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
def test_friendbuy_connection_test(
    friendbuy_connection_config,
) -> None:
    get_connector(friendbuy_connection_config).test_connection()


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_friendbuy_access_request_task(
    db,
    dsr_version,
    request,
    policy,
    privacy_request,
    friendbuy_connection_config,
    friendbuy_dataset_config,
    friendbuy_identity_email,
    connection_config,
    friendbuy_postgres_dataset_config,
    friendbuy_postgres_db,
) -> None:
    """Full access request based on the Friendbuy Conversations SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_attribute = "email"
    identity_value = friendbuy_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = friendbuy_connection_config.get_saas_config().fides_key
    merged_graph = friendbuy_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, friendbuy_postgres_dataset_config.get_graph()])

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [friendbuy_connection_config, connection_config],
        {"email": friendbuy_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "account_id",
            "email_address",
            "first_name",
            "last_name",
            "stripe_customer_id",
            "chargebee_customer_id",
            "first_purchase_date",
            "last_purchase_date",
            "created_at",
            "last_modified_at",
        ],
    )


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_friendbuy_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    friendbuy_connection_config,
    friendbuy_dataset_config,
    connection_config,
    friendbuy_postgres_dataset_config,
    erasure_policy_string_rewrite,
    friendbuy_erasure_identity_email,
    friendbuy_erasure_data,
    friendbuy_postgres_erasure_db,
) -> None:
    """Full erasure request based on the Friendbuy SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity_attribute = "email"
    identity_value = friendbuy_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = friendbuy_connection_config.get_saas_config().fides_key
    merged_graph = friendbuy_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, friendbuy_postgres_dataset_config.get_graph()])

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [friendbuy_connection_config, connection_config],
        {"email": friendbuy_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "account_id",
            "email_address",
            "first_name",
            "last_name",
            "stripe_customer_id",
            "chargebee_customer_id",
            "first_purchase_date",
            "last_purchase_date",
            "created_at",
            "last_modified_at",
        ],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [friendbuy_connection_config, connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Verify masking request was issued for endpoints with delete actions
    assert x == {
        "friendbuy_instance:customer": 1,
        "friendbuy_postgres:friendbuy_users": 0,
    }

    # Verifying PII is deleted but it is delayed for 60 seconds
    sleep(30)
    user_id = v[f"{dataset_name}:customer"][0]["id"]

    # Verifying user is deleted, once user is deleted email address, first_name and last_name becomes null since PII is deleted
    friendbuy_secrets = friendbuy_connection_config.secrets
    base_url = f"https://{friendbuy_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {friendbuy_secrets['token']}",
    }

    user_response = requests.get(
        url=f"{base_url}/v2/customers/{user_id}",
        headers=headers,
    )

    user = user_response.json().get("customer")

    assert user["email_address"] is None
    assert user["first_name"] is None
    assert user["last_name"] is None

    CONFIG.execution.masking_strict = temp_masking
