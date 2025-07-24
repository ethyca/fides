from datetime import datetime, timezone
from typing import Dict
from uuid import uuid4

import pytest
from boto3.dynamodb.types import TypeDeserializer

from fides.api.service.connectors.dynamodb_connector import DynamoDBConnector
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    get_privacy_request_results,
)


@pytest.fixture(scope="function")
def dynamodb_resources(
    dynamodb_example_test_dataset_config,
):
    dynamodb_connection_config = dynamodb_example_test_dataset_config.connection_config
    dynamodb_client = DynamoDBConnector(dynamodb_connection_config).client()
    uuid = str(uuid4())
    customer_email = f"customer-{uuid}@example.com"
    customer_name = f"{uuid}"

    ## document and remove remaining comments if we can't get the bigger test running
    items = {
        "customer_identifier": [
            {
                "customer_id": {"S": customer_name},
                "email": {"S": customer_email},
                "name": {"S": customer_name},
                "created": {"S": datetime.now(timezone.utc).isoformat()},
            }
        ],
        "customer": [
            {
                "id": {"S": customer_name},
                "name": {"S": customer_name},
                "email": {"S": customer_email},
                "address_id": {"L": [{"S": customer_name}, {"S": customer_name}]},
                "personal_info": {"M": {"gender": {"S": "male"}, "age": {"S": "99"}}},
                "created": {"S": datetime.now(timezone.utc).isoformat()},
            }
        ],
        "address": [
            {
                "id": {"S": customer_name},
                "city": {"S": "city"},
                "house": {"S": "house"},
                "state": {"S": "state"},
                "street": {"S": "street"},
                "zip": {"S": "zip"},
            }
        ],
        "login": [
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-01"},
                "name": {"S": customer_name},
                "email": {"S": customer_email},
            },
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-02"},
                "name": {"S": customer_name},
                "email": {"S": customer_email},
            },
        ],
    }

    for table_name, rows in items.items():
        for item in rows:
            res = dynamodb_client.put_item(
                TableName=table_name,
                Item=item,
            )
            assert res["ResponseMetadata"]["HTTPStatusCode"] == 200

    yield {
        "email": customer_email,
        "formatted_email": customer_email,
        "name": customer_name,
        "customer_id": uuid,
        "client": dynamodb_client,
    }
    # Remove test data and close Dynamodb connection in teardown
    delete_items = {
        "customer_identifier": [{"email": {"S": customer_email}}],
        "customer": [{"id": {"S": customer_name}}],
        "address": [{"id": {"S": customer_name}}],
        "login": [
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-01"},
            },
            {
                "customer_id": {"S": customer_name},
                "login_date": {"S": "2023-01-02"},
            },
        ],
    }
    for table_name, rows in delete_items.items():
        for item in rows:
            res = dynamodb_client.delete_item(
                TableName=table_name,
                Key=item,
            )
            assert res["ResponseMetadata"]["HTTPStatusCode"] == 200


@pytest.mark.integration_external
@pytest.mark.integration_dynamodb
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_empty_access_request_dynamodb(
    db,
    cache,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": "thiscustomerdoesnot@exist.com"},
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    # Here the results should be empty as no data will be located for that identity
    results = pr.get_raw_access_results()
    pr.delete(db=db)
    assert results == {}


@pytest.mark.integration_external
@pytest.mark.integration_dynamodb
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_dynamodb(
    dynamodb_resources,
    db,
    cache,
    policy,
    run_privacy_request_task,
    dsr_version,
    request,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = dynamodb_resources["email"]
    customer_name = dynamodb_resources["name"]
    customer_id = dynamodb_resources["customer_id"]
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
    customer_table_key = f"dynamodb_example_test_dataset:customer"
    address_table_key = f"dynamodb_example_test_dataset:address"
    login_table_key = f"dynamodb_example_test_dataset:login"
    assert len(results[customer_table_key]) == 1
    assert len(results[address_table_key]) == 1
    assert len(results[login_table_key]) == 2
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name
    assert results[customer_table_key][0]["id"] == customer_id
    assert results[address_table_key][0]["id"] == customer_id
    assert results[login_table_key][0]["name"] == customer_name

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_dynamodb
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_dynamodb(
    dynamodb_example_test_dataset_config,
    dynamodb_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    erasure_policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = dynamodb_resources["email"]
    dynamodb_client = dynamodb_resources["client"]
    customer_id = dynamodb_resources["customer_id"]
    customer_name = dynamodb_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)
    deserializer = TypeDeserializer()
    customer = dynamodb_client.get_item(
        TableName="customer",
        Key={"id": {"S": customer_id}},
    )
    customer_identifier = dynamodb_client.get_item(
        TableName="customer_identifier",
        Key={"email": {"S": customer_email}},
    )
    login = dynamodb_client.get_item(
        TableName="login",
        Key={
            "customer_id": {"S": customer_name},
            "login_date": {"S": "2023-01-01"},
        },
    )
    assert deserializer.deserialize(customer["Item"]["name"]) == None
    assert deserializer.deserialize(customer_identifier["Item"]["name"]) == None
    assert deserializer.deserialize(login["Item"]["name"]) == None
