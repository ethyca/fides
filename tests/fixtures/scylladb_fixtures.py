from typing import Dict, Generator, List

import pytest
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from fideslang.models import Dataset
from sqlalchemy.orm import Session

from fides.api.graph.graph import Node
from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.connection_configuration.connection_secrets_scylla import (
    ScyllaSchema,
)
from fides.api.service.connectors.scylla_connector import ScyllaConnector


@pytest.fixture(scope="function")
def scylladb_integration_with_keyspace(integration_scylladb_config_with_keyspace):
    connector = ScyllaConnector(integration_scylladb_config_with_keyspace)
    client = connector.create_client()
    yield client


@pytest.fixture(scope="function")
def scylladb_integration_no_keyspace(integration_scylladb_config):
    connector = ScyllaConnector(integration_scylladb_config)
    client = connector.create_client()
    yield client


@pytest.fixture(scope="function")
def scylladb_test_dataset_config(
    integration_scylladb_config_with_keyspace: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
):
    scylladb_dataset = example_datasets[15]
    fides_key = scylladb_dataset["fides_key"]
    integration_scylladb_config_with_keyspace.name = fides_key
    integration_scylladb_config_with_keyspace.key = fides_key
    integration_scylladb_config_with_keyspace.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, scylladb_dataset)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": integration_scylladb_config_with_keyspace.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def scylladb_test_dataset_config_no_keyspace(
    integration_scylladb_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
):
    scylladb_dataset = example_datasets[15]
    fides_key = scylladb_dataset["fides_key"]
    integration_scylladb_config.name = fides_key
    integration_scylladb_config.key = fides_key
    integration_scylladb_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, scylladb_dataset)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": integration_scylladb_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def scylla_db_integration(
    integration_scylladb_config_with_keyspace,
) -> Generator[Cluster, None, None]:
    scylla_config = ScyllaSchema(**integration_scylladb_config_with_keyspace.secrets)
    auth_provider = PlainTextAuthProvider(
        username=scylla_config.username, password=scylla_config.password
    )
    cluster = Cluster(
        [scylla_config.host], port=scylla_config.port, auth_provider=auth_provider
    )
    yield cluster
    cluster.shutdown()


@pytest.fixture(scope="function")
def scylla_reset_db(scylla_db_integration: Cluster):
    """
    Removes all rows from all tables in the app_keyspace keyspace
    and re-populates them with the same insert statements as in scylla_example.cql
    This ensures a clean state for the test.
    """

    truncate_statements = [
        "TRUNCATE users;",
        "TRUNCATE user_activity;",
        "TRUNCATE payment_methods;",
        "TRUNCATE orders;",
    ]

    insert_statements = [
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins, ascii_data, big_int_data, float_data, double_data, timestamp, uuid, duration) VALUES (1, 'John', 41, 'customer-1@example.com', { 'phone': '+1 (531) 988-5905', 'work_email': 'customer-1@example.com' }, true, null, {'VA', 'NC', 'TN'}, ['12:34:26'], '!\"#$%&\()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~', 1844674407370955161, 1.1234568, 1.1234567890123446, '2011-02-03T04:05+0000', 7bac016c-3eec-4d76-ae39-605cb8ce2693, 12h30m) IF NOT EXISTS;",
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (2, 'Jane', 38, 'jane@example.com', {'phone': '+1 (393) 214-4128', 'work_email': 'jane@example.com' }, true, null, {'FL', 'MA', 'CA'}, ['11:23:15']) IF NOT EXISTS;",
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (3, 'Marguerite', 27, 'customer-2@example.com', { 'phone': '(472) 162-6435',  'work_email': 'customer-2-work@example.com' }, true, null, {'CA'}, ['08:12:54.123456789']) IF NOT EXISTS;",
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (4, 'Lafayette', 55, 'customer-3@example.com', { 'phone': '+1 (074) 534-0949',  'work_email': 'customer-3-work@example.com' }, false, '2011-02-03', {'NY', 'TX'}, ['08:12:54.123']) IF NOT EXISTS;",
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (5, 'Manuel', 23, 'customer-4@example.com', { 'phone': '+1 (831) 870-12348',  'work_email': 'customer-4@example.com' }, false, '2024-03-05', {'MO', 'KS'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;",
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (6, NULL, 23, 'customer-6@example.com', { 'phone': '+1 (831) 870-12349',  'work_email': 'customer-6@example.com' }, false, '2024-04-05', {'MO', 'NY'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;",
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (7, NULL, 26, 'customer-7@example.com', { 'phone': '+1 (831) 870-12359',  'work_email': 'customer-7@example.com' }, false, '2023-02-05', {'MO', 'TX'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;",
        "INSERT INTO users (user_id, name, age, email, alternative_contacts, do_not_contact, last_contacted, states_lived, logins) VALUES (8, 'Jasmine', 34, 'customer-8@example.com', { 'phone': '+1 (831) 214-12359',  'work_email': 'customer-8@example.com' }, false, '2024-01-23', {'CA', 'NY'}, ['08:12:54.123456', '08:12:54.123456']) IF NOT EXISTS;",
        "INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (1, '2024-07-09T04:05+0000', 'Safari', 'login') IF NOT EXISTS;",
        "INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (3, '2024-07-09T04:12+0000', 'Chrome', 'login') IF NOT EXISTS;",
        "INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (1, '2024-07-09T04:19+0000', 'Safari', 'logout') IF NOT EXISTS;",
        "INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (5, '2024-07-12T16:53+0000', 'Firefox', 'login') IF NOT EXISTS;",
        "INSERT INTO user_activity (user_id, timestamp, user_agent, activity_type) VALUES (1, '2024-07-13T17:02+0000', 'Safari iOS', 'login') IF NOT EXISTS;",
        "INSERT INTO payment_methods (payment_method_id, user_id, card_number, expiration_date) VALUES (1, 1, '123456', '2024-09-05') IF NOT EXISTS;",
        "INSERT INTO payment_methods (payment_method_id, user_id, card_number, expiration_date) VALUES (2, 2, '234567', '2028-02-01') IF NOT EXISTS;",
        "INSERT INTO payment_methods (payment_method_id, user_id, card_number, expiration_date) VALUES (3, 1, '345678', '2027-10-31') IF NOT EXISTS;",
        "INSERT INTO orders (order_id, payment_method_id, order_amount, order_date, order_description) VALUES (1, 1, 123, '2024-08-05', 'office supplies') IF NOT EXISTS;",
        "INSERT INTO orders (order_id, payment_method_id, order_amount, order_date, order_description) VALUES (2, 2, 85, '2024-08-07', 'books') IF NOT EXISTS;",
        "INSERT INTO orders (order_id, payment_method_id, order_amount, order_date, order_description) VALUES (3, 3, 1350, '2024-08-12', 'new computer') IF NOT EXISTS;",
    ]

    with scylla_db_integration.connect() as connection:
        connection.set_keyspace("app_keyspace")
        for statement in truncate_statements:
            connection.execute(statement)
        for statement in insert_statements:
            connection.execute(statement)


@pytest.fixture(scope="function")
def scylladb_execution_node(
    example_datasets, integration_scylladb_config_with_keyspace
):
    dataset = Dataset(**example_datasets[15])
    graph = convert_dataset_to_graph(
        dataset, integration_scylladb_config_with_keyspace.key
    )
    users_collection = None
    for collection in graph.collections:
        if collection.name == "users":
            users_collection = collection
            break
    node = Node(graph, users_collection)
    traversal_node = TraversalNode(node)
    return traversal_node.to_mock_execution_node()
