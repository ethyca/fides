import uuid

import pytest

from fidesops.common_exceptions import PrivacyRequestPaused
from fidesops.graph.config import CollectionAddress
from fidesops.models.policy import PausedStep
from fidesops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fidesops.task import graph_task

from ..graph.graph_test_util import assert_rows_match
from ..task.traversal_data import postgres_and_manual_nodes


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures("postgres_integration_db")
def test_postgres_with_manual_input_access_request_task(
    db,
    policy,
    integration_postgres_config,
    integration_manual_config,
) -> None:
    """Run a privacy request with two manual nodes"""
    privacy_request = PrivacyRequest(
        id=f"test_postgres_access_request_task_{uuid.uuid4()}"
    )

    # ATTEMPT 1 - storage unit node will throw an exception. Waiting on manual input.
    with pytest.raises(PrivacyRequestPaused):
        graph_task.run_access_request(
            privacy_request,
            policy,
            postgres_and_manual_nodes("postgres_example", "manual_example"),
            [integration_postgres_config, integration_manual_config],
            {"email": "customer-1@example.com"},
        )

    request_type, paused_node = privacy_request.get_paused_step_and_collection()
    assert paused_node.value == "manual_example:storage_unit"
    assert request_type == PausedStep.access

    # Mock user retrieving storage unit data by adding manual data to cache
    privacy_request.cache_manual_input(
        CollectionAddress.from_string("manual_example:storage_unit"),
        [{"box_id": 5, "email": "customer-1@example.com"}],
    )

    # Attempt 2 - Filing cabinet node will throw an exception. Waiting on manual input.
    with pytest.raises(PrivacyRequestPaused):
        graph_task.run_access_request(
            privacy_request,
            policy,
            postgres_and_manual_nodes("postgres_example", "manual_example"),
            [integration_postgres_config, integration_manual_config],
            {"email": "customer-1@example.com"},
        )

    privacy_request.cache_manual_input(
        CollectionAddress.from_string("manual_example:filing_cabinet"),
        [{"id": 1, "authorized_user": "Jane Doe", "payment_card_id": "pay_bbb-bbb"}],
    )

    # Attempt 3 - All manual data has been retrieved.
    v = graph_task.run_access_request(
        privacy_request,
        policy,
        postgres_and_manual_nodes("postgres_example", "manual_example"),
        [integration_postgres_config, integration_manual_config],
        {"email": "customer-1@example.com"},
    )
    # Manual filing cabinet data returned
    assert_rows_match(
        v["manual_example:filing_cabinet"],
        min_size=1,
        keys=["id", "authorized_user", "payment_card_id"],
    )

    # Manual storage unit data returned
    assert_rows_match(
        v["manual_example:storage_unit"],
        min_size=1,
        keys=["box_id", "email"],
    )

    # One customer row returned
    assert_rows_match(
        v["postgres_example:customer"],
        min_size=1,
        keys=["id", "name", "email", "address_id"],
    )

    # Two payment card rows returned, one from customer_id input, other retrieved from a separate manual input
    assert_rows_match(
        v["postgres_example:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id", "billing_address_id"],
    )

    assert_rows_match(
        v["postgres_example:orders"],
        min_size=3,
        keys=["id", "customer_id", "shipping_address_id", "payment_card_id"],
    )

    assert_rows_match(
        v["postgres_example:address"],
        min_size=2,
        keys=["city", "id", "state", "street", "zip"],
    )

    # Paused node removed from cache
    request_type, paused_node = privacy_request.get_paused_step_and_collection()
    assert request_type is None
    assert paused_node is None

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    # Customer node run once.
    customer_logs = execution_logs.filter_by(collection_name="customer").order_by(
        "created_at"
    )
    assert [log.status for log in customer_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]
    assert customer_logs.count() == 2

    # Storage unit node run twice.
    storage_unit_logs = execution_logs.filter_by(
        collection_name="storage_unit"
    ).order_by("created_at")
    assert storage_unit_logs.count() == 4
    assert [log.status for log in storage_unit_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.paused,
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    # Order node run once
    order_logs = execution_logs.filter_by(collection_name="orders").order_by(
        "created_at"
    )
    assert [log.status for log in order_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]
    assert order_logs.count() == 2

    # Filing cabinet node run twice
    filing_cabinet_logs = execution_logs.filter_by(
        collection_name="filing_cabinet"
    ).order_by("created_at")
    assert filing_cabinet_logs.count() == 4
    assert [log.status for log in filing_cabinet_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.paused,
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    # Payment card node run once
    payment_logs = execution_logs.filter_by(collection_name="payment_card").order_by(
        "created_at"
    )
    assert [log.status for log in payment_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    # Address logs run once
    address_logs = execution_logs.filter_by(collection_name="address").order_by(
        "created_at"
    )
    assert [log.status for log in address_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures("postgres_integration_db")
def test_no_manual_input_found(
    policy,
    integration_postgres_config,
    integration_manual_config,
) -> None:
    """Assert manual node can be restarted with an empty list. There isn't necessarily manual data found."""
    privacy_request = PrivacyRequest(
        id=f"test_postgres_access_request_task_{uuid.uuid4()}"
    )

    # ATTEMPT 1 - storage unit node will throw an exception. Waiting on manual input.
    with pytest.raises(PrivacyRequestPaused):
        graph_task.run_access_request(
            privacy_request,
            policy,
            postgres_and_manual_nodes("postgres_example", "manual_example"),
            [integration_postgres_config, integration_manual_config],
            {"email": "customer-1@example.com"},
        )

    request_type, paused_node = privacy_request.get_paused_step_and_collection()
    assert request_type == PausedStep.access
    assert paused_node.value == "manual_example:storage_unit"

    # Mock user retrieving storage unit data by adding manual data to cache,
    # In this case, no data was found in the storage unit, so we pass in an empty list.
    privacy_request.cache_manual_input(
        CollectionAddress.from_string("manual_example:storage_unit"),
        [],
    )

    # Attempt 2 - Filing cabinet node will throw an exception. Waiting on manual input.
    with pytest.raises(PrivacyRequestPaused):
        graph_task.run_access_request(
            privacy_request,
            policy,
            postgres_and_manual_nodes("postgres_example", "manual_example"),
            [integration_postgres_config, integration_manual_config],
            {"email": "customer-1@example.com"},
        )

    # No filing cabinet input found
    privacy_request.cache_manual_input(
        CollectionAddress.from_string("manual_example:filing_cabinet"),
        [],
    )

    # Attempt 3 - All manual data has been retrieved/attempted to be retrieved
    v = graph_task.run_access_request(
        privacy_request,
        policy,
        postgres_and_manual_nodes("postgres_example", "manual_example"),
        [integration_postgres_config, integration_manual_config],
        {"email": "customer-1@example.com"},
    )

    # No filing cabinet data or storage unit data found
    assert v["manual_example:filing_cabinet"] == []
    assert v["manual_example:storage_unit"] == []

    # One customer row returned
    assert_rows_match(
        v["postgres_example:customer"],
        min_size=1,
        keys=["id", "name", "email", "address_id"],
    )

    # One payment card row returned
    assert_rows_match(
        v["postgres_example:payment_card"],
        min_size=1,
        keys=["id", "name", "ccn", "customer_id", "billing_address_id"],
    )

    # Paused node removed from cache
    request_type, paused_node = privacy_request.get_paused_step_and_collection()
    assert request_type is None
    assert paused_node is None


@pytest.mark.integration_postgres
@pytest.mark.integration
def test_collections_with_manual_erasure_confirmation(
    policy,
    integration_postgres_config,
    integration_manual_config,
) -> None:
    """Run an erasure privacy request with two manual nodes"""
    privacy_request = PrivacyRequest(
        id=f"test_postgres_access_request_task_{uuid.uuid4()}"
    )

    cached_data_for_erasures = {
        "postgres_example:payment_card": [
            {
                "id": "pay_aaa-aaa",
                "name": "Example Card 1",
                "ccn": 123456789,
                "customer_id": 1,
                "billing_address_id": 1,
            },
            {
                "id": "pay_bbb-bbb",
                "name": "Example Card 2",
                "ccn": 987654321,
                "customer_id": 2,
                "billing_address_id": 1,
            },
        ],
        "postgres_example:address": [
            {
                "id": 1,
                "street": "Example Street",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12345",
            },
            {
                "id": 2,
                "street": "Example Lane",
                "city": "Exampletown",
                "state": "NY",
                "zip": "12321",
            },
        ],
        "postgres_example:customer": [
            {
                "id": 1,
                "name": "John Customer",
                "email": "customer-1@example.com",
                "address_id": 1,
            }
        ],
        "manual_example:filing_cabinet": [
            {"id": 1, "authorized_user": "Jane Doe", "payment_card_id": "pay_bbb-bbb"}
        ],
        "manual_example:storage_unit": [
            {"box_id": 5, "email": "customer-1@example.com"}
        ],
        "postgres_example:orders": [
            {
                "id": "ord_aaa-aaa",
                "customer_id": 1,
                "shipping_address_id": 2,
                "payment_card_id": "pay_aaa-aaa",
            },
            {
                "id": "ord_ccc-ccc",
                "customer_id": 1,
                "shipping_address_id": 1,
                "payment_card_id": "pay_aaa-aaa",
            },
            {
                "id": "ord_ddd-ddd",
                "customer_id": 1,
                "shipping_address_id": 1,
                "payment_card_id": "pay_bbb-bbb",
            },
        ],
    }

    # ATTEMPT 1 - erasure request will pause to wait for confirmation that data has been destroyed from the filing cabinet
    with pytest.raises(PrivacyRequestPaused):
        graph_task.run_erasure(
            privacy_request,
            policy,
            postgres_and_manual_nodes("postgres_example", "manual_example"),
            [integration_postgres_config, integration_manual_config],
            {"email": "customer-1@example.com"},
            cached_data_for_erasures,
        )

    request_type, paused_node = privacy_request.get_paused_step_and_collection()
    assert paused_node.value == "manual_example:filing_cabinet"
    assert request_type == PausedStep.erasure

    # Mock confirming from user that there was no data in the filing cabinet
    privacy_request.cache_manual_erasure_count(
        CollectionAddress.from_string("manual_example:filing_cabinet"),
        0,
    )

    # Attempt 2 - erasure request will pause, waiting for confirmation that the box in the storage unit is destroyed.
    with pytest.raises(PrivacyRequestPaused):
        graph_task.run_erasure(
            privacy_request,
            policy,
            postgres_and_manual_nodes("postgres_example", "manual_example"),
            [integration_postgres_config, integration_manual_config],
            {"email": "customer-1@example.com"},
            cached_data_for_erasures,
        )

    request_type, paused_node = privacy_request.get_paused_step_and_collection()
    assert paused_node.value == "manual_example:storage_unit"
    assert request_type == PausedStep.erasure

    # Mock confirming from user that storage unit erasure is complete
    privacy_request.cache_manual_erasure_count(
        CollectionAddress.from_string("manual_example:storage_unit"), 1
    )

    # Attempt 3 - We've confirmed data has been removed for manual nodes so we can proceed with the rest of the erasure
    v = graph_task.run_erasure(
        privacy_request,
        policy,
        postgres_and_manual_nodes("postgres_example", "manual_example"),
        [integration_postgres_config, integration_manual_config],
        {"email": "customer-1@example.com"},
        cached_data_for_erasures,
    )

    assert v == {
        "postgres_example:customer": 0,
        "manual_example:storage_unit": 1,
        "postgres_example:payment_card": 0,
        "postgres_example:orders": 0,
        "postgres_example:address": 0,
        "manual_example:filing_cabinet": 0,
    }
