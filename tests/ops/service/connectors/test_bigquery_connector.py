import logging
from typing import Generator

import pytest
import sqlalchemy
from fideslang.models import Dataset, MaskingStrategies, MaskingStrategyOverride
from loguru import logger
from sqlalchemy import text

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (
    BigQueryNamespaceMeta,
)
from fides.api.service.connectors.bigquery_connector import BigQueryConnector
from tests.fixtures.bigquery_fixtures import seed_bigquery_integration_db


@pytest.fixture(scope="session", autouse=True)
def update_bigquery_data(bigquery_test_engine):
    """Refresh the BigQuery data at the start of the test session"""
    seed_bigquery_integration_db(bigquery_test_engine)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
class TestBigQueryConnector:
    """
    Tests to verify that the query_config method of BigQueryConnector
    correctly retrieves namespace metadata from the dataset (if available).
    """

    @pytest.fixture
    def execution_node(
        self, bigquery_example_test_dataset_config: DatasetConfig
    ) -> Generator:
        dataset_config = bigquery_example_test_dataset_config
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.fixture
    def execution_node_with_namespace_meta(
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

    @pytest.fixture
    def execution_node_with_namespace_and_partitioning_meta(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
    ) -> Generator:
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(
            dataset_graph, {"email": "customer-1@example.com", "custom_id": "123"}
        )

        yield traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.fixture
    def customer_data(
        self, bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
    ):
        """Fixture to create and clean up test customer data"""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        test_email = "customer-3@example.com"

        # Insert test data
        with connector.client().connect() as connection:
            connection.execute(
                text(
                    """
                INSERT INTO fidesopstest.customer VALUES
                (3, 'customer-3@example.com', 'John Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY), 1, 'custom_id_1', STRUCT('Exampletown' as city, '123' as house, 1 as id, 'NY' as state, 'Example Street' as street, 3 as address_id),
                ['VIP', 'Rewards', 'Premium'],
                [STRUCT('ITEM-1' as item_id, 29.99 as price, '2023-01-15' as purchase_date, ['electronics', 'gadgets'] as item_tags),
                STRUCT('ITEM-2' as item_id, 49.99 as price, '2023-02-20' as purchase_date, ['clothing', 'accessories'] as item_tags)]
                ),
                (4, 'customer-3@example.com', 'John Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY), 2, 'custom_id_2', STRUCT('Exampletown' as city, '4' as house, 2 as id, 'NY' as state, 'Example Lane' as street, 4 as address_id),
                ['Standard', 'New'],
                [STRUCT('ITEM-3' as item_id, 19.99 as price, '2023-03-10' as purchase_date, ['books', 'education'] as item_tags)]
                ),
                (5, 'customer-3@example.com', 'John Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY), 3, 'custom_id_3', STRUCT('Exampletown' as city, '5' as house, 3 as id, 'NY' as state, 'Example Street' as street, 5 as address_id),
                ['Standard', 'New'],
                [STRUCT('ITEM-4' as item_id, 19.99 as price, '2023-04-10' as purchase_date, ['books', 'education'] as item_tags)]
                )
                ;
            """
                )
            )

        yield {
            "email": test_email,
            "name": "John Customer",
            "rows": [
                {
                    "email": "customer-3@example.com",
                    "name": "John Customer",
                    "address_id": 3,
                },
                {
                    "email": "customer-3@example.com",
                    "name": "John Customer",
                    "address_id": 4,
                },
            ],
        }

        # Clean up test data
        try:
            with connector.client().connect() as connection:
                connection.execute(
                    text(
                        """
                    DELETE FROM fidesopstest.customer
                    WHERE email = 'customer-3@example.com'
                """
                    )
                )
        except Exception as exc:
            # Log cleanup errors but don't fail the test
            logger.warning(f"Failed to clean up test data: {exc}")

    def test_query_config(
        self,
        bigquery_example_test_dataset_config: DatasetConfig,
        execution_node,
    ):
        dataset_config = bigquery_example_test_dataset_config
        connector = BigQueryConnector(dataset_config.connection_config)
        query_config = connector.query_config(execution_node)
        assert query_config.namespace_meta is None

    def test_query_config_with_namespace_meta(
        self,
        bigquery_example_test_dataset_config_with_namespace_meta: DatasetConfig,
        execution_node_with_namespace_meta,
    ):
        dataset_config = bigquery_example_test_dataset_config_with_namespace_meta
        connector = BigQueryConnector(dataset_config.connection_config)
        query_config = connector.query_config(execution_node_with_namespace_meta)
        assert query_config.namespace_meta == BigQueryNamespaceMeta(
            **dataset_config.ctl_dataset.fides_meta["namespace"]
        )

    def test_generate_update_partitioned_table(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
    ):
        """Unit test of BigQueryQueryConfig.generate_update specifically for a partitioned table"""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)
        query_config = connector.query_config(
            execution_node_with_namespace_and_partitioning_meta
        )

        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }
        updates = query_config.generate_update(
            row=row,
            policy=erasure_policy,
            request=PrivacyRequest(),
            client=connector.client(),
        )

        assert len(updates) == 2
        stmts = [str(stmt) for stmt in updates]
        assert stmts == [
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `name`=%(name:STRING)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP()",
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `name`=%(name:STRING)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",
        ]

    def test_generate_delete_partitioned_table_with_batched_delete(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        customer_data,
        db,
        mocker,
    ):
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        # Set DELETE masking strategy for the customer collection
        execution_node = execution_node_with_namespace_and_partitioning_meta
        execution_node.collection.masking_strategy_override = MaskingStrategyOverride(
            strategy=MaskingStrategies.DELETE
        )

        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)

        execute_spy = mocker.spy(sqlalchemy.engine.Connection, "execute")

        update_or_delete_ct = connector.mask_data(
            node=execution_node,
            policy=erasure_policy,
            privacy_request=PrivacyRequest(),
            request_task=RequestTask(),
            rows=customer_data["rows"],
        )
        # Delete all 3 customer rows
        assert update_or_delete_ct == 3

        # Verify that we only execute one delete per partition, not per row
        assert execute_spy.call_count == 2

    def test_mask_data_empty_rows_no_execute(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        mocker,
    ):
        """mask_data should be a no-op when given an empty list of rows."""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        # Force DELETE masking strategy to exercise the new batched delete path
        execution_node = execution_node_with_namespace_and_partitioning_meta
        execution_node.collection.masking_strategy_override = MaskingStrategyOverride(
            strategy=MaskingStrategies.DELETE
        )

        execute_spy = mocker.spy(sqlalchemy.engine.Connection, "execute")

        update_or_delete_ct = connector.mask_data(
            node=execution_node,
            policy=erasure_policy,
            privacy_request=PrivacyRequest(),
            request_task=RequestTask(),
            rows=[],
        )

        # Nothing should have been deleted / updated and no SQL should have executed
        assert update_or_delete_ct == 0
        assert execute_spy.call_count == 0

    def test_mask_data_missing_reference_fields_no_execute(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        mocker,
    ):
        """mask_data should not execute deletes when rows lack reference field data."""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        # Force DELETE masking strategy for this test
        execution_node = execution_node_with_namespace_and_partitioning_meta
        execution_node.collection.masking_strategy_override = MaskingStrategyOverride(
            strategy=MaskingStrategies.DELETE
        )

        # A row missing reference fields (e.g. 'email' and 'address_id')
        rows_missing_refs = [
            {
                "email": None,
                "name": "Jane Doe",
                "address_id": None,
            }
        ]

        execute_spy = mocker.spy(sqlalchemy.engine.Connection, "execute")

        update_or_delete_ct = connector.mask_data(
            node=execution_node,
            policy=erasure_policy,
            privacy_request=PrivacyRequest(),
            request_task=RequestTask(),
            rows=rows_missing_refs,
        )

        # No statements should execute because WHERE clause cannot be built
        assert update_or_delete_ct == 0
        assert execute_spy.call_count == 0

    def test_generate_delete_partitioned_table(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
    ):
        """Unit test of BigQueryQueryConfig.generate_delete specifically for a partitioned table"""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)
        query_config = connector.query_config(
            execution_node_with_namespace_and_partitioning_meta
        )

        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }
        deletes = query_config.generate_delete(row=row, client=connector.client())

        assert len(deletes) == 2

        stmts = [str(stmt) for stmt in deletes]
        assert stmts == [
            "DELETE FROM `silken-precinct-284918.fidesopstest.customer` WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP()",
            "DELETE FROM `silken-precinct-284918.fidesopstest.customer` WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",
        ]

    def test_retrieve_partitioned_data(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        policy,
        privacy_request_with_email_identity,
    ):
        """Unit test of BigQueryQueryConfig.retrieve_data specifically for a partitioned table"""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        results = connector.retrieve_data(
            node=execution_node_with_namespace_and_partitioning_meta,
            policy=policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            input_data={"email": ["customer-1@example.com"]},
        )

        assert len(results) == 1
        assert results[0]["email"] == "customer-1@example.com"

    def test_retrieve_partitioned_data_with_multiple_identifying_fields(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        policy,
        privacy_request_with_email_identity,
        loguru_caplog,
    ):
        """Unit test of BigQueryQueryConfig.retrieve_data specifically for a partitioned table with multiple identifying fields"""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        with loguru_caplog.at_level(logging.INFO):
            results = connector.retrieve_data(
                node=execution_node_with_namespace_and_partitioning_meta,
                policy=policy,
                privacy_request=privacy_request_with_email_identity,
                request_task=RequestTask(),
                input_data={
                    "email": ["customer-1@example.com"],
                    "custom_id": ["123"],
                },
            )
            # Check that the correct SQL queries were executed and logged by sqlalchemy.engine.Engine
            # This may be not be the best way to test this, but it's the best I could come up with
            # without modifying the BigQueryConnector class to allow for a SQL queries generation
            # that's decoupled from the actual execution of the queries.
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `silken-precinct-284918.fidesopstest.customer` WHERE (email = %(email)s OR custom_id = %(custom_id)s) AND (`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP())"
                in loguru_caplog.text
            )
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `silken-precinct-284918.fidesopstest.customer` WHERE (email = %(email)s OR custom_id = %(custom_id)s) AND (`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY))"
                in loguru_caplog.text
            )

        assert len(results) == 1
        assert results[0]["email"] == "customer-1@example.com"


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
class TestBigQueryConnectorTimeBasedPartitioning:
    """
    Tests to verify the BigQuery connector with the new TimeBasedPartitioning schema
    """

    @pytest.fixture
    def execution_node_with_namespace_and_time_based_partitioning_meta(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta: DatasetConfig,
    ) -> Generator:
        dataset_config = bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(
            dataset_graph, {"email": "customer-1@example.com", "custom_id": "123"}
        )

        yield traversal.traversal_node_dict[
            CollectionAddress("bigquery_example_test_dataset", "customer")
        ].to_mock_execution_node()

    def test_generate_update_partitioned_table(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_time_based_partitioning_meta,
        erasure_policy,
    ):
        """Unit test of BigQueryQueryConfig.generate_update specifically for a partitioned table using TimeBasedPartitioning"""
        dataset_config = bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta
        connector = BigQueryConnector(dataset_config.connection_config)
        query_config = connector.query_config(
            execution_node_with_namespace_and_time_based_partitioning_meta
        )

        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }
        updates = query_config.generate_update(
            row=row,
            policy=erasure_policy,
            request=PrivacyRequest(),
            client=connector.client(),
        )

        assert len(updates) == 2
        stmts = [str(stmt) for stmt in updates]
        assert stmts == [
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `name`=%(name:STRING)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` >= CURRENT_TIMESTAMP - INTERVAL 2000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 1000 DAY",
            "UPDATE `silken-precinct-284918.fidesopstest.customer` SET `name`=%(name:STRING)s WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 1000 DAY AND `created` <= CURRENT_TIMESTAMP",
        ]

    def test_generate_delete_partitioned_table(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_time_based_partitioning_meta,
        erasure_policy,
    ):
        """Unit test of BigQueryQueryConfig.generate_delete specifically for a partitioned table using TimeBasedPartitioning"""
        dataset_config = bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta
        connector = BigQueryConnector(dataset_config.connection_config)
        query_config = connector.query_config(
            execution_node_with_namespace_and_time_based_partitioning_meta
        )

        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }
        deletes = query_config.generate_delete(row=row, client=connector.client())

        assert len(deletes) == 2

        stmts = [str(stmt) for stmt in deletes]
        assert stmts == [
            "DELETE FROM `silken-precinct-284918.fidesopstest.customer` WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` >= CURRENT_TIMESTAMP - INTERVAL 2000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 1000 DAY",
            "DELETE FROM `silken-precinct-284918.fidesopstest.customer` WHERE `silken-precinct-284918.fidesopstest.customer`.`email` = %(email_1:STRING)s AND `created` > CURRENT_TIMESTAMP - INTERVAL 1000 DAY AND `created` <= CURRENT_TIMESTAMP",
        ]

    def test_retrieve_partitioned_data(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_time_based_partitioning_meta,
        policy,
        privacy_request_with_email_identity,
    ):
        """Unit test of BigQueryQueryConfig.retrieve_data specifically for a partitioned table using TimeBasedPartitioning"""
        dataset_config = bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta
        connector = BigQueryConnector(dataset_config.connection_config)

        results = connector.retrieve_data(
            node=execution_node_with_namespace_and_time_based_partitioning_meta,
            policy=policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            input_data={"email": ["customer-1@example.com"]},
        )

        assert len(results) == 1
        assert results[0]["email"] == "customer-1@example.com"

    def test_retrieve_partitioned_data_with_multiple_identifying_fields(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_time_based_partitioning_meta,
        policy,
        privacy_request_with_email_identity,
        loguru_caplog,
    ):
        """Unit test of BigQueryQueryConfig.retrieve_data specifically for a partitioned table with multiple identifying fields using TimeBasedPartitioning"""
        dataset_config = bigquery_example_test_dataset_config_with_namespace_and_time_based_partitioning_meta
        connector = BigQueryConnector(dataset_config.connection_config)

        with loguru_caplog.at_level(logging.INFO):
            results = connector.retrieve_data(
                node=execution_node_with_namespace_and_time_based_partitioning_meta,
                policy=policy,
                privacy_request=privacy_request_with_email_identity,
                request_task=RequestTask(),
                input_data={
                    "email": ["customer-1@example.com"],
                    "custom_id": ["123"],
                },
            )
            # Check that the correct SQL queries were executed and logged by sqlalchemy.engine.Engine
            # This may be not be the best way to test this, but it's the best I could come up with
            # without modifying the BigQueryConnector class to allow for a SQL queries generation
            # that's decoupled from the actual execution of the queries.
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `silken-precinct-284918.fidesopstest.customer` WHERE (email = %(email)s OR custom_id = %(custom_id)s) AND (`created` >= CURRENT_TIMESTAMP - INTERVAL 2000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 1000 DAY)"
                in loguru_caplog.text
            )
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT address_id, created, custom_id, email, extra_address_data, id, name, purchase_history, tags FROM `silken-precinct-284918.fidesopstest.customer` WHERE (email = %(email)s OR custom_id = %(custom_id)s) AND (`created` >= CURRENT_TIMESTAMP - INTERVAL 2000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 1000 DAY)"
                in loguru_caplog.text
            )

        assert len(results) == 1
        assert results[0]["email"] == "customer-1@example.com"
