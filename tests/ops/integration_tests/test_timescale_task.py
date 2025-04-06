from datetime import datetime

import pytest
from sqlalchemy import text

from fides.api.graph.config import Collection, ScalarField
from fides.api.graph.graph import DatasetGraph
from fides.api.models.privacy_request import ExecutionLog
from fides.api.task.graph_task import get_cached_data_for_erasures

from ...conftest import access_runner_tester, erasure_runner_tester
from ..graph.graph_test_util import assert_rows_match, field, records_matching_fields
from ..task.traversal_data import (
    integration_db_graph,
    postgres_db_graph_dataset,
    str_converter,
)


@pytest.mark.integration_timescale
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_timescale_access_request_task(
    db,
    policy,
    timescale_connection_config,
    timescale_integration_db,
    privacy_request,
    dsr_version,
    request,
) -> None:
    database_name = "my_timescale_db_1"
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    v = access_runner_tester(
        privacy_request,
        policy,
        integration_db_graph(database_name),
        [timescale_connection_config],
        {"email": "customer-1@example.com"},
        db,
    )

    assert_rows_match(
        v[f"{database_name}:address"],
        min_size=2,
        keys=["id", "street", "city", "state", "zip"],
    )
    assert_rows_match(
        v[f"{database_name}:orders"],
        min_size=3,
        keys=["id", "customer_id", "shipping_address_id", "payment_card_id"],
    )
    assert_rows_match(
        v[f"{database_name}:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id", "billing_address_id"],
    )
    assert_rows_match(
        v[f"{database_name}:customer"],
        min_size=1,
        keys=["id", "name", "email", "address_id"],
    )

    # links
    assert v[f"{database_name}:customer"][0]["email"] == "customer-1@example.com"

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )

    logs = [log.__dict__ for log in logs]

    assert (
        len(
            records_matching_fields(
                logs, dataset_name=database_name, collection_name="customer"
            )
        )
        > 0
    )

    assert (
        len(
            records_matching_fields(
                logs, dataset_name=database_name, collection_name="address"
            )
        )
        > 0
    )

    assert (
        len(
            records_matching_fields(
                logs, dataset_name=database_name, collection_name="orders"
            )
        )
        > 0
    )

    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name=database_name,
                collection_name="payment_card",
            )
        )
        > 0
    )


@pytest.mark.integration_timescale
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_timescale_erasure_request_task(
    db,
    erasure_policy,
    timescale_connection_config,
    timescale_integration_db,
    privacy_request_with_erasure_policy,
    dsr_version,
    request,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    rule = erasure_policy.rules[0]
    target = rule.targets[0]
    target.data_category = "user"
    target.save(db)

    database_name = "my_timescale_db_1"

    dataset = postgres_db_graph_dataset(database_name, timescale_connection_config.key)

    # Set some data categories on fields that will be targeted by the policy above
    field([dataset], database_name, "customer", "name").data_categories = ["user.name"]
    field([dataset], database_name, "address", "street").data_categories = ["user"]
    field([dataset], database_name, "payment_card", "ccn").data_categories = ["user"]

    graph = DatasetGraph(dataset)

    v = access_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        graph,
        [timescale_connection_config],
        {"email": "customer-1@example.com"},
        db,
    )

    v = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        graph,
        [timescale_connection_config],
        {"email": "customer-1@example.com"},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )
    assert v == {
        f"{database_name}:customer": 1,
        f"{database_name}:orders": 0,
        f"{database_name}:payment_card": 2,
        f"{database_name}:address": 2,
    }, "No erasure on orders table - no data categories targeted"

    # Verify masking in appropriate tables
    address_cursor = timescale_integration_db.execute(
        text("select * from address where id in (1, 2)")
    )
    for address in address_cursor:
        assert address.street is None  # Masked due to matching data category
        assert address.state is not None
        assert address.city is not None
        assert address.zip is not None

    customer_cursor = timescale_integration_db.execute(
        text("select * from customer where id = 1")
    )
    customer = [customer for customer in customer_cursor][0]
    assert customer.name is None  # Masked due to matching data category
    assert customer.email == "customer-1@example.com"
    assert customer.address_id is not None

    payment_card_cursor = timescale_integration_db.execute(
        text("select * from payment_card where id in ('pay_aaa-aaa', 'pay_bbb-bbb')")
    )
    payment_cards = [card for card in payment_card_cursor]
    assert all(
        [card.ccn is None for card in payment_cards]
    )  # Masked due to matching data category
    assert not any([card.name is None for card in payment_cards]) is None


@pytest.mark.integration_timescale
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_timescale_query_and_mask_hypertable(
    db,
    erasure_policy,
    timescale_connection_config,
    timescale_integration_db,
    privacy_request_with_erasure_policy,
    dsr_version,
    request,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    database_name = "my_timescale_db_1"

    dataset = postgres_db_graph_dataset(database_name, timescale_connection_config.key)
    # For this test, add a new collection to our standard dataset corresponding to the
    # "onsite_personnel" timescale hypertable
    onsite_personnel_collection = Collection(
        name="onsite_personnel",
        fields=[
            ScalarField(
                name="responsible", data_type_converter=str_converter, identity="email"
            ),
            ScalarField(
                name="time", data_type_converter=str_converter, primary_key=True
            ),
        ],
    )

    dataset.collections.append(onsite_personnel_collection)
    graph = DatasetGraph(dataset)
    rule = erasure_policy.rules[0]
    target = rule.targets[0]
    target.data_category = "user"
    target.save(db)
    # Update data category on responsible field
    field(
        [dataset], database_name, "onsite_personnel", "responsible"
    ).data_categories = ["user.contact.email"]

    access_results = access_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        graph,
        [timescale_connection_config],
        {"email": "employee-1@example.com"},
        db,
    )

    # Demonstrate hypertable can be queried
    assert access_results[f"{database_name}:onsite_personnel"] == [
        {"responsible": "employee-1@example.com", "time": datetime(2022, 1, 1, 9, 0)},
        {"responsible": "employee-1@example.com", "time": datetime(2022, 1, 2, 9, 0)},
        {"responsible": "employee-1@example.com", "time": datetime(2022, 1, 3, 9, 0)},
        {"responsible": "employee-1@example.com", "time": datetime(2022, 1, 5, 9, 0)},
    ]

    # Run an erasure on the hypertable targeting the responsible field
    v = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        graph,
        [timescale_connection_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )

    assert v == {
        f"{database_name}:customer": 0,
        f"{database_name}:orders": 0,
        f"{database_name}:payment_card": 0,
        f"{database_name}:address": 0,
        f"{database_name}:onsite_personnel": 4,
    }, "onsite_personnel.responsible was the only targeted data category"

    personnel_records = timescale_integration_db.execute(
        text("select * from onsite_personnel")
    )
    for record in personnel_records:
        assert (
            record.responsible != "employee-1@example.com"
        )  # These emails have all been masked
