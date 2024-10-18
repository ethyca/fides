from time import sleep

import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.cache_secrets_helper import clear_cache_identities


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_square_connection_test(square_connection_config) -> None:
    get_connector(square_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_square_access_request_task_by_email(
    db,
    policy,
    privacy_request,
    dsr_version,
    request,
    square_connection_config,
    square_dataset_config,
    square_identity_email,
) -> None:
    """Full access request based on the Square SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": square_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = square_connection_config.get_saas_config().fides_key
    merged_graph = square_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [square_connection_config],
        {"email": square_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "created_at",
            "updated_at",
            "given_name",
            "family_name",
            "nickname",
            "email_address",
            "address",
            "phone_number",
            "company_name",
            "preferences",
            "creation_source",
            "birthday",
            "segment_ids",
            "version",
        ],
    )
    # verify we only returned data for our identity email
    for customer in v[f"{dataset_name}:customer"]:
        assert customer["email_address"] == square_identity_email

    assert_rows_match(
        v[f"{dataset_name}:locations"],
        min_size=1,
        keys=[
            "id",
            "name",
            "address",
            "timezone",
            "capabilities",
            "status",
            "created_at",
            "merchant_id",
            "country",
            "language_code",
            "currency",
            "business_name",
            "type",
            "business_hours",
            "mcc",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:orders"],
        min_size=1,
        keys=["id", "location_id", "customer_id", "state"],
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_square_access_request_task_by_phone_number(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    square_connection_config,
    square_dataset_config,
    square_identity_email,
    square_identity_phone_number,
) -> None:
    """Full access request based on the Square SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    # Privacy request fixture already caches an email and a phone number, so
    # clearing those first
    clear_cache_identities(privacy_request.id)

    identity = Identity(**{"phone_number": square_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = square_connection_config.get_saas_config().fides_key
    merged_graph = square_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [square_connection_config],
        {"phone_number": square_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "created_at",
            "updated_at",
            "given_name",
            "family_name",
            "nickname",
            "email_address",
            "address",
            "phone_number",
            "company_name",
            "preferences",
            "creation_source",
            "birthday",
            "segment_ids",
            "version",
        ],
    )
    # verify we only returned data for our identity phone number
    for customer in v[f"{dataset_name}:customer"]:
        assert customer["phone_number"] == square_identity_phone_number
        assert customer["email_address"] == square_identity_email


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_square_access_request_task_with_multiple_identities(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    square_connection_config,
    square_dataset_config,
    square_identity_email,
    square_identity_phone_number,
) -> None:
    """Full access request based on the Square SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(
        **{"email": square_identity_email, "phone_number": square_identity_phone_number}
    )
    privacy_request.cache_identity(identity)

    dataset_name = square_connection_config.get_saas_config().fides_key
    merged_graph = square_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [square_connection_config],
        {"email": square_identity_email, "phone_number": square_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "created_at",
            "updated_at",
            "given_name",
            "family_name",
            "nickname",
            "email_address",
            "address",
            "phone_number",
            "company_name",
            "preferences",
            "creation_source",
            "birthday",
            "segment_ids",
            "version",
        ],
    )

    # verify we only returned data for our identity phone number
    for customer in v[f"{dataset_name}:customer"]:
        assert customer["phone_number"] == square_identity_phone_number
        assert customer["email_address"] == square_identity_email

    # verify orders aren't duplicated since we are looking up the customer by two different identities
    assert len(v[f"{dataset_name}:orders"]) == 2


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.integration_square
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_square_erasure_request_task(
    db,
    privacy_request,
    dsr_version,
    request,
    erasure_policy_string_rewrite,
    square_connection_config,
    square_dataset_config,
    square_erasure_identity_email,
    square_erasure_data,
    square_test_client,
) -> None:
    """Full erasure request based on the Square SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity_kwargs = {"email": square_erasure_identity_email}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = square_connection_config.get_saas_config().fides_key
    merged_graph = square_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [square_connection_config],
        identity_kwargs,
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "created_at",
            "updated_at",
            "given_name",
            "family_name",
            "nickname",
            "email_address",
            "address",
            "company_name",
            "preferences",
            "creation_source",
            "birthday",
            "segment_ids",
            "version",
        ],
    )
    # verify we only returned data for our identity email
    for customer in v[f"{dataset_name}:customer"]:
        assert customer["email_address"] == square_erasure_identity_email

    assert_rows_match(
        v[f"{dataset_name}:locations"],
        min_size=1,
        keys=[
            "id",
            "name",
            "address",
            "timezone",
            "capabilities",
            "status",
            "created_at",
            "merchant_id",
            "country",
            "language_code",
            "currency",
            "business_name",
            "type",
            "business_hours",
            "mcc",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:orders"],
        min_size=1,
        keys=["id", "location_id", "customer_id", "state"],
    )
    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [square_connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    assert x == {
        f"{dataset_name}:customer": 1,
        f"{dataset_name}:orders": 0,
        f"{dataset_name}:locations": 0,
    }

    sleep(30)  # wait for update to propagate on Square's side

    customer_response = square_test_client.get_customer(square_erasure_identity_email)
    customer = customer_response.json()
    customer = customer["customers"][0]
    assert customer["given_name"] == "MASKED"
    assert customer["family_name"] == "MASKED"
    assert customer["nickname"] == "MASKED"

    CONFIG.execution.masking_strict = temp_masking
