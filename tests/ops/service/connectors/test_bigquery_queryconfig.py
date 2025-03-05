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
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            # Namespace meta will be a dict / JSON when retrieved from the DB
            (
                {"project_id": "cool_project", "dataset_id": "first_dataset"},
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            (
                {
                    "project_id": "cool_project",
                    "dataset_id": "first_dataset",
                    "connection_type": "bigquery",
                },
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name FROM `cool_project.first_dataset.customer` WHERE (email = :email)",
            ),
            (
                None,
                "SELECT address_id, created, custom_id, email, extra_address_data, id, name FROM `customer` WHERE (email = :email)",
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
            == "SELECT address_id, created, custom_id, email, extra_address_data, id, name FROM `customer` WHERE (email IN (:email_in_stmt_generated_0, :email_in_stmt_generated_1))"
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
