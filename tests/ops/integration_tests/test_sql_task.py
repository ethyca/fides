import copy
from datetime import datetime
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fideslang import Dataset
from sqlalchemy import text

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    FieldAddress,
    GraphDataset,
    ScalarField,
)
from fides.api.graph.data_type import DataType, StringTypeConverter
from fides.api.graph.graph import DatasetGraph, Edge, Node
from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.policy import ActionType, Policy, Rule, RuleTarget
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.service.connectors import get_connector
from fides.api.task import graph_task
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.core.config import CONFIG

from ..graph.graph_test_util import (
    assert_rows_match,
    erasure_policy,
    field,
    records_matching_fields,
)
from ..task.traversal_data import (
    integration_db_dataset,
    integration_db_graph,
    str_converter,
)

sample_postgres_configuration_policy = erasure_policy(
    "system.operations",
    "user.unique_id",
    "user.sensor",
    "user.contact.address.city",
    "user.contact.email",
    "user.contact.address.postal_code",
    "user.contact.address.state",
    "user.contact.address.street",
    "user.financial.account_number",
    "user.financial",
    "user.name",
    "user",
)


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_erasure_ignores_collections_without_pk(
    db, postgres_inserts, integration_postgres_config
):
    seed_email = postgres_inserts["customer"][0]["email"]
    policy = erasure_policy(
        "A", "B"
    )  # makes an erasure policy with two data categories to match against
    dataset = integration_db_dataset("postgres_example", "postgres_example")

    field([dataset], "postgres_example", "address", "id").primary_key = False

    # set categories: A,B will be marked erasable, C will not
    field([dataset], "postgres_example", "address", "city").data_categories = ["A"]
    field([dataset], "postgres_example", "address", "state").data_categories = ["B"]
    field([dataset], "postgres_example", "address", "zip").data_categories = ["C"]
    field([dataset], "postgres_example", "customer", "name").data_categories = ["A"]

    graph = DatasetGraph(dataset)
    privacy_request = PrivacyRequest(id=str(uuid4()))
    await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_postgres_config],
        {"email": seed_email},
        db,
    )
    v = await graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [integration_postgres_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )
    logs = [log.__dict__ for log in logs]
    # since address has no primary_key=True field, it's erasure is skipped
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name="postgres_example",
                collection_name="address",
                message="No values were erased since no primary key was defined for this collection",
            )
        )
        == 1
    )
    assert v == {
        "postgres_example:customer": 1,
        "postgres_example:payment_card": 0,
        "postgres_example:orders": 0,
        "postgres_example:address": 0,
    }


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_composite_key_erasure(
    db,
    integration_postgres_config: ConnectionConfig,
) -> None:
    privacy_request = PrivacyRequest(id=str(uuid4()))
    policy = erasure_policy("A")
    customer = Collection(
        name="customer",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(
                name="email",
                identity="email",
                data_type_converter=StringTypeConverter(),
            ),
        ],
    )

    composite_pk_test = Collection(
        name="composite_pk_test",
        fields=[
            ScalarField(
                name="id_a",
                primary_key=True,
                data_type_converter=DataType.integer.value,
            ),
            ScalarField(
                name="id_b",
                primary_key=True,
                data_type_converter=DataType.integer.value,
            ),
            ScalarField(
                name="description",
                data_type_converter=StringTypeConverter(),
                data_categories=["A"],
            ),
            ScalarField(
                name="customer_id",
                data_type_converter=DataType.integer.value,
                references=[
                    (FieldAddress("postgres_example", "customer", "id"), "from")
                ],
            ),
        ],
    )

    dataset = GraphDataset(
        name="postgres_example",
        collections=[customer, composite_pk_test],
        connection_key=integration_postgres_config.key,
    )

    access_request_data = await graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_postgres_config],
        {"email": "customer-1@example.com"},
        db,
    )
    customer = access_request_data["postgres_example:customer"][0]
    composite_pk_test = access_request_data["postgres_example:composite_pk_test"][0]

    assert customer["id"] == 1
    assert composite_pk_test["customer_id"] == 1

    # erasure
    erasure = await graph_task.run_erasure(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_postgres_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert erasure == {
        "postgres_example:customer": 0,
        "postgres_example:composite_pk_test": 1,
    }

    # re-run access request. Description has been
    # nullified here.
    privacy_request = PrivacyRequest(id=str(uuid4()))
    access_request_data = await graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_postgres_config],
        {"email": "customer-1@example.com"},
        db,
    )

    assert access_request_data == {
        "postgres_example:composite_pk_test": [
            {"id_a": 1, "id_b": 10, "description": None, "customer_id": 1}
        ],
        "postgres_example:customer": [{"id": 1, "email": "customer-1@example.com"}],
    }


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_erasure_task(db, postgres_inserts, integration_postgres_config):
    seed_email = postgres_inserts["customer"][0]["email"]

    policy = erasure_policy("A", "B")
    dataset = integration_db_dataset("postgres_example", "postgres_example")
    field([dataset], "postgres_example", "address", "id").primary_key = True
    # set categories: A,B will be marked erasable, C will not
    field([dataset], "postgres_example", "address", "city").data_categories = ["A"]
    field([dataset], "postgres_example", "address", "state").data_categories = ["B"]
    field([dataset], "postgres_example", "address", "zip").data_categories = ["C"]
    field([dataset], "postgres_example", "customer", "name").data_categories = ["A"]
    graph = DatasetGraph(dataset)
    privacy_request = PrivacyRequest(id=str(uuid4()))
    await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_postgres_config],
        {"email": seed_email},
        db,
    )
    v = await graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [integration_postgres_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert v == {
        "postgres_example:customer": 1,
        "postgres_example:payment_card": 0,
        "postgres_example:orders": 0,
        "postgres_example:address": 2,
    }


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_access_request_task(
    db,
    policy,
    integration_postgres_config,
    postgres_integration_db,
) -> None:
    privacy_request = PrivacyRequest(id=str(uuid4()))

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        integration_db_graph("postgres_example"),
        [integration_postgres_config],
        {"email": "customer-1@example.com"},
        db,
    )

    assert_rows_match(
        v["postgres_example:address"],
        min_size=2,
        keys=["id", "street", "city", "state", "zip"],
    )
    assert_rows_match(
        v["postgres_example:orders"],
        min_size=3,
        keys=["id", "customer_id", "shipping_address_id", "payment_card_id"],
    )
    assert_rows_match(
        v["postgres_example:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id", "billing_address_id"],
    )
    assert_rows_match(
        v["postgres_example:customer"],
        min_size=1,
        keys=["id", "name", "email", "address_id"],
    )

    # links
    assert v["postgres_example:customer"][0]["email"] == "customer-1@example.com"

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )

    logs = [log.__dict__ for log in logs]
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="postgres_example", collection_name="customer"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="postgres_example", collection_name="address"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="postgres_example", collection_name="orders"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name="postgres_example",
                collection_name="payment_card",
            )
        )
        > 0
    )


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_privacy_requests_against_non_default_schema(
    db,
    policy,
    postgres_connection_config_with_schema,
    postgres_integration_db,
    erasure_policy,
) -> None:
    """Assert that the postgres connector can make access and erasure requests against the non-default (public) schema"""

    privacy_request = PrivacyRequest(id=str(uuid4()))
    database_name = "postgres_backup"
    customer_email = "customer-500@example.com"

    dataset = integration_db_dataset(
        database_name, postgres_connection_config_with_schema.key
    )
    graph = DatasetGraph(dataset)

    access_results = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [postgres_connection_config_with_schema],
        {"email": customer_email},
        db,
    )

    # Confirm data retrieved from backup_schema, not public schema. This data only exists in the backup_schema.
    assert access_results == {
        f"{database_name}:address": [
            {
                "id": 7,
                "street": "Test Street",
                "city": "Test Town",
                "state": "TX",
                "zip": "79843",
            }
        ],
        f"{database_name}:payment_card": [],
        f"{database_name}:orders": [],
        f"{database_name}:customer": [
            {
                "id": 1,
                "name": "Johanna Customer",
                "email": "customer-500@example.com",
                "address_id": 7,
            }
        ],
    }

    rule = erasure_policy.rules[0]
    target = rule.targets[0]
    target.data_category = "user"
    target.save(db)
    # Update data category on customer name
    field([dataset], database_name, "customer", "name").data_categories = ["user.name"]

    erasure_results = await graph_task.run_erasure(
        privacy_request,
        erasure_policy,
        graph,
        [postgres_connection_config_with_schema],
        {"email": customer_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Confirm record masked in non-default schema
    assert erasure_results == {
        f"{database_name}:customer": 1,
        f"{database_name}:payment_card": 0,
        f"{database_name}:orders": 0,
        f"{database_name}:address": 0,
    }, "Only one record on customer table has targeted data category"
    customer_records = postgres_integration_db.execute(
        text("select * from backup_schema.customer where id = 1;")
    )
    johanna_record = [c for c in customer_records][0]
    assert johanna_record.email == customer_email  # Not masked
    assert johanna_record.name is None  # Masked by erasure request


@pytest.mark.integration_mssql
@pytest.mark.integration
@pytest.mark.asyncio
async def test_mssql_access_request_task(
    db,
    policy,
    connection_config_mssql,
    mssql_integration_db,
) -> None:
    privacy_request = PrivacyRequest(id=str(uuid4()))

    v = await graph_task.run_access_request(
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


@pytest.mark.integration_mysql
@pytest.mark.integration
@pytest.mark.asyncio
async def test_mysql_access_request_task(
    db,
    policy,
    connection_config_mysql,
    mysql_integration_db,
) -> None:
    privacy_request = PrivacyRequest(id=str(uuid4()))

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        integration_db_graph("my_mysql_db_1"),
        [connection_config_mysql],
        {"email": "customer-1@example.com"},
        db,
    )

    assert_rows_match(
        v["my_mysql_db_1:address"],
        min_size=2,
        keys=["id", "street", "city", "state", "zip"],
    )
    assert_rows_match(
        v["my_mysql_db_1:orders"],
        min_size=3,
        keys=["id", "customer_id", "shipping_address_id", "payment_card_id"],
    )
    assert_rows_match(
        v["my_mysql_db_1:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id", "billing_address_id"],
    )
    assert_rows_match(
        v["my_mysql_db_1:customer"],
        min_size=1,
        keys=["id", "name", "email", "address_id"],
    )

    # links
    assert v["my_mysql_db_1:customer"][0]["email"] == "customer-1@example.com"

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )

    logs = [log.__dict__ for log in logs]
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_mysql_db_1", collection_name="customer"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_mysql_db_1", collection_name="address"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_mysql_db_1", collection_name="orders"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name="my_mysql_db_1",
                collection_name="payment_card",
            )
        )
        > 0
    )


@pytest.mark.integration_mariadb
@pytest.mark.integration
@pytest.mark.asyncio
async def test_mariadb_access_request_task(
    db,
    policy,
    connection_config_mariadb,
    mariadb_integration_db,
) -> None:
    privacy_request = PrivacyRequest(id=str(uuid4()))

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        integration_db_graph("my_maria_db_1"),
        [connection_config_mariadb],
        {"email": "customer-1@example.com"},
        db,
    )

    assert_rows_match(
        v["my_maria_db_1:address"],
        min_size=2,
        keys=["id", "street", "city", "state", "zip"],
    )
    assert_rows_match(
        v["my_maria_db_1:orders"],
        min_size=3,
        keys=["id", "customer_id", "shipping_address_id", "payment_card_id"],
    )
    assert_rows_match(
        v["my_maria_db_1:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id", "billing_address_id"],
    )
    assert_rows_match(
        v["my_maria_db_1:customer"],
        min_size=1,
        keys=["id", "name", "email", "address_id"],
    )

    # links
    assert v["my_maria_db_1:customer"][0]["email"] == "customer-1@example.com"

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )

    logs = [log.__dict__ for log in logs]
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_maria_db_1", collection_name="customer"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_maria_db_1", collection_name="address"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name="my_maria_db_1", collection_name="orders"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name="my_maria_db_1",
                collection_name="payment_card",
            )
        )
        > 0
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_on_data_categories(
    db,
    privacy_request,
    connection_config,
    example_datasets,
    policy,
    integration_postgres_config,
):
    postgres_config = copy.copy(integration_postgres_config)

    rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": policy.client_id,
            "name": "Valid Access Rule",
            "policy_id": policy.id,
            "storage_destination_id": policy.rules[0].storage_destination.id,
        },
    )

    rule_target = RuleTarget.create(
        db,
        data={
            "name": "Test Rule 1",
            "key": "test_rule_1",
            "data_category": "user.contact.address.street",
            "rule_id": rule.id,
        },
    )

    dataset = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
    dataset_graph = DatasetGraph(*[graph])

    access_request_results = await graph_task.run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config],
        {"email": "customer-1@example.com"},
        db,
    )

    target_categories = {target.data_category for target in rule.targets}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )

    # One rule target, with data category that maps to house/street on address collection only.
    assert filtered_results == {
        "postgres_example_test_dataset:address": [
            {"house": 123, "street": "Example Street"},
            {"house": 4, "street": "Example Lane"},
        ]
    }

    # Specify the target category:
    target_categories = {"user.contact"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )

    assert filtered_results == {
        "postgres_example_test_dataset:visit": [{"email": "customer-1@example.com"}],
        "postgres_example_test_dataset:address": [
            {
                "city": "Exampletown",
                "house": 123,
                "state": "NY",
                "street": "Example Street",
                "zip": "12345",
            },
            {
                "city": "Exampletown",
                "house": 4,
                "state": "NY",
                "street": "Example Lane",
                "zip": "12321",
            },
        ],
        "postgres_example_test_dataset:service_request": [
            {"alt_email": "customer-1-alt@example.com"}
        ],
        "postgres_example_test_dataset:customer": [{"email": "customer-1@example.com"}],
    }

    # Add two more rule targets, one that is also applicable to the address table, and
    # another that spans multiple tables.

    rule_target_two = RuleTarget.create(
        db,
        data={
            "name": "Test Rule 2",
            "key": "test_rule_2",
            "data_category": "user.contact.email",
            "rule_id": rule.id,
        },
    )

    rule_target_three = RuleTarget.create(
        db,
        data={
            "name": "Test Rule 3",
            "key": "test_rule_3",
            "data_category": "user.contact.address.state",
            "rule_id": rule.id,
        },
    )

    target_categories = {target.data_category for target in rule.targets}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )
    assert filtered_results == {
        "postgres_example_test_dataset:service_request": [
            {"alt_email": "customer-1-alt@example.com"}
        ],
        "postgres_example_test_dataset:address": [
            {"house": 123, "state": "NY", "street": "Example Street"},
            {"house": 4, "state": "NY", "street": "Example Lane"},
        ],
        "postgres_example_test_dataset:visit": [{"email": "customer-1@example.com"}],
        "postgres_example_test_dataset:customer": [{"email": "customer-1@example.com"}],
    }

    rule_target.delete(db)
    rule_target_two.delete(db)
    rule_target_three.delete(db)
    rule_target.delete(db)


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_access_erasure_type_conversion(
    db,
    integration_postgres_config: ConnectionConfig,
) -> None:
    """Retrieve data from the type_link table. This requires retrieving data from
    the employee id field, which is an int, and converting it into a string to query
    against the type_link_test.id field."""
    privacy_request = PrivacyRequest(id=str(uuid4()))
    policy = erasure_policy("A")
    employee = Collection(
        name="employee",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(name="name", data_type_converter=StringTypeConverter()),
            ScalarField(
                name="email",
                identity="email",
                data_type_converter=StringTypeConverter(),
            ),
        ],
    )

    type_link = Collection(
        name="type_link_test",
        fields=[
            ScalarField(
                name="id",
                primary_key=True,
                data_type_converter=StringTypeConverter(),
                references=[
                    (FieldAddress("postgres_example", "employee", "id"), "from")
                ],
            ),
            ScalarField(
                name="name",
                data_type_converter=StringTypeConverter(),
                data_categories=["A"],
            ),
        ],
    )

    dataset = GraphDataset(
        name="postgres_example",
        collections=[employee, type_link],
        connection_key=integration_postgres_config.key,
    )

    access_request_data = await graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_postgres_config],
        {"email": "employee-1@example.com"},
        db,
    )

    employee = access_request_data["postgres_example:employee"][0]
    link = access_request_data["postgres_example:type_link_test"][0]

    assert employee["id"] == 1
    assert link["id"] == "1"

    # erasure
    erasure = await graph_task.run_erasure(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_postgres_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert erasure == {
        "postgres_example:employee": 0,
        "postgres_example:type_link_test": 1,
    }


@pytest.mark.integration_postgres
@pytest.mark.integration
class TestRetrievingData:
    @pytest.fixture
    def connector(self, integration_postgres_config):
        return get_connector(integration_postgres_config)

    @pytest.fixture
    def traversal_node(self, example_datasets, integration_postgres_config):
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
        node = Node(graph, graph.collections[1])  # customer collection
        traversal_node = TraversalNode(node)
        return traversal_node

    @mock.patch("fides.api.ops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data(
        self,
        mock_incoming_edges: Mock,
        privacy_request,
        db,
        connector,
        traversal_node,
        postgres_integration_db,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("postgres_example_test_dataset", "customer", "email"),
            )
        }

        results = connector.retrieve_data(
            traversal_node,
            Policy(),
            privacy_request,
            {"email": ["customer-1@example.com"]},
        )
        assert len(results) is 1
        assert results == [
            {
                "address_id": 1,
                "created": datetime(2020, 4, 1, 11, 47, 42),
                "email": "customer-1@example.com",
                "id": 1,
                "name": "John Customer",
            }
        ]

    @mock.patch("fides.api.ops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data_no_input(
        self,
        mock_incoming_edges: Mock,
        privacy_request,
        db,
        connector,
        traversal_node,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("postgres_example_test_dataset", "customer", "email"),
            )
        }

        assert [] == connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"email": []}
        )

        assert [] == connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {}
        )

        assert [] == connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"bad_key": ["test"]}
        )

        assert [] == connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"email": [None]}
        )

        assert [] == connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"email": None}
        )

    @mock.patch("fides.api.ops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data_input_not_in_table(
        self,
        mock_incoming_edges: Mock,
        db,
        privacy_request,
        connection_config,
        example_datasets,
        connector,
        traversal_node,
        postgres_integration_db,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("postgres_example_test_dataset", "customer", "email"),
            )
        }
        results = connector.retrieve_data(
            traversal_node,
            Policy(),
            privacy_request,
            {"email": ["customer_not_in_dataset@example.com"]},
        )
        assert results == []


@pytest.mark.integration_postgres
@pytest.mark.integration
class TestRetryIntegration:
    @mock.patch(
        "fides.api.ops.service.connectors.sql_connector.SQLConnector.retrieve_data"
    )
    @pytest.mark.asyncio
    async def test_retry_access_request(
        self,
        mock_retrieve,
        db,
        privacy_request,
        connection_config,
        example_datasets,
        policy,
        integration_postgres_config,
    ):
        CONFIG.execution.task_retry_count = 1
        CONFIG.execution.task_retry_delay = 0.1
        CONFIG.execution.task_retry_backoff = 0.01

        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
        dataset_graph = DatasetGraph(*[graph])

        # Mock errors with retrieving data
        mock_retrieve.side_effect = Exception("Insufficient data")

        # Call run_access_request with an email that isn't in the database
        with pytest.raises(Exception) as exc:
            await graph_task.run_access_request(
                privacy_request,
                sample_postgres_configuration_policy,
                dataset_graph,
                [integration_postgres_config],
                {"email": "customer-5@example.com"},
                db,
            )

        execution_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id
        )

        assert 3 == execution_logs.count()

        # Execution starts with the employee collection, retries once on failure, and then errors
        assert [
            (
                CollectionAddress(log.dataset_name, log.collection_name).value,
                log.status.value,
            )
            for log in execution_logs.order_by("created_at")
        ] == [
            ("postgres_example_test_dataset:employee", "in_processing"),
            ("postgres_example_test_dataset:employee", "retrying"),
            ("postgres_example_test_dataset:employee", "error"),
        ]

    @mock.patch("fides.api.ops.service.connectors.sql_connector.SQLConnector.mask_data")
    @pytest.mark.asyncio
    async def test_retry_erasure(
        self,
        mock_mask: Mock,
        db,
        privacy_request,
        connection_config,
        example_datasets,
        policy,
        integration_postgres_config,
    ):
        CONFIG.execution.task_retry_count = 2
        CONFIG.execution.task_retry_delay = 0.1
        CONFIG.execution.task_retry_backoff = 0.01

        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
        dataset_graph = DatasetGraph(*[graph])

        # Mock errors with masking data
        mock_mask.side_effect = Exception("Insufficient data")

        # Call run_erasure with an email that isn't in the database
        with pytest.raises(Exception):
            await graph_task.run_erasure(
                privacy_request,
                sample_postgres_configuration_policy,
                dataset_graph,
                [integration_postgres_config],
                {"email": "customer-5@example.com"},
                {
                    "postgres_example_test_dataset:employee": [],
                    "postgres_example_test_dataset:visit": [],
                    "postgres_example_test_dataset:customer": [],
                    "postgres_example_test_dataset:report": [],
                    "postgres_example_test_dataset:orders": [],
                    "postgres_example_test_dataset:payment_card": [],
                    "postgres_example_test_dataset:service_request": [],
                    "postgres_example_test_dataset:login": [],
                    "postgres_example_test_dataset:address": [],
                    "postgres_example_test_dataset:order_item": [],
                    "postgres_example_test_dataset:product": [],
                },
                db,
            )

        execution_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id
        )

        assert 4 == execution_logs.count()

        # Execution starts with the address collection, retries twice on failure, and then errors
        assert [
            (
                CollectionAddress(log.dataset_name, log.collection_name).value,
                log.status.value,
            )
            for log in execution_logs.order_by("created_at")
        ] == [
            ("postgres_example_test_dataset:address", "in_processing"),
            ("postgres_example_test_dataset:address", "retrying"),
            ("postgres_example_test_dataset:address", "retrying"),
            ("postgres_example_test_dataset:address", "error"),
        ]


@pytest.mark.integration_timescale
@pytest.mark.integration
@pytest.mark.asyncio
async def test_timescale_access_request_task(
    db,
    policy,
    timescale_connection_config,
    timescale_integration_db,
) -> None:
    database_name = "my_timescale_db_1"
    privacy_request = PrivacyRequest(id=str(uuid4()))

    v = await graph_task.run_access_request(
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
async def test_timescale_erasure_request_task(
    db,
    erasure_policy,
    timescale_connection_config,
    timescale_integration_db,
) -> None:
    rule = erasure_policy.rules[0]
    target = rule.targets[0]
    target.data_category = "user"
    target.save(db)

    database_name = "my_timescale_db_1"
    privacy_request = PrivacyRequest(id=str(uuid4()))

    dataset = integration_db_dataset(database_name, timescale_connection_config.key)

    # Set some data categories on fields that will be targeted by the policy above
    field([dataset], database_name, "customer", "name").data_categories = ["user.name"]
    field([dataset], database_name, "address", "street").data_categories = ["user"]
    field([dataset], database_name, "payment_card", "ccn").data_categories = ["user"]

    graph = DatasetGraph(dataset)

    access_results = {  # To avoid running a separate access request, just feed in what the access results would be
        f"{database_name}:payment_card": [
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
        f"{database_name}:customer": [
            {
                "id": 1,
                "name": "John Customer",
                "email": "customer-1@example.com",
                "address_id": 1,
            }
        ],
        f"{database_name}:address": [
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
        f"{database_name}:orders": [
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

    v = await graph_task.run_erasure(
        privacy_request,
        erasure_policy,
        graph,
        [timescale_connection_config],
        {"email": "customer-1@example.com"},
        access_results,
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
async def test_timescale_query_and_mask_hypertable(
    db, policy, erasure_policy, timescale_connection_config, timescale_integration_db
) -> None:
    database_name = "my_timescale_db_1"
    privacy_request = PrivacyRequest(id=str(uuid4()))

    dataset = integration_db_dataset(database_name, timescale_connection_config.key)
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

    access_results = await graph_task.run_access_request(
        privacy_request,
        policy,
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

    rule = erasure_policy.rules[0]
    target = rule.targets[0]
    target.data_category = "user"
    target.save(db)
    # Update data category on responsible field
    field(
        [dataset], database_name, "onsite_personnel", "responsible"
    ).data_categories = ["user.contact.email"]

    # Run an erasure on the hypertable targeting the responsible field
    v = await graph_task.run_erasure(
        privacy_request,
        erasure_policy,
        graph,
        [timescale_connection_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request.id),
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
