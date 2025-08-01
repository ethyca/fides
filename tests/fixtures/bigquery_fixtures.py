import ast
import os
import random
from datetime import datetime
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.connection_configuration import BigQuerySchema
from fides.api.service.connectors import BigQueryConnector, get_connector

from .application_fixtures import integration_config


@pytest.fixture(scope="function")
def bigquery_connection_config_without_secrets(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_bigquery_config",
            "connection_type": ConnectionType.bigquery,
            "access": AccessLevel.write,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def bigquery_connection_config(db: Session, bigquery_keyfile_creds) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_bigquery_config",
            "connection_type": ConnectionType.bigquery,
            "access": AccessLevel.write,
        },
    )
    # Pulling from integration config file or GitHub secrets
    dataset = integration_config.get("bigquery", {}).get("dataset") or os.environ.get(
        "BIGQUERY_DATASET"
    )
    if bigquery_keyfile_creds:
        schema = BigQuerySchema(keyfile_creds=bigquery_keyfile_creds, dataset=dataset)
        connection_config.secrets = schema.model_dump(mode="json")
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def bigquery_enterprise_test_dataset_collections(
    example_datasets: List[Dict],
) -> List[str]:
    """Returns the names of collections in the BigQuery Enterprise dataset"""
    bigquery_enterprise_dataset = example_datasets[16]
    return [
        collection["name"] for collection in bigquery_enterprise_dataset["collections"]
    ]


@pytest.fixture(scope="function")
def bigquery_enterprise_connection_config(
    db: Session, bigquery_enterprise_keyfile_creds
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_bigquery_enterprise_config",
            "connection_type": ConnectionType.bigquery,
            "access": AccessLevel.write,
        },
    )
    # Pulling from integration config file or GitHub secrets
    dataset = integration_config.get("bigquery_enterprise", {}).get(
        "dataset"
    ) or os.environ.get("BIGQUERY_ENTERPRISE_DATASET")
    if bigquery_enterprise_keyfile_creds:
        schema = BigQuerySchema(
            keyfile_creds=bigquery_enterprise_keyfile_creds, dataset=dataset
        )
        connection_config.secrets = schema.model_dump(mode="json")
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="session")
def bigquery_keyfile_creds():
    """
    Pulling from integration config file or GitHub secrets
    """
    keyfile_creds = integration_config.get("bigquery", {}).get("keyfile_creds")

    if not keyfile_creds and "BIGQUERY_KEYFILE_CREDS" in os.environ:
        keyfile_creds = ast.literal_eval(os.environ.get("BIGQUERY_KEYFILE_CREDS"))

    if not keyfile_creds:
        raise RuntimeError("Missing keyfile_creds for BigQuery")

    yield keyfile_creds


@pytest.fixture(scope="session")
def bigquery_enterprise_keyfile_creds():
    """
    Pulling from integration config file or GitHub secrets
    """
    keyfile_creds = integration_config.get("bigquery_enterprise", {}).get(
        "keyfile_creds"
    )
    if keyfile_creds:
        return keyfile_creds

    if "BIGQUERY_ENTERPRISE_KEYFILE_CREDS" in os.environ:
        keyfile_creds = ast.literal_eval(
            os.environ.get("BIGQUERY_ENTERPRISE_KEYFILE_CREDS")
        )

    if not keyfile_creds:
        raise RuntimeError("Missing keyfile_creds for BigQuery Enterprise")

    yield keyfile_creds


@pytest.fixture(scope="function")
def bigquery_connection_config_without_default_dataset(
    db: Session, bigquery_keyfile_creds
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_bigquery_config",
            "connection_type": ConnectionType.bigquery,
            "access": AccessLevel.write,
        },
    )
    if bigquery_keyfile_creds:
        schema = BigQuerySchema(keyfile_creds=bigquery_keyfile_creds)
        connection_config.secrets = schema.model_dump(mode="json")
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def bigquery_example_test_dataset_config(
    bigquery_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    bigquery_dataset = example_datasets[7]
    fides_key = bigquery_dataset["fides_key"]
    bigquery_connection_config.name = fides_key
    bigquery_connection_config.key = fides_key
    bigquery_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, bigquery_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": bigquery_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def bigquery_enterprise_test_dataset_config(
    bigquery_enterprise_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    bigquery_enterprise_dataset = example_datasets[16]
    fides_key = bigquery_enterprise_dataset["fides_key"]
    bigquery_enterprise_connection_config.name = fides_key
    bigquery_enterprise_connection_config.key = fides_key
    bigquery_enterprise_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, bigquery_enterprise_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": bigquery_enterprise_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def bigquery_enterprise_test_dataset_config_with_partitioning_meta(
    bigquery_enterprise_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    bigquery_enterprise_dataset = example_datasets[16]
    fides_key = bigquery_enterprise_dataset["fides_key"]
    bigquery_enterprise_connection_config.name = fides_key
    bigquery_enterprise_connection_config.key = fides_key

    # Update stackoverflow_posts_partitioned collection to have partition meta_data
    # It is already set up as a partitioned table in BigQuery itself
    stackoverflow_posts_partitioned_collection = next(
        collection
        for collection in bigquery_enterprise_dataset["collections"]
        if collection["name"] == "stackoverflow_posts_partitioned"
    )
    bigquery_enterprise_dataset["collections"].remove(
        stackoverflow_posts_partitioned_collection
    )
    stackoverflow_posts_partitioned_collection["fides_meta"] = {
        "partitioning": {
            "where_clauses": [
                "`creation_date` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `creation_date` <= CURRENT_TIMESTAMP()",
                "`creation_date` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `creation_date` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",
            ]
        }
    }
    bigquery_enterprise_dataset["collections"].append(
        stackoverflow_posts_partitioned_collection
    )

    bigquery_enterprise_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, bigquery_enterprise_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": bigquery_enterprise_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def bigquery_example_test_dataset_config_with_namespace_meta(
    bigquery_connection_config_without_default_dataset: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    bigquery_dataset = example_datasets[7]
    bigquery_dataset["fides_meta"] = {
        "namespace": {
            "project_id": "silken-precinct-284918",
            "dataset_id": "fidesopstest",
            "connection_type": "bigquery",
        }
    }
    fides_key = bigquery_dataset["fides_key"]
    bigquery_connection_config_without_default_dataset.name = fides_key
    bigquery_connection_config_without_default_dataset.key = fides_key
    bigquery_connection_config_without_default_dataset.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, bigquery_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": bigquery_connection_config_without_default_dataset.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta(
    bigquery_connection_config_without_default_dataset: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator[DatasetConfig, None, None]:
    bigquery_dataset = example_datasets[7]
    bigquery_dataset["fides_meta"] = {
        "namespace": {
            "project_id": "silken-precinct-284918",
            "dataset_id": "fidesopstest",
            "connection_type": "bigquery",
        },
    }
    # update customer collection to have a partition
    customer_collection = next(
        collection
        for collection in bigquery_dataset["collections"]
        if collection["name"] == "customer"
    )
    bigquery_dataset["collections"].remove(customer_collection)
    customer_collection["fides_meta"] = {
        "partitioning": {
            "where_clauses": [
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP()",
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",
            ]
        }
    }
    bigquery_dataset["collections"].append(customer_collection)

    fides_key = bigquery_dataset["fides_key"]
    bigquery_connection_config_without_default_dataset.name = fides_key
    bigquery_connection_config_without_default_dataset.key = fides_key
    bigquery_connection_config_without_default_dataset.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, bigquery_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": bigquery_connection_config_without_default_dataset.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta(
    bigquery_connection_config_without_default_dataset: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator[DatasetConfig, None, None]:
    bigquery_dataset = example_datasets[7]
    bigquery_dataset["fides_meta"] = {
        "namespace": {
            "project_id": "silken-precinct-284918",
            "dataset_id": "fidesopstest",
            "connection_type": "bigquery",
        },
    }
    # update customer collection to have TimeBasedPartitioning
    customer_collection = next(
        collection
        for collection in bigquery_dataset["collections"]
        if collection["name"] == "customer"
    )
    bigquery_dataset["collections"].remove(customer_collection)
    customer_collection["fides_meta"] = {
        "partitioning": [
            {
                "field": "created",
                "start": "NOW() - 2000 DAYS",
                "end": "NOW()",
                "interval": "1000 DAYS",
            }
        ]
    }
    bigquery_dataset["collections"].append(customer_collection)

    fides_key = bigquery_dataset["fides_key"]
    bigquery_connection_config_without_default_dataset.name = fides_key
    bigquery_connection_config_without_default_dataset.key = fides_key
    bigquery_connection_config_without_default_dataset.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, bigquery_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": bigquery_connection_config_without_default_dataset.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def bigquery_resources(
    bigquery_example_test_dataset_config,
):
    # Increment the ids by a random number to avoid conflicts on concurrent test runs
    random_increment = random.randint(1, 99999)
    bigquery_connection_config = bigquery_example_test_dataset_config.connection_config
    connector = BigQueryConnector(bigquery_connection_config)
    bigquery_client = connector.client()
    with bigquery_client.connect() as connection:
        uuid = str(uuid4())
        customer_email = f"customer-{uuid}@example.com"
        customer_name = f"{uuid}"

        stmt = "select max(id) from customer;"
        res = connection.execute(stmt)
        customer_id = res.all()[0][0] + random_increment

        stmt = "select max(id) from address;"
        res = connection.execute(stmt)
        address_id = res.all()[0][0] + random_increment

        city = "Test City"
        state = "TX"
        stmt = f"""
        insert into address (id, house, street, city, state, zip)
        values ({address_id}, '{111}', 'Test Street', '{city}', '{state}', '55555');
        """
        connection.execute(stmt)

        stmt = f"""
            insert into customer (id, email, name, address_id, `custom id`, extra_address_data, tags, purchase_history)
            values ({customer_id}, '{customer_email}', '{customer_name}', {address_id}, 'custom_{customer_id}', STRUCT('{city}' as city, '111' as house, {customer_id} as id, '{state}' as state, 'Test Street' as street, {address_id} as address_id), ['VIP', 'Rewards', 'Premium'], [STRUCT('ITEM-1' as item_id, 29.99 as price, '2023-01-15' as purchase_date, ['electronics', 'gadgets'] as item_tags), STRUCT('ITEM-2' as item_id, 49.99 as price, '2023-02-20' as purchase_date, ['clothing', 'accessories'] as item_tags)]);
        """

        connection.execute(stmt)

        # Insert into customer_profile table
        stmt = f"""
            insert into customer_profile (id, contact_info, address)
            values ({customer_id}, STRUCT('{customer_email}', '555-{customer_id}-1234'), '{111} Test Street, {city}, {state} 55555');
        """
        connection.execute(stmt)

        last_visit_date = "2024-10-03 01:00:00"
        stmt = f"""
            insert into visit_partitioned (email, last_visit)
            values ('{customer_email}', '{last_visit_date}');
        """

        connection.execute(stmt)

        stmt = "select max(id) from employee;"
        res = connection.execute(stmt)
        employee_id = res.all()[0][0] + random_increment
        employee_email = f"employee-{uuid}@example.com"
        employee_name = f"Jane {uuid}"

        stmt = f"""
           insert into employee (id, email, name, address_id)
           values ({employee_id}, '{employee_email}', '{employee_name}', {address_id});
        """
        connection.execute(stmt)

        yield {
            "email": customer_email,
            "name": customer_name,
            "id": customer_id,
            "client": bigquery_client,
            "address_id": address_id,
            "city": city,
            "state": state,
            "connector": connector,
            "employee_id": employee_id,
            "employee_email": employee_email,
        }
        # Remove test data and close BigQuery connection in teardown
        stmt = f"delete from customer where email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f"delete from customer_profile where contact_info.primary_email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f"delete from visit_partitioned where email = '{customer_email}' and last_visit = '{last_visit_date}';"
        connection.execute(stmt)

        stmt = f"delete from address where id = {address_id};"
        connection.execute(stmt)

        stmt = f"delete from employee where address_id = {address_id};"
        connection.execute(stmt)


@pytest.fixture(scope="function")
def bigquery_resources_with_namespace_meta(
    bigquery_example_test_dataset_config_with_namespace_meta,
):
    # Increment the ids by a random number to avoid conflicts on concurrent test runs
    random_increment = random.randint(1, 99999)
    bigquery_connection_config = (
        bigquery_example_test_dataset_config_with_namespace_meta.connection_config
    )
    connector = BigQueryConnector(bigquery_connection_config)
    bigquery_client = connector.client()
    with bigquery_client.connect() as connection:
        uuid = str(uuid4())
        customer_email = f"customer-{uuid}@example.com"
        customer_name = f"{uuid}"

        stmt = "select max(id) from fidesopstest.customer;"
        res = connection.execute(stmt)
        customer_id = res.all()[0][0] + random_increment

        stmt = "select max(id) from fidesopstest.address;"
        res = connection.execute(stmt)
        address_id = res.all()[0][0] + random_increment

        city = "Test City"
        state = "TX"
        stmt = f"""
        insert into fidesopstest.address (id, house, street, city, state, zip)
        values ({address_id}, '{111}', 'Test Street', '{city}', '{state}', '55555');
        """
        connection.execute(stmt)

        stmt = f"""
            insert into fidesopstest.customer (id, email, name, address_id, `custom id`, extra_address_data, tags, purchase_history, created)
            values ({customer_id}, '{customer_email}', '{customer_name}', {address_id}, 'custom_{customer_id}', STRUCT('{city}' as city, '111' as house, {customer_id} as id, '{state}' as state, 'Test Street' as street, {address_id} as address_id), ['VIP', 'Rewards', 'Premium'], [STRUCT('ITEM-1' as item_id, 29.99 as price, '2023-01-15' as purchase_date, ['electronics', 'gadgets'] as item_tags), STRUCT('ITEM-2' as item_id, 49.99 as price, '2023-02-20' as purchase_date, ['clothing', 'accessories'] as item_tags)], CURRENT_TIMESTAMP);
        """

        connection.execute(stmt)

        # Insert into customer_profile table
        stmt = f"""
            insert into fidesopstest.customer_profile (id, contact_info, address)
            values ({customer_id}, STRUCT('{customer_email}', '555-{customer_id}-1234'), '{111} Test Street, {city}, {state} 55555');
        """
        connection.execute(stmt)

        last_visit_date = "2024-10-03 01:00:00"
        stmt = f"""
            insert into fidesopstest.visit_partitioned (email, last_visit)
            values ('{customer_email}', '{last_visit_date}');
        """

        connection.execute(stmt)

        stmt = "select max(id) from fidesopstest.employee;"
        res = connection.execute(stmt)
        employee_id = res.all()[0][0] + random_increment
        employee_email = f"employee-{uuid}@example.com"
        employee_name = f"Jane {uuid}"

        stmt = f"""
           insert into fidesopstest.employee (id, email, name, address_id)
           values ({employee_id}, '{employee_email}', '{employee_name}', {address_id});
        """
        connection.execute(stmt)

        yield {
            "email": customer_email,
            "name": customer_name,
            "id": customer_id,
            "client": bigquery_client,
            "address_id": address_id,
            "city": city,
            "state": state,
            "connector": connector,
            "employee_id": employee_id,
            "employee_email": employee_email,
        }
        # Remove test data and close BigQuery connection in teardown
        stmt = f"delete from fidesopstest.customer where email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f"delete from fidesopstest.customer_profile where contact_info.primary_email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f"delete from fidesopstest.visit_partitioned where email = '{customer_email}' and last_visit = '{last_visit_date}';"
        connection.execute(stmt)

        stmt = f"delete from fidesopstest.address where id = {address_id};"
        connection.execute(stmt)

        stmt = f"delete from fidesopstest.employee where address_id = {address_id};"
        connection.execute(stmt)


@pytest.fixture(scope="function")
def bigquery_enterprise_resources(
    bigquery_enterprise_test_dataset_config,
):
    # Increment the ids by a random number to avoid conflicts on concurrent test runs
    random_increment = random.randint(1, 99999)
    bigquery_connection_config = (
        bigquery_enterprise_test_dataset_config.connection_config
    )
    connector = BigQueryConnector(bigquery_connection_config)
    bigquery_client = connector.client()
    with bigquery_client.connect() as connection:

        # Real max id in the Stackoverflow dataset is 20081052, so we purposefully generate and id above this max
        stmt = "select max(id) from enterprise_dsr_testing.users;"
        res = connection.execute(stmt)
        user_id = res.all()[0][0] + random_increment
        display_name = (
            f"fides_testing_{user_id}"  # prefix to do manual cleanup if needed
        )
        about_me = "HI hello"
        age = 25
        down_votes = 9
        last_access_date = datetime.now()
        creation_date = datetime.now()
        location = "Dream World"

        # Create test user data
        stmt = f"""
            insert into enterprise_dsr_testing.users (id, display_name, about_me, age, down_votes, last_access_date, creation_date, location, account_internal)
            values ({user_id}, '{display_name}', '{about_me}', '{age}', {down_votes}, '{last_access_date}', '{creation_date}', '{location}', [STRUCT('SILVER' as account_type, 1.04 as score, '2029-01-15' as expiry_date, ['mysql', 'html'] as tags), STRUCT('GOLD' as account_type, 0.87 as score, '2029-02-20' as expiry_date, ['css', 'html'] as tags)]);
        """
        connection.execute(stmt)

        # Create test stackoverflow_posts_partitioned data. Posts are responses to questions on Stackoverflow, and does not include original question.
        post_body = "For me, the solution was to adopt 3 cats and dance with them under the full moon at midnight."
        stmt = "select max(id) from enterprise_dsr_testing.stackoverflow_posts_partitioned;"
        res = connection.execute(stmt)
        post_id = res.all()[0][0] + random_increment
        stmt = f"""
            insert into enterprise_dsr_testing.stackoverflow_posts_partitioned (body, creation_date, id, owner_user_id, owner_display_name)
            values ('{post_body}', '{creation_date}', {post_id}, {user_id}, '{display_name}');
        """
        connection.execute(stmt)

        # Create test comments data. Comments are responses to posts or questions on Stackoverflow, and does not include original question or post itself.
        stmt = "select max(id) from enterprise_dsr_testing.comments;"
        res = connection.execute(stmt)
        comment_id = res.all()[0][0] + random_increment
        comment_text = "FYI this only works if you have pytest installed locally."
        stmt = f"""
            insert into enterprise_dsr_testing.comments (id, text, creation_date, post_id, user_id, user_display_name)
            values ({comment_id}, '{comment_text}', '{creation_date}', {post_id}, {user_id}, '{display_name}');
        """
        connection.execute(stmt)

        # Create test post_history data
        stmt = "select max(id) from enterprise_dsr_testing.post_history;"
        res = connection.execute(stmt)
        post_history_id = res.all()[0][0] + random_increment
        revision_text = "this works if you have pytest"
        uuid = str(uuid4())
        stmt = f"""
            insert into enterprise_dsr_testing.post_history (id, text, creation_date, post_id, user_id, post_history_type_id, revision_guid)
            values ({post_history_id}, '{revision_text}', '{creation_date}', {post_id}, {user_id}, 1, '{uuid}');
        """
        connection.execute(stmt)

        yield {
            "name": display_name,
            "user_id": user_id,
            "comment_id": comment_id,
            "post_history_id": post_history_id,
            "post_id": post_id,
            "client": bigquery_client,
            "connector": connector,
            "first_comment_text": comment_text,
            "first_post_body": post_body,
            "revision_text": revision_text,
            "display_name": display_name,
        }
        # Remove test data and close BigQuery connection in teardown
        stmt = f"delete from enterprise_dsr_testing.post_history where id = {post_history_id};"
        connection.execute(stmt)

        stmt = f"delete from enterprise_dsr_testing.comments where id = {comment_id};"
        connection.execute(stmt)

        stmt = f"delete from enterprise_dsr_testing.stackoverflow_posts_partitioned where id = {post_id};"
        connection.execute(stmt)

        stmt = f"delete from enterprise_dsr_testing.users where id = {user_id};"
        connection.execute(stmt)


@pytest.fixture(scope="function")
def bigquery_enterprise_resources_with_partitioning(
    bigquery_enterprise_test_dataset_config_with_partitioning_meta,
):
    # Increment the ids by a random number to avoid conflicts on concurrent test runs
    random_increment = random.randint(1, 99999)
    bigquery_connection_config = (
        bigquery_enterprise_test_dataset_config_with_partitioning_meta.connection_config
    )
    connector = BigQueryConnector(bigquery_connection_config)
    bigquery_client = connector.client()
    with bigquery_client.connect() as connection:

        # Real max id in the Stackoverflow dataset is 20081052, so we purposefully generate and id above this max
        stmt = "select max(id) from enterprise_dsr_testing.users;"
        res = connection.execute(stmt)
        user_id = res.all()[0][0] + random_increment
        display_name = (
            f"fides_testing_{user_id}"  # prefix to do manual cleanup if needed
        )
        last_access_date = datetime.now()
        creation_date = datetime.now()
        location = "Dream World"

        # Create test user data
        stmt = f"""
            insert into enterprise_dsr_testing.users (id, display_name, last_access_date, creation_date, location, account_internal)
            values ({user_id}, '{display_name}', '{last_access_date}', '{creation_date}', '{location}', [STRUCT('SILVER' as account_type, 1.04 as score, '2029-01-15' as expiry_date, ['mysql', 'html'] as tags), STRUCT('GOLD' as account_type, 0.87 as score, '2029-02-20' as expiry_date, ['css', 'html'] as tags)]);
        """
        connection.execute(stmt)

        # Create test stackoverflow_posts_partitioned data. Posts are responses to questions on Stackoverflow, and does not include original question.
        post_body = "For me, the solution was to adopt 3 cats and dance with them under the full moon at midnight."
        stmt = "select max(id) from enterprise_dsr_testing.stackoverflow_posts_partitioned;"
        res = connection.execute(stmt)
        post_id = res.all()[0][0] + random_increment
        stmt = f"""
            insert into enterprise_dsr_testing.stackoverflow_posts_partitioned (body, creation_date, id, owner_user_id, owner_display_name)
            values ('{post_body}', '{creation_date}', {post_id}, {user_id}, '{display_name}');
        """
        connection.execute(stmt)

        # Create test comments data. Comments are responses to posts or questions on Stackoverflow, and does not include original question or post itself.
        stmt = "select max(id) from enterprise_dsr_testing.comments;"
        res = connection.execute(stmt)
        comment_id = res.all()[0][0] + random_increment
        comment_text = "FYI this only works if you have pytest installed locally."
        stmt = f"""
            insert into enterprise_dsr_testing.comments (id, text, creation_date, post_id, user_id, user_display_name)
            values ({comment_id}, '{comment_text}', '{creation_date}', {post_id}, {user_id}, '{display_name}');
        """
        connection.execute(stmt)

        # Create test post_history data
        stmt = "select max(id) from enterprise_dsr_testing.post_history;"
        res = connection.execute(stmt)
        post_history_id = res.all()[0][0] + random_increment
        revision_text = "this works if you have pytest"
        uuid = str(uuid4())
        stmt = f"""
            insert into enterprise_dsr_testing.post_history (id, text, creation_date, post_id, user_id, post_history_type_id, revision_guid)
            values ({post_history_id}, '{revision_text}', '{creation_date}', {post_id}, {user_id}, 1, '{uuid}');
        """
        connection.execute(stmt)

        yield {
            "name": display_name,
            "user_id": user_id,
            "comment_id": comment_id,
            "post_history_id": post_history_id,
            "post_id": post_id,
            "client": bigquery_client,
            "connector": connector,
            "first_comment_text": comment_text,
            "first_post_body": post_body,
            "revision_text": revision_text,
            "display_name": display_name,
        }
        # Remove test data and close BigQuery connection in teardown
        stmt = f"delete from enterprise_dsr_testing.post_history where id = {post_history_id};"
        connection.execute(stmt)

        stmt = f"delete from enterprise_dsr_testing.comments where id = {comment_id};"
        connection.execute(stmt)

        stmt = f"delete from enterprise_dsr_testing.stackoverflow_posts_partitioned where id = {post_id};"
        connection.execute(stmt)

        stmt = f"delete from enterprise_dsr_testing.users where id = {user_id};"
        connection.execute(stmt)


@pytest.fixture(scope="session")
def bigquery_test_engine(bigquery_keyfile_creds) -> Generator:
    """Return a connection to a Google BigQuery Warehouse"""

    connection_config = ConnectionConfig(
        name="My BigQuery Config",
        key="test_bigquery_key",
        connection_type=ConnectionType.bigquery,
    )

    # Pulling from integration config file or GitHub secrets
    dataset = integration_config.get("bigquery", {}).get("dataset") or os.environ.get(
        "BIGQUERY_DATASET"
    )
    if bigquery_keyfile_creds:
        schema = BigQuerySchema(keyfile_creds=bigquery_keyfile_creds, dataset=dataset)
        connection_config.secrets = schema.model_dump(mode="json")

    connector: BigQueryConnector = get_connector(connection_config)
    engine = connector.client()
    connector.test_connection()
    yield engine
    engine.dispose()


def seed_bigquery_enterprise_integration_db(
    bigquery_connection_config,
) -> None:
    """
    Currently unused.
    This helper function has already been run once, and data has been populated in the test BigQuery enterprise dataset.
    We may need this later in case tables are accidentally removed.
    """
    connector = BigQueryConnector(bigquery_connection_config)
    bigquery_client = connector.client()
    with bigquery_client.connect() as connection:

        stmt = "CREATE TABLE enterprise_dsr_testing.stackoverflow_posts_partitioned partition by date(creation_date) as select * from enterprise_dsr_testing.stackoverflow_posts;"
        connection.execute(stmt)

        stmt = "ALTER TABLE enterprise_dsr_testing.users ADD COLUMN IF NOT EXISTS account_internal ARRAY<STRUCT<account_type STRING, score FLOAT64, expiry_date STRING, tags ARRAY<STRING>>;"
        connection.execute(stmt)

    logger.info(
        "Created table enterprise_dsr_testing.stackoverflow_posts_partitioned, partitioned on column creation_date."
    )


def seed_bigquery_integration_db(bigquery_integration_engine) -> None:
    """
    Currently unused.
    This helper function has already been run once, and data has been populated in the test BigQuery dataset.
    We may need this later for integration erasure tests, or in case tables are accidentally removed.
    """
    logger.info("Refreshing BigQuery integration test data")
    statements = [
        """
        DROP TABLE IF EXISTS fidesopstest.report;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.service_request;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.login;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.visit;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.visit_partitioned;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.order_item;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.orders;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.payment_card;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.employee;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.customer;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.address;
        """,
        """
        DROP TABLE IF EXISTS fidesopstest.product;

        """,
        """
        DROP TABLE IF EXISTS fidesopstest.customer_profile;
        """,
        """
        CREATE TABLE fidesopstest.product (
            id INT,
            name STRING,
            price DECIMAL(10,2)
        );
        """,
        """
        CREATE TABLE fidesopstest.customer_profile (
            id INT,
            contact_info STRUCT<
                primary_email STRING,
                phone_number STRING
            >,
            address STRING
        );
        """,
        """
        CREATE TABLE fidesopstest.address (
            id BIGINT,
            house STRING,
            street STRING,
            city STRING,
            state STRING,
            zip STRING
        );
        """,
        """
        CREATE TABLE fidesopstest.customer (
            id INT,
            email STRING,
            name STRING,
            created TIMESTAMP,
            address_id BIGINT,
            `custom id` STRING,
            extra_address_data STRUCT<
                city STRING,
                house STRING,
                id INT,
                state STRING,
                street STRING,
                address_id BIGINT
            >,
            tags ARRAY<STRING>,
            purchase_history ARRAY<STRUCT<
                item_id STRING,
                price FLOAT64,
                purchase_date STRING,
                item_tags ARRAY<STRING>
            >>
        );
        """,
        """
        CREATE TABLE fidesopstest.employee (
            id INT,
            email STRING,
            name STRING,
            address_id BIGINT
        );
        """,
        """
        CREATE TABLE fidesopstest.payment_card (
            id STRING,
            name STRING,
            ccn BIGINT,
            code SMALLINT,
            preferred BOOLEAN,
            customer_id INT,
            billing_address_id BIGINT
        );
        """,
        """
        CREATE TABLE fidesopstest.orders (
            id STRING,
            customer_id INT,
            shipping_address_id BIGINT,
            payment_card_id STRING
        );
        """,
        """
        CREATE TABLE fidesopstest.order_item (
            order_id STRING,
            item_no SMALLINT,
            product_id INT,
            quantity SMALLINT
        );
        """,
        """
        CREATE TABLE fidesopstest.visit (
            email STRING,
            last_visit TIMESTAMP
        );
        """,
        """
        CREATE TABLE fidesopstest.visit_partitioned (
            email STRING,
            last_visit TIMESTAMP
        )
        PARTITION BY
            DATE(last_visit)
            OPTIONS(
                require_partition_filter = TRUE
            )
        ;
        """,
        """
        CREATE TABLE fidesopstest.login (
            id INT,
            customer_id INT,
            time TIMESTAMP
        );
        """,
        """
        CREATE TABLE fidesopstest.service_request (
            id STRING,
            email STRING,
            alt_email STRING,
            opened DATE,
            closed DATE,
            employee_id INT
        );
        """,
        """
        CREATE TABLE fidesopstest.report (
            id INT,
            email STRING,
            name STRING,
            year INT,
            month INT,
            total_visits INT
        );
        """,
        """
        INSERT INTO fidesopstest.product VALUES
        (1, 'Example Product 1', 10.00),
        (2, 'Example Product 2', 20.00),
        (3, 'Example Product 3', 50.00);
        """,
        """
        INSERT INTO fidesopstest.address VALUES
        (1, '123', 'Example Street', 'Exampletown', 'NY', '12345'),
        (2, '4', 'Example Lane', 'Exampletown', 'NY', '12321'),
        (3, '555', 'Example Ave', 'Example City', 'NY', '12000');
        """,
        """
        INSERT INTO fidesopstest.customer VALUES
        (1, 'customer-1@example.com', 'John Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY), 1, 'custom_id_1', STRUCT('Exampletown' as city, '123' as house, 1 as id, 'NY' as state, 'Example Street' as street, 1 as address_id),
         ['VIP', 'Rewards', 'Premium'],
         [STRUCT('ITEM-1' as item_id, 29.99 as price, '2023-01-15' as purchase_date, ['electronics', 'gadgets'] as item_tags),
          STRUCT('ITEM-2' as item_id, 49.99 as price, '2023-02-20' as purchase_date, ['clothing', 'accessories'] as item_tags)]
        ),
        (2, 'customer-2@example.com', 'Jill Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY), 2, 'custom_id_2', STRUCT('Exampletown' as city, '4' as house, 2 as id, 'NY' as state, 'Example Lane' as street, 2 as address_id),
         ['Standard', 'New'],
         [STRUCT('ITEM-3' as item_id, 19.99 as price, '2023-03-10' as purchase_date, ['books', 'education'] as item_tags)]
        );
        """,
        """
        INSERT INTO fidesopstest.employee VALUES
        (1, 'employee-1@example.com', 'Jack Employee', 3),
        (2, 'employee-2@example.com', 'Jane Employee', 3);
        """,
        """
        INSERT INTO fidesopstest.payment_card VALUES
        ('pay_aaa-aaa', 'Example Card 1', 123456789, 321, true, 1, 1),
        ('pay_bbb-bbb', 'Example Card 2', 987654321, 123, false, 2, 1);
        """,
        """
        INSERT INTO fidesopstest.orders VALUES
        ('ord_aaa-aaa', 1, 2, 'pay_aaa-aaa'),
        ('ord_bbb-bbb', 2, 1, 'pay_bbb-bbb'),
        ('ord_ccc-ccc', 1, 1, 'pay_aaa-aaa'),
        ('ord_ddd-ddd', 1, 1, 'pay_bbb-bbb');
        """,
        """
        INSERT INTO fidesopstest.order_item VALUES
        ('ord_aaa-aaa', 1, 1, 1),
        ('ord_bbb-bbb', 1, 1, 1),
        ('ord_ccc-ccc', 1, 1, 1),
        ('ord_ccc-ccc', 2, 2, 1),
        ('ord_ddd-ddd', 1, 1, 1);
        """,
        """
        INSERT INTO fidesopstest.visit VALUES
        ('customer-1@example.com', '2021-01-06 01:00:00'),
        ('customer-2@example.com', '2021-01-06 01:00:00');
        """,
        """
        INSERT INTO fidesopstest.visit_partitioned VALUES
        ('customer-1@example.com', '2021-01-06 01:00:00'),
        ('customer-2@example.com', '2021-01-06 01:00:00'),
        ('customer-2@example.com', '2024-10-03 01:00:00');
        """,
        """
        INSERT INTO fidesopstest.login VALUES
        (1, 1, '2021-01-01 01:00:00'),
        (2, 1, '2021-01-02 01:00:00'),
        (5, 1, '2021-01-05 01:00:00'),
        (6, 1, '2021-01-06 01:00:00'),
        (7, 2, '2021-01-06 01:00:00');
        """,
        """
        INSERT INTO fidesopstest.service_request VALUES
        ('ser_aaa-aaa', 'customer-1@example.com', 'customer-1-alt@example.com', '2021-01-01', '2021-01-03', 1),
        ('ser_bbb-bbb', 'customer-2@example.com', null, '2021-01-04', null, 1),
        ('ser_ccc-ccc', 'customer-3@example.com', null, '2021-01-05', '2020-01-07', 1),
        ('ser_ddd-ddd', 'customer-3@example.com', null, '2021-05-05', '2020-05-08', 2);
        """,
        """
        INSERT INTO fidesopstest.report VALUES
        (1, 'admin-account@example.com', 'Monthly Report', 2021, 8, 100),
        (2, 'admin-account@example.com', 'Monthly Report', 2021, 9, 100),
        (3, 'admin-account@example.com', 'Monthly Report', 2021, 10, 100),
        (4, 'admin-account@example.com', 'Monthly Report', 2021, 11, 100);
        """,
        """
        INSERT INTO fidesopstest.customer_profile VALUES
        (1, STRUCT('customer-1@example.com', '555-123-4567'), '123 Example Street, Exampletown, NY 12345'),
        (2, STRUCT('customer-2@example.com', '555-987-6543'), '4 Example Lane, Exampletown, NY 12321');
        """,
    ]
    with bigquery_integration_engine.connect() as connection:
        [connection.execute(stmt) for stmt in statements]
    return
