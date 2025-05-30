from typing import Generator

import pytest
from fideslang.models import Dataset, MaskingStrategies
from pydantic import ValidationError

from fides.api.graph.config import CollectionAddress
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (
    BigQueryNamespaceMeta,
)
from fides.api.service.connectors import BigQueryConnector
from fides.api.service.connectors.query_configs.bigquery_query_config import (
    BigQueryQueryConfig,
)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
class TestBigQueryQueryConfig:
    """
    Verify that the generate_query method of BigQueryQueryConfig correctly adjusts
    the table name based on the available namespace info in the dataset's fides_meta.
    """

    @pytest.fixture(scope="function")
    def bigquery_client(self, bigquery_connection_config):
        connector = BigQueryConnector(bigquery_connection_config)
        return connector.client()

    @pytest.fixture(scope="function")
    def dataset_graph(self, example_datasets, bigquery_connection_config):
        dataset = Dataset(**example_datasets[7])
        graph = convert_dataset_to_graph(dataset, bigquery_connection_config.key)
        return DatasetGraph(*[graph])

    @pytest.fixture(scope="function")
    def employee_node(self, dataset_graph):
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        return bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "employee")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def address_node(self, dataset_graph):
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        return bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "address")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def customer_profile_node(self, dataset_graph):
        identity = {"email": ["customer-1@example.com", "customer-2@example.com"]}
        bigquery_traversal = Traversal(dataset_graph, identity)
        return bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer_profile")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def customer_node(self, dataset_graph):
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        return bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.fixture
    def execution_node(
        self, bigquery_example_test_dataset_config_with_namespace_meta: DatasetConfig
    ) -> Generator:
        dataset_config = bigquery_example_test_dataset_config_with_namespace_meta
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.mark.parametrize(
        "namespace_meta, expected_query",
        [
            (
                BigQueryNamespaceMeta(
                    project_id="cool_project", dataset_id="first_dataset"
                ),
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            # Namespace meta will be a dict / JSON when retrieved from the DB
            (
                {"project_id": "cool_project", "dataset_id": "first_dataset"},
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            (
                {
                    "project_id": "cool_project",
                    "dataset_id": "first_dataset",
                    "connection_type": "bigquery",
                },
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            (
                None,
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `customer` WHERE (email = :email)",
            ),
        ],
    )
    def test_generate_query_with_namespace_meta(
        self, execution_node: ExecutionNode, namespace_meta, expected_query
    ):
        query_config = BigQueryQueryConfig(execution_node, namespace_meta)
        assert (
            query_config.generate_query(
                input_data={"email": ["customer-1@example.com"]}
            ).text
            == expected_query
        )

    def test_generate_query_with_multiple_identities(
        self, execution_node: ExecutionNode
    ):
        query_config = BigQueryQueryConfig(execution_node)
        assert (
            query_config.generate_query(
                input_data={
                    "email": ["customer-1@example.com", "customer-2@example.com"]
                }
            ).text
            == "SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `customer` WHERE (email IN (:email_in_stmt_generated_0, :email_in_stmt_generated_1))"
        )

    def test_generate_query_with_nested_identity(
        self, customer_profile_node: ExecutionNode
    ):
        query_config = BigQueryQueryConfig(customer_profile_node)
        assert (
            query_config.generate_query(
                input_data={
                    "contact_info.primary_email": [
                        "customer-1@example.com",
                        "customer-2@example.com",
                    ],
                }
            ).text
            == "SELECT address, contact_info, id FROM `customer_profile` WHERE (contact_info.primary_email IN (:contact_info_primary_email_in_stmt_generated_0, :contact_info_primary_email_in_stmt_generated_1))"
        )

    def test_generate_query_with_invalid_namespace_meta(
        self, execution_node: ExecutionNode
    ):
        with pytest.raises(ValidationError) as exc:
            BigQueryQueryConfig(
                execution_node, BigQueryNamespaceMeta(dataset_id="first_dataset")
            )
        assert "Field required" in str(exc)

    def test_generate_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test node uses typical policy-level masking strategies in an update statement
        """

        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "address")
            ].collection.masking_strategy_override
            is None
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmts = BigQueryQueryConfig(address_node).generate_masking_stmt(
            address_node,
            {
                "id": "1",
                "house": "222",
                "state": "TX",
                "city": "Houston",
                "street": "Water",
                "zip": "11111",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `address` SET `house`=%(house:STRING)s, `street`=%(street:STRING)s, `city`=%(city:STRING)s, `state`=%(state:STRING)s, `zip`=%(zip:STRING)s WHERE `address`.`id` = %(id_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_delete_stmt(
        self,
        db,
        employee_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test that collection-level masking strategy override takes precedence and a delete statement is issued
        instead
        """
        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "employee")
            ].collection.masking_strategy_override.strategy
            == MaskingStrategies.DELETE
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        delete_stmts = BigQueryQueryConfig(employee_node).generate_masking_stmt(
            employee_node,
            {
                "id": "2",
                "email": "employee-2@example.com",
                "name": "John Doe",
                "address_id": "3",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in delete_stmts)
        expected_stmts = {
            "DELETE FROM `employee` WHERE `employee`.`address_id` = %(address_id_1:STRING)s AND `employee`.`email` = %(email_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_namespaced_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test node uses typical policy-level masking strategies in an update statement
        """

        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "address")
            ].collection.masking_strategy_override
            is None
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmts = BigQueryQueryConfig(
            address_node,
            BigQueryNamespaceMeta(
                project_id="silken-precinct-284918", dataset_id="fidesopstest"
            ),
        ).generate_masking_stmt(
            address_node,
            {
                "id": "1",
                "house": "222",
                "state": "TX",
                "city": "Houston",
                "street": "Water",
                "zip": "11111",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `silken-precinct-284918.fidesopstest.address` SET `house`=%(house:STRING)s, `street`=%(street:STRING)s, `city`=%(city:STRING)s, `state`=%(state:STRING)s, `zip`=%(zip:STRING)s WHERE `silken-precinct-284918.fidesopstest.address`.`id` = %(id_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_namespaced_delete_stmt(
        self,
        db,
        employee_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test that collection-level masking strategy override takes precedence and a delete statement is issued
        instead
        """
        assert (
            dataset_graph.nodes[
                CollectionAddress("bigquery_example_test_dataset", "employee")
            ].collection.masking_strategy_override.strategy
            == MaskingStrategies.DELETE
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        delete_stmts = BigQueryQueryConfig(
            employee_node,
            BigQueryNamespaceMeta(
                project_id="silken-precinct-284918", dataset_id="fidesopstest"
            ),
        ).generate_masking_stmt(
            employee_node,
            {
                "id": "2",
                "email": "employee-2@example.com",
                "name": "John Doe",
                "address_id": "3",
            },
            erasure_policy,
            privacy_request,
            bigquery_client,
        )
        stmts = set(str(stmt) for stmt in delete_stmts)
        expected_stmts = {
            "DELETE FROM `silken-precinct-284918.fidesopstest.employee` WHERE `silken-precinct-284918.fidesopstest.employee`.`address_id` = %(address_id_1:STRING)s AND `silken-precinct-284918.fidesopstest.employee`.`email` = %(email_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_update_stmt_with_nested_fields(
        self,
        db,
        customer_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test update statements correctly handle nested struct fields in BigQuery
        """
        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        # Create a row with nested data in extra_address_data struct
        customer_data = {
            "email": "customer-1@example.com",
            "id": "123",
            "name": "John Doe",
            "custom_id": "cust-123",
            "created": "2023-01-01",
            "address_id": "addr-123",
            "extra_address_data": {
                "city": "Austin",
                "house": "456",
                "id": "nested-id-123",
                "state": "TX",
                "street": "Main St",
                "address_id": "addr-nested-123",
            },
        }

        update_stmts = BigQueryQueryConfig(customer_node).generate_masking_stmt(
            customer_node,
            customer_data,
            erasure_policy,
            privacy_request,
            bigquery_client,
        )

        stmts = set(str(stmt) for stmt in update_stmts)

        # BigQuery struct updates require setting the entire struct with new values
        expected_stmts = {
            "UPDATE `customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s, `custom_id`=%(custom_id:STRING)s, `extra_address_data`=%(extra_address_data:STRUCT<city STRING, house STRING, id INT64, state STRING, street STRING, address_id INT64>)s WHERE `customer`.`email` = %(email_1:STRING)s"
        }

        assert stmts == expected_stmts

    def test_generate_update_stmt_with_nested_identity_fields(
        self,
        db,
        customer_profile_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test update statements correctly handle nested struct fields with nested identity in BigQuery
        """
        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        # Create a row with nested data in contact_info struct, which contains the identity field
        customer_profile_data = {
            "id": "profile-123",
            "contact_info": {
                "primary_email": "customer-1@example.com",
                "phone_number": "555-123-4567",
            },
            "address": "123 Main St, Austin, TX 78701",
        }

        update_stmts = BigQueryQueryConfig(customer_profile_node).generate_masking_stmt(
            customer_profile_node,
            customer_profile_data,
            erasure_policy,
            privacy_request,
            bigquery_client,
        )

        stmts = set(str(stmt) for stmt in update_stmts)

        # BigQuery nested field updates include both the identity field and other fields
        expected_stmts = {
            "UPDATE `customer_profile` SET `contact_info`=%(contact_info:STRUCT<primary_email STRING, phone_number STRING>)s, `address`=%(address:STRING)s WHERE `customer_profile`.`contact_info`.`primary_email` = %(contact_info.primary_email_1:STRING)s"
        }

        assert stmts == expected_stmts

    def test_generate_namespaced_update_stmt_with_nested_fields(
        self,
        db,
        customer_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test namespaced update statements correctly handle nested struct fields in BigQuery
        """
        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        # Create a row with nested data in extra_address_data struct
        customer_data = {
            "email": "customer-1@example.com",
            "id": "123",
            "name": "John Doe",
            "custom_id": "cust-123",
            "created": "2023-01-01",
            "address_id": "addr-123",
            "extra_address_data": {
                "city": "Austin",
                "house": "456",
                "id": "nested-id-123",
                "state": "TX",
                "street": "Main St",
                "address_id": "addr-nested-123",
            },
        }

        update_stmts = BigQueryQueryConfig(
            customer_node,
            BigQueryNamespaceMeta(
                project_id="silken-precinct-284918", dataset_id="fidesopstest"
            ),
        ).generate_masking_stmt(
            customer_node,
            customer_data,
            erasure_policy,
            privacy_request,
            bigquery_client,
        )

        stmts = set(str(stmt) for stmt in update_stmts)

        # BigQuery namespaced struct updates include the fully qualified project.dataset.table path
        expected_stmts = {
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s, `custom_id`=%(custom_id:STRING)s, `extra_address_data`=%(extra_address_data:STRUCT<city STRING, house STRING, id INT64, state STRING, street STRING, address_id INT64>)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s"
        }

        assert stmts == expected_stmts

    def test_generate_array_update_stmt(
        self,
        db,
        customer_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test update statements correctly handle simple array fields in BigQuery
        """

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        # Row with string array data
        row = {
            "id": 1,
            "email": "customer-1@example.com",
            "name": "John Doe",
            "tags": ["VIP", "Rewards", "Premium"],
        }

        update_stmts = BigQueryQueryConfig(customer_node).generate_masking_stmt(
            customer_node,
            row,
            erasure_policy,
            privacy_request,
            bigquery_client,
        )

        # Test that standard fields and array fields are included in the update parameters
        update_stmt = update_stmts[0]
        compiled_stmt = update_stmt.compile(dialect=bigquery_client.dialect)
        update_params = compiled_stmt.params

        assert update_params == {
            "id": None,
            "name": None,
            "tags": [],
            "email_1": "customer-1@example.com",
        }

        # Add expected SQL statement for clarity
        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s, `tags`=%(tags:ARRAY<STRING>)s WHERE `customer`.`email` = %(email_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_nested_array_update_stmt(
        self,
        db,
        customer_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test update statements correctly handle nested array fields in BigQuery
        """

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        # Row with nested array data
        row = {
            "id": 1,
            "email": "customer-1@example.com",
            "name": "John Doe",
            "purchase_history": [
                {
                    "item_id": 123,
                    "purchase_date": "2021-01-01",
                    "item_tags": ["Electronics", "Gadgets"],
                },
                {
                    "item_id": 456,
                    "purchase_date": "2021-02-01",
                    "item_tags": ["Books", "Fiction"],
                },
            ],
        }

        update_stmts = BigQueryQueryConfig(customer_node).generate_masking_stmt(
            customer_node,
            row,
            erasure_policy,
            privacy_request,
            bigquery_client,
        )

        # Test that array fields are processed correctly
        update_stmt = update_stmts[0]
        compiled_stmt = update_stmt.compile(dialect=bigquery_client.dialect)
        update_params = compiled_stmt.params

        assert update_params == {
            "id": None,
            "name": None,
            "purchase_history": [
                {
                    "item_id": 123,
                    "purchase_date": "2021-01-01",
                    "item_tags": [],
                },
                {
                    "item_id": 456,
                    "purchase_date": "2021-02-01",
                    "item_tags": [],
                },
            ],
            "email_1": "customer-1@example.com",
        }

        # Add expected SQL statement for clarity
        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s, `purchase_history`=%(purchase_history:ARRAY<STRUCT<item_id STRING, price FLOAT64, purchase_date STRING, item_tags ARRAY<STRING>>>)s WHERE `customer`.`email` = %(email_1:STRING)s"
        }
        assert stmts == expected_stmts

    def test_generate_namespaced_array_update_stmt(
        self,
        db,
        customer_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
        dataset_graph,
    ):
        """
        Test update statements correctly handle array fields in namespaced BigQuery configurations
        """

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        # Row with string array data
        row = {
            "id": 1,
            "email": "customer-1@example.com",
            "name": "John Doe",
            "tags": ["VIP", "Rewards", "Premium"],
        }

        update_stmts = BigQueryQueryConfig(
            customer_node,
            BigQueryNamespaceMeta(
                project_id="silken-precinct-284918", dataset_id="fidesopstest"
            ),
        ).generate_masking_stmt(
            customer_node,
            row,
            erasure_policy,
            privacy_request,
            bigquery_client,
        )

        # Test that namespaced paths work correctly
        update_stmt = update_stmts[0]
        compiled_stmt = update_stmt.compile(dialect=bigquery_client.dialect)
        update_params = compiled_stmt.params

        assert update_params == {
            "id": None,
            "name": None,
            "tags": [],
            "email_1": "customer-1@example.com",
        }

        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s, `tags`=%(tags:ARRAY<STRING>)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s"
        }
        assert stmts == expected_stmts


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
class TestBigQueryQueryConfigPartitioning:
    """
    Test partition generation functionality for BigQuery query configurations.
    """

    @pytest.fixture(scope="function")
    def bigquery_client(self, bigquery_connection_config):
        connector = BigQueryConnector(bigquery_connection_config)
        return connector.client()

    @pytest.fixture(scope="function")
    def dataset_graph(self, example_datasets, bigquery_connection_config):
        dataset = Dataset(**example_datasets[7])
        graph = convert_dataset_to_graph(dataset, bigquery_connection_config.key)
        return DatasetGraph(*[graph])

    @pytest.fixture(scope="function")
    def partitioned_customer_node(self, dataset_graph):
        """Create a customer node with time-based partitioning configuration"""
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        node = bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

        # Add partitioning configuration
        node.collection.partitioning = {
            "field": "created",
            "start": "NOW() - 1000 DAYS",
            "end": "NOW()",
            "interval": "500 DAYS",
        }
        return node

    @pytest.fixture(scope="function")
    def where_clause_partitioned_node(self, dataset_graph):
        """Create a node with where_clauses partitioning configuration"""
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        node = bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

        # Add where_clauses partitioning configuration
        node.collection.partitioning = {
            "where_clauses": [
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)",
                "`created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 DAY) AND `created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)",
            ]
        }
        return node

    @pytest.fixture(scope="function")
    def non_partitioned_node(self, dataset_graph):
        """Create a node without partitioning configuration"""
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        return bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

    def test_get_partition_clauses_time_based_partitioning(
        self, partitioned_customer_node
    ):
        """Test get_partition_clauses with time-based partitioning configuration"""
        query_config = BigQueryQueryConfig(partitioned_customer_node)
        partition_clauses = query_config.get_partition_clauses()
        assert partition_clauses == [
            "`created` > CURRENT_TIMESTAMP - INTERVAL 1000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 500 DAY",
            "`created` > CURRENT_TIMESTAMP - INTERVAL 500 DAY AND `created` <= CURRENT_TIMESTAMP",
        ]

    def test_get_partition_clauses_where_clauses_partitioning(
        self, where_clause_partitioned_node
    ):
        """Test get_partition_clauses with where_clauses partitioning configuration"""
        query_config = BigQueryQueryConfig(where_clause_partitioned_node)
        partition_clauses = query_config.get_partition_clauses()

        # Should return the exact where_clauses provided
        expected_clauses = [
            "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)",
            "`created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 DAY) AND `created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)",
        ]
        assert partition_clauses == expected_clauses

    def test_get_partition_clauses_no_partitioning(self, non_partitioned_node):
        """Test get_partition_clauses with no partitioning configuration"""
        query_config = BigQueryQueryConfig(non_partitioned_node)
        partition_clauses = query_config.get_partition_clauses()

        # Should return empty list
        assert partition_clauses == []

    def test_get_partition_clauses_invalid_partitioning_spec(
        self, non_partitioned_node
    ):
        """Test get_partition_clauses with invalid partitioning specification"""
        # Set invalid partitioning spec (missing required fields)
        non_partitioned_node.collection.partitioning = {
            "field": "created",
            "start": "NOW() - 1000 DAYS",
            # Missing 'end' and 'interval'
        }

        query_config = BigQueryQueryConfig(non_partitioned_node)

        # Should raise ValueError for invalid specification
        with pytest.raises(ValueError):
            query_config.get_partition_clauses()

    def test_get_partition_clauses_single_partition(self, dataset_graph):
        """Test get_partition_clauses when interval equals total duration (single partition)"""
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        node = bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

        # Set partitioning where interval equals total duration
        node.collection.partitioning = {
            "field": "created",
            "start": "NOW() - 7 DAYS",
            "end": "NOW()",
            "interval": "7 DAYS",
        }

        query_config = BigQueryQueryConfig(node)
        partition_clauses = query_config.get_partition_clauses()

        assert partition_clauses == [
            "`created` > CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND `created` <= CURRENT_TIMESTAMP",
        ]

    def test_get_partition_clauses_many_partitions(self, dataset_graph):
        """Test get_partition_clauses with many small partitions"""
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        node = bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

        # Set partitioning with small intervals
        node.collection.partitioning = {
            "field": "created",
            "start": "NOW() - 30 DAYS",
            "end": "NOW()",
            "interval": "5 DAYS",
        }

        query_config = BigQueryQueryConfig(node)
        partition_clauses = query_config.get_partition_clauses()

        assert partition_clauses == [
            "`created` > CURRENT_TIMESTAMP - INTERVAL 30 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 25 DAY",
            "`created` > CURRENT_TIMESTAMP - INTERVAL 25 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 20 DAY",
            "`created` > CURRENT_TIMESTAMP - INTERVAL 20 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 15 DAY",
            "`created` > CURRENT_TIMESTAMP - INTERVAL 15 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 10 DAY",
            "`created` > CURRENT_TIMESTAMP - INTERVAL 10 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 5 DAY",
            "`created` > CURRENT_TIMESTAMP - INTERVAL 5 DAY AND `created` <= CURRENT_TIMESTAMP",
        ]

    def test_get_partition_clauses_week_intervals(self, dataset_graph):
        """Test get_partition_clauses with week intervals"""
        identity = {"email": "customer-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        node = bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

        # Set partitioning with week intervals
        node.collection.partitioning = {
            "field": "last_visit",
            "start": "NOW() - 4 WEEKS",
            "end": "NOW()",
            "interval": "1 WEEK",
        }

        query_config = BigQueryQueryConfig(node)
        partition_clauses = query_config.get_partition_clauses()

        assert partition_clauses == [
            "`last_visit` > CURRENT_TIMESTAMP - INTERVAL 4 WEEK AND `last_visit` <= CURRENT_TIMESTAMP - INTERVAL 3 WEEK",
            "`last_visit` > CURRENT_TIMESTAMP - INTERVAL 3 WEEK AND `last_visit` <= CURRENT_TIMESTAMP - INTERVAL 2 WEEK",
            "`last_visit` > CURRENT_TIMESTAMP - INTERVAL 2 WEEK AND `last_visit` <= CURRENT_TIMESTAMP - INTERVAL 1 WEEK",
            "`last_visit` > CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND `last_visit` <= CURRENT_TIMESTAMP",
        ]

    def test_get_partition_clauses_with_namespace_meta(self, partitioned_customer_node):
        """Test get_partition_clauses works correctly with namespace meta"""
        namespace_meta = BigQueryNamespaceMeta(
            project_id="cool_project", dataset_id="first_dataset"
        )
        query_config = BigQueryQueryConfig(partitioned_customer_node, namespace_meta)
        partition_clauses = query_config.get_partition_clauses()

        assert partition_clauses == [
            "`created` > CURRENT_TIMESTAMP - INTERVAL 1000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 500 DAY",
            "`created` > CURRENT_TIMESTAMP - INTERVAL 500 DAY AND `created` <= CURRENT_TIMESTAMP",
        ]

    def test_generate_update_with_partitions(
        self,
        db,
        partitioned_customer_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
    ):
        """Test that update statements are correctly generated for partitioned tables"""
        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        row = {
            "email": "customer-1@example.com",
            "id": "123",
            "name": "John Doe",
        }

        query_config = BigQueryQueryConfig(partitioned_customer_node)
        update_stmts = query_config.generate_update(
            row, erasure_policy, privacy_request, bigquery_client
        )

        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s WHERE `customer`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 1000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 500 DAY",
            "UPDATE `customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s WHERE `customer`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 500 DAY AND `created` <= CURRENT_TIMESTAMP",
        }
        assert stmts == expected_stmts

    def test_generate_delete_with_partitions(
        self,
        db,
        dataset_graph,
        erasure_policy,
        privacy_request,
        bigquery_client,
    ):
        """Test that delete statements are correctly generated for partitioned tables"""
        # Create a partitioned employee node (employee has DELETE masking override)
        identity = {"email": "employee-1@example.com"}
        bigquery_traversal = Traversal(dataset_graph, identity)
        employee_node = bigquery_traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "employee")
        ].to_mock_execution_node()

        # Add partitioning configuration
        employee_node.collection.partitioning = {
            "field": "created",
            "start": "NOW() - 1000 DAYS",
            "end": "NOW()",
            "interval": "500 DAYS",
        }

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        row = {
            "email": "employee-1@example.com",
            "id": "123",
            "name": "Jane Doe",
            "address_id": "456",
        }

        query_config = BigQueryQueryConfig(employee_node)
        delete_stmts = query_config.generate_delete(row, bigquery_client)

        stmts = set(str(stmt) for stmt in delete_stmts)
        expected_stmts = {
            "DELETE FROM `employee` WHERE `employee`.`address_id` = %(address_id_1:STRING)s AND `employee`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 1000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 500 DAY",
            "DELETE FROM `employee` WHERE `employee`.`address_id` = %(address_id_1:STRING)s AND `employee`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 500 DAY AND `created` <= CURRENT_TIMESTAMP",
        }
        assert stmts == expected_stmts

    def test_generate_update_with_namespace_and_partitions(
        self,
        db,
        partitioned_customer_node,
        erasure_policy,
        privacy_request,
        bigquery_client,
    ):
        """Test that update statements correctly combine namespace and partition information"""
        namespace_meta = BigQueryNamespaceMeta(
            project_id="silken-precinct-284918", dataset_id="fidesopstest"
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        row = {
            "email": "customer-1@example.com",
            "id": "123",
            "name": "John Doe",
        }

        query_config = BigQueryQueryConfig(partitioned_customer_node, namespace_meta)
        update_stmts = query_config.generate_update(
            row, erasure_policy, privacy_request, bigquery_client
        )

        stmts = set(str(stmt) for stmt in update_stmts)
        expected_stmts = {
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 1000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 500 DAY",
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `id`=%(id:INT64)s, `name`=%(name:STRING)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 500 DAY AND `created` <= CURRENT_TIMESTAMP",
        }
        assert stmts == expected_stmts
