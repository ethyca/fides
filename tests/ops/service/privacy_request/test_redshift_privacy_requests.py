from typing import Dict
from uuid import uuid4

import pytest

from fides.api.service.connectors.redshift_connector import RedshiftConnector
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    get_privacy_request_results,
)


@pytest.fixture(scope="function")
def redshift_resources(
    redshift_example_test_dataset_config,
):
    redshift_connection_config = redshift_example_test_dataset_config.connection_config
    connector = RedshiftConnector(redshift_connection_config)
    redshift_client = connector.client()
    with redshift_client.connect() as connection:
        connector.set_schema(connection)
        uuid = str(uuid4())
        customer_email = f"customer-{uuid}@example.com"
        customer_name = f"{uuid}"

        stmt = "select max(id) from customer;"
        res = connection.execute(stmt)
        customer_id = res.all()[0][0] + 1

        stmt = "select max(id) from address;"
        res = connection.execute(stmt)
        address_id = res.all()[0][0] + 1

        city = "Test City"
        state = "TX"
        stmt = f"""
        insert into address (id, house, street, city, state, zip)
        values ({address_id}, '{111}', 'Test Street', '{city}', '{state}', '55555');
        """
        connection.execute(stmt)

        stmt = f"""
            insert into customer (id, email, name, address_id)
            values ({customer_id}, '{customer_email}', '{customer_name}', '{address_id}');
        """
        connection.execute(stmt)

        yield {
            "email": customer_email,
            "name": customer_name,
            "id": customer_id,
            "client": redshift_client,
            "address_id": address_id,
            "city": city,
            "state": state,
            "connector": connector,
        }
        # Remove test data and close Redshift connection in teardown
        stmt = f"delete from customer where email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f'delete from address where "id" = {address_id};'
        connection.execute(stmt)


@pytest.mark.integration_external
@pytest.mark.integration_redshift
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_redshift(
    redshift_resources,
    db,
    cache,
    policy,
    run_privacy_request_task,
    dsr_version,
    request,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = redshift_resources["email"]
    customer_name = redshift_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = "redshift_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    address_table_key = "redshift_example_test_dataset:address"

    city = redshift_resources["city"]
    state = redshift_resources["state"]
    assert len(results[address_table_key]) == 1
    assert results[address_table_key][0]["city"] == city
    assert results[address_table_key][0]["state"] == state

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_redshift
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_redshift(
    redshift_example_test_dataset_config,
    redshift_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    erasure_policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = redshift_resources["email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    # Should erase customer name
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    connector = redshift_resources["connector"]
    redshift_client = redshift_resources["client"]
    with redshift_client.connect() as connection:
        connector.set_schema(connection)
        stmt = f"select name from customer where email = '{customer_email}';"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.name is None

        address_id = redshift_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # Not yet masked because these fields aren't targeted by erasure policy
            assert row.city == redshift_resources["city"]
            assert row.state == redshift_resources["state"]

    target = erasure_policy.rules[0].targets[0]
    target.data_category = "user.contact.address.state"
    target.save(db=db)

    # Should erase state fields on address table
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    connector = redshift_resources["connector"]
    redshift_client = redshift_resources["client"]
    with redshift_client.connect() as connection:
        connector.set_schema(connection)

        address_id = redshift_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None
