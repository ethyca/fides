import pytest

from fides.api.models.privacy_request import ExecutionLog

from ...conftest import access_runner_tester
from ..graph.graph_test_util import assert_rows_match, records_matching_fields
from ..task.traversal_data import integration_db_graph


@pytest.mark.integration_mssql
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mssql_access_request_task(
    db,
    policy,
    connection_config_mssql,
    mssql_integration_db,
    privacy_request,
    dsr_version,
    request,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    v = access_runner_tester(
        privacy_request,
        policy,
        integration_db_graph("my_mssql_db_1"),
        [connection_config_mssql],
        {"email": "customer-1@example.com"},
        db,
    )

    assert_rows_match(
        v["my_mssql_db_1:address"],
        min_size=2,
        keys=["id", "street", "city", "state", "zip"],
    )
    assert_rows_match(
        v["my_mssql_db_1:orders"],
        min_size=3,
        keys=["id", "customer_id", "shipping_address_id", "payment_card_id"],
    )
    assert_rows_match(
        v["my_mssql_db_1:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id", "billing_address_id"],
    )
    assert_rows_match(
        v["my_mssql_db_1:customer"],
        min_size=1,
        keys=["id", "name", "email", "address_id"],
    )

    # links
    assert v["my_mssql_db_1:customer"][0]["email"] == "customer-1@example.com"

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )

    logs = [log.__dict__ for log in logs]
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_mssql_db_1", collection_name="customer"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_mssql_db_1", collection_name="address"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_mssql_db_1", collection_name="orders"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name="my_mssql_db_1",
                collection_name="payment_card",
            )
        )
        > 0
    )
