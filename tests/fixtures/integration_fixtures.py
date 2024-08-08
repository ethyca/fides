import random
from datetime import datetime
from typing import Any, Dict, Generator, List
from uuid import uuid4

import pytest
from cassandra.cluster import Cluster
from pymongo import MongoClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.service.connectors import MongoDBConnector, ScyllaConnector
from tests.ops.task.traversal_data import mongo_dataset_dict, postgres_dataset_dict

from .application_fixtures import faker, integration_secrets


def generate_integration_records():
    return {
        "customer": [
            {
                "id": 10000,
                "email": "test_one@example.com",
                "name": faker.name(),
                "address_id": 1000,
            },
            {
                "id": 10001,
                "email": "test_two@example.com",
                "name": faker.name(),
                "address_id": 1001,
            },
            {
                "id": 10002,
                "email": "test_three@example.com",
                "name": faker.name(),
                "address_id": 1002,
            },
        ],
        "orders": [
            {
                "id": "test_order_id_10000",
                "customer_id": 10000,
                "payment_card_id": "test_payment_card_1000",
                "shipping_address_id": 1002,
            },
            {
                "id": "test_order_id_10001",
                "customer_id": 10001,
                "payment_card_id": uuid4(),
                "shipping_address_id": 1002,
            },
            {
                "id": "test_order_id_10002",
                "customer_id": 10002,
                "payment_card_id": uuid4(),
                "shipping_address_id": 1002,
            },
        ],
        "payment_card": [
            {
                "id": "test_payment_card_1001",
                "name": faker.name(),
                "ccn": random.randint(10000, 1000000000),
                "billing_address_id": 10001,
            },
            {
                "id": "test_payment_card_1002",
                "name": faker.name(),
                "ccn": random.randint(10000, 1000000000),
                "billing_address_id": 10002,
            },
        ],
        "address": [
            {
                "id": 1000,
                "street": faker.street_address(),
                "city": faker.city(),
                "state": faker.state(),
                "zip": faker.zipcode(),
            },
            {
                "id": 1001,
                "street": faker.street_address(),
                "city": faker.city(),
                "state": faker.state(),
                "zip": faker.zipcode(),
            },
            {
                "id": 1002,
                "street": faker.street_address(),
                "city": faker.city(),
                "state": faker.state(),
                "zip": faker.zipcode(),
            },
        ],
    }


# ======================= postgres ==========================


@pytest.fixture(scope="function")
def integration_postgres_config(postgres_inserts, db) -> ConnectionConfig:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "postgres_example",
            "name": "postgres_test",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "secrets": integration_secrets["postgres_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def integration_postgres_config_with_dataset(
    postgres_inserts, db, integration_postgres_config
) -> ConnectionConfig:
    connection_config = integration_postgres_config
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        postgres_dataset_dict(
            connection_config.key,
        ),
    )
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": connection_config.key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )

    yield connection_config

    connection_config.delete(db)
    dataset.delete(db)
    ctl_dataset.delete(db)


def sql_insert(engine: Engine, table_name: str, record: Dict[str, Any]) -> None:
    fields = record.keys()
    value_keys = [f":{k}" for k in fields]
    insert_str = f"INSERT INTO {table_name} ({','.join(fields)}) VALUES ({ ','.join(value_keys)})"
    text_clause = text(insert_str)
    with engine.connect() as connection:
        connection.execute(text_clause, record)


def sql_delete(engine: Engine, table_name: str, ids: List[Any]) -> None:
    delete_str = f"DELETE FROM {table_name} where id in {tuple(ids)}"
    with engine.connect() as connection:
        connection.execute(delete_str)


@pytest.fixture(scope="function")
def postgres_inserts(postgres_integration_db):
    integration_postgres_db_engine = postgres_integration_db.bind
    records = generate_integration_records()
    for table_name, record_list in records.items():
        for record in record_list:
            sql_insert(integration_postgres_db_engine, table_name, record)
    yield records
    for table_name, record_list in records.items():
        sql_delete(
            integration_postgres_db_engine, table_name, [r["id"] for r in record_list]
        )


# ======================= mongodb  ==========================


@pytest.fixture(scope="function")
def integration_mongodb_config(db) -> ConnectionConfig:
    connection_config = ConnectionConfig(
        key="mongo_example",
        connection_type=ConnectionType.mongodb,
        access=AccessLevel.write,
        secrets=integration_secrets["mongo_example"],
        name="mongo_example",
    )
    connection_config.save(db)
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def integration_mongodb_config_with_dataset(
    db, integration_mongodb_config, integration_postgres_config_with_dataset
) -> ConnectionConfig:
    connection_config = integration_mongodb_config
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        mongo_dataset_dict("mongo_test", integration_postgres_config_with_dataset.key),
    )
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": connection_config.key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )

    yield connection_config

    connection_config.delete(db)
    dataset.delete(db)
    ctl_dataset.delete(db)


@pytest.fixture(scope="function")
def integration_mongodb_connector(integration_mongodb_config) -> MongoClient:
    return MongoDBConnector(integration_mongodb_config).client()


def mongo_insert(
    client: MongoClient, db_name: str, collection_name: str, record: Dict[str, Any]
) -> None:
    db = client[db_name]
    collection = db[collection_name]
    return collection.insert_one(record).inserted_id


def mongo_delete(
    client: MongoClient,
    db_name: str,
    collection_name: str,
    records: List[Dict[str, Any]],
) -> None:
    """Deletion in the context of this test. This deletion is not using the mongo _id fields,
    since those are generated at the time of the test."""

    db = client[db_name]
    collection = db[collection_name]
    return collection.delete_many({"id": {"$in": [record["id"] for record in records]}})


def generate_mongo_specific_records():
    """These records are generated for mongo erasure tests where we mask some of the data as part of the test"""
    return {
        "customer_details": [
            {
                "id": "001",
                "customer_id": 10000,
                "gender": "male",
                "birthday": datetime(1988, 1, 10),
                "workplace_info": {
                    "employer": "Green Tea Company",
                    "position": "Head Grower",
                    "direct_reports": ["Margo Robbins"],
                },
                "emergency_contacts": [
                    {
                        "name": "Grace Customer",
                        "relationship": "mother",
                        "phone": "123-456-7890",
                    },
                    {
                        "name": "Joseph Customer",
                        "relationship": "brother",
                        "phone": "000-000-0000",
                    },
                ],
                "children": ["Kent Customer", "Kenny Customer"],
                "travel_identifiers": ["D222-22221", "Z111-1111"],
                "comments": [
                    {"comment_id": "com_0011"},
                    {"comment_id": "com_0013"},
                    {"comment_id": "com_0015"},
                ],
            },
            {
                "id": "002",
                "customer_id": 10001,
                "gender": "female",
                "birthday": datetime(1985, 3, 5),
                "workplace_info": {
                    "employer": "The Tool Shop",
                    "position": "Mechanic 1",
                    "direct_reports": ["Langdon Jeanne", "Dorothy Faron"],
                },
                "emergency_contacts": [
                    {
                        "name": "Jenny Customer",
                        "relationship": "spouse",
                        "phone": "111-000-1111",
                    },
                    {
                        "name": "Jill Customer",
                        "relationship": "sister",
                        "phone": "222-222-2222",
                    },
                ],
                "children": ["Connie Customer"],
                "travel_identifiers": ["C222-222222"],
            },
            {
                "id": "003",
                "customer_id": 10002,
                "gender": "female",
                "birthday": datetime(1990, 2, 28),
                "travel_identifiers": ["G111-11111"],
                "children": ["Erica Example"],
                "comments": [
                    {"comment_id": "com_0012"},
                    {"comment_id": "com_0014"},
                    {"comment_id": "com_0016"},
                ],
            },
        ],
        "customer_feedback": [
            {
                "id": "feed_1",
                "customer_information": {
                    "email": "test_one@example.com",
                    "phone": "333-000-3333",
                    "internal_customer_id": "cust_014",
                },
                "rating": 3,
                "date": datetime(2022, 1, 5),
                "message": "Customer service wait times have increased to over an hour.",
            },
            {
                "id": "feed_2",
                "customer_information": {
                    "email": "test_two@example.com",
                    "phone": "111-000-1111",
                    "internal_customer_id": "cust_015",
                },
                "rating": 5,
                "date": datetime(2022, 1, 10),
                "message": "Customer service rep was very helpful and answered all my questions.",
            },
        ],
        "internal_customer_profile": [
            {
                "id": "prof_1",
                "customer_identifiers": {"internal_id": "cust_014"},
                "derived_interests": ["marketing", "food"],
            },
            {
                "id": "prof_2",
                "customer_identifiers": {
                    "internal_id": "cust_015",
                    "derived_phone": ["757-499-5508"],
                },
                "derived_interests": ["programming", "hiking", "skateboarding"],
            },
            {
                "id": "prof_3",
                "customer_identifiers": {
                    "internal_id": "cust_016",
                    "derived_emails": ["jenny1@example.com", "jenny@example.com"],
                    "derived_phone": ["424-216-1577", "413-821-6662"],
                },
                "derived_interests": ["interior design", "travel", "photography"],
            },
        ],
        "conversations": [
            {
                "id": "thread_1",
                "thread": [
                    {
                        "comment": "com_0011",
                        "message": "hey do you know when we're landing?",
                        "chat_name": "John C",
                        "ccn": "123456789",
                    },
                    {
                        "comment": "com_0012",
                        "message": "the detour we're taking for the storm we'll probably add an hour",
                        "chat_name": "Jenny C",
                        "ccn": "987654321",
                    },
                ],
            },
            {
                "id": "thread_2",
                "thread": [
                    {
                        "comment": "com_0013",
                        "message": "should we text Grace when we land or should we just surprise her?",
                        "chat_name": "John C",
                        "ccn": "123456789",
                    },
                    {
                        "comment": "com_0014",
                        "message": "I think we should give her a heads-up",
                        "chat_name": "Jenny C",
                        "ccn": "987654321",
                    },
                    {
                        "comment": "com_0015",
                        "message": "Aw but she loves surprises.",
                        "chat_name": "John C",
                        "ccn": "123456789",
                    },
                    {
                        "comment": "com_0016",
                        "message": "I'm pretty sure she needs the peace of mind",
                        "chat_name": "Jenny C",
                    },
                ],
            },
            {
                "id": "thread_3",
                "thread": [
                    {
                        "comment": "com_0017",
                        "message": "Flight attendants, prepare the cabin take-off please.",
                        "chat_name": "Pilot 21",
                    },
                    {
                        "comment": "com_0018",
                        "message": "Airliner B, runway 13 cleared for takeoff",
                        "chat_name": "ATC 12",
                    },
                ],
            },
        ],
        "flights": [
            {
                "id": "cust_flight_1",
                "passenger_information": {
                    "passenger_ids": ["old_travel_number", "D222-22221"],
                    "full_name": "John Customer",
                },
                "flight_no": "AA230",
                "date": "2021-01-01",
                "pilots": ["3", "4"],
                "plane": 20002,
            },
            {
                "id": "cust_flight_2",
                "passenger_information": {
                    "passenger_ids": ["JK111-11111", "G111-11111"],
                    "full_name": "Jenny Customer",
                },
                "flight_no": "AA240",
                "date": "2021-02-01",
                "pilots": ["4"],
                "plane": 40005,
            },
        ],
        "aircraft": [
            {
                "id": "plane_type_1",
                "model": "Airbus A350",
                "planes": ["20001", "20002", "20003", "20004", "20005"],
            },
            {
                "id": "plane_type_2",
                "model": "Boeing 747-8",
                "planes": ["40005", "30006", "40007"],
            },
        ],
        "employee": [
            {
                "email": "employee-3@example.com",
                "name": "Jonathan Employee",
                "id": "3",
                "address": {
                    "house": 555,
                    "street": "Example Ave",
                    "city": "Example City",
                    "state": "TX",
                    "zip": "12000",
                },
                "foreign_id": "000000000000000000000001",
            },
            {
                "email": "employee-4@example.com",
                "name": "Jessica Employee",
                "id": "4",
                "address": {
                    "house": 555,
                    "street": "Example Ave",
                    "city": "Example City",
                    "state": "TX",
                    "zip": "12000",
                },
                "foreign_id": "000000000000000000000002",
            },
        ],
        "rewards": [
            {
                "id": "rew_1",
                "owner": [
                    {"phone": "424-216-1577", "shopper_name": "jenny"},
                    {"phone": "217-821-9886", "shopper_name": "jenny"},
                ],
                "points": 100,
                "expiration": datetime(2023, 1, 5),
            },
            {
                "id": "rew_2",
                "owner": [{"phone": "413-821-6662", "shopper_name": "jenny"}],
                "points": 2,
                "expiration": datetime(2023, 2, 5),
            },
            {
                "id": "rew_3",
                "owner": [{"phone": "805-496-5401", "shopper-name": "jenny"}],
                "points": 2,
                "expiration": datetime(2022, 2, 5),
            },
        ],
    }


@pytest.fixture(scope="function")
def mongo_inserts(integration_mongodb_connector):
    records = generate_integration_records()
    records.update(generate_mongo_specific_records())
    for table_name, record_list in records.items():
        for record in record_list:
            mongo_insert(
                integration_mongodb_connector, "mongo_test", table_name, record
            )
    yield records
    for table_name, record_list in records.items():
        mongo_delete(
            integration_mongodb_connector, "mongo_test", table_name, record_list
        )


# ======================= dynamodb  ==========================


@pytest.fixture(scope="function")
def integration_dynamodb_config(db) -> ConnectionConfig:
    connection_config = ConnectionConfig(
        key="dynamodb_example",
        connection_type=ConnectionType.dynamodb,
        access=AccessLevel.write,
        secrets=integration_secrets["dynamodb_example"],
        name="dynamodb_example",
    )
    connection_config.save(db)
    yield connection_config
    connection_config.delete(db)


# ======================= scylladb  ==========================


@pytest.fixture(scope="function")
def integration_scylladb_config(db) -> ConnectionConfig:
    connection_config = ConnectionConfig(
        key="scylla_example",
        connection_type=ConnectionType.scylla,
        access=AccessLevel.read,
        secrets=integration_secrets["scylla_example"],
        name="scylla_example",
    )
    connection_config.save(db)
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def integration_scylladb_config_with_keyspace(
    db,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig(
        key="scylla_example_with_keyspace",
        connection_type=ConnectionType.scylla,
        access=AccessLevel.write,
        secrets={**integration_secrets["scylla_example"], "keyspace": "app_keyspace"},
        name="scylla_example_with_keyspace",
    )
    connection_config.save(db)
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def integration_scylla_connector(integration_scylladb_config) -> Cluster:
    return ScyllaConnector(integration_scylladb_config).client()
