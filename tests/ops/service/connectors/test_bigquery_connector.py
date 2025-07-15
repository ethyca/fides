import logging
from typing import Generator
from unittest.mock import MagicMock

import pytest
import sqlalchemy
from fideslang.models import Dataset, MaskingStrategies, MaskingStrategyOverride
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Engine

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
    def execution_node_with_namespace_and_partitioning_meta_and_multiple_identities(
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
            dataset_graph,
            {
                "email": [
                    "customer-3@example.com",
                    "customer-4@example.com",
                    "customer-5@example.com",
                ],
                "custom_id": ["custom_id_3", "custom_id_4", "custom_id_5"],
            },
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
                {
                    "email": "customer-3@example.com",
                    "name": "John Customer",
                    "address_id": 5,
                },
            ],
        }

        # Clean up test data
        try:
            with connector.client().connect() as connection:
                connection.execute(
                    text(
                        "DELETE FROM fidesopstest.customer WHERE email = 'customer-3@example.com'"
                    )
                )
        except Exception as exc:
            # Log cleanup errors but don't fail the test
            logger.warning(f"Failed to clean up test data: {exc}")

    @pytest.fixture
    def multiple_customer_data(
        self, bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
    ):
        """Fixture to create and clean up test customer data"""
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        # Insert test data
        with connector.client().connect() as connection:
            connection.execute(
                text(
                    """
                INSERT INTO fidesopstest.customer VALUES
                (3, 'customer-3@example.com', 'John Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY), 1, 'custom_id_3', STRUCT('Exampletown' as city, '123' as house, 1 as id, 'NY' as state, 'Example Street' as street, 3 as address_id),
                ['VIP', 'Rewards', 'Premium'],
                [STRUCT('ITEM-1' as item_id, 29.99 as price, '2023-01-15' as purchase_date, ['electronics', 'gadgets'] as item_tags),
                STRUCT('ITEM-2' as item_id, 49.99 as price, '2023-02-20' as purchase_date, ['clothing', 'accessories'] as item_tags)]
                ),
                (4, 'customer-4@example.com', 'Jon Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY), 2, 'custom_id_4', STRUCT('Exampletown' as city, '4' as house, 2 as id, 'NY' as state, 'Example Lane' as street, 4 as address_id),
                ['Standard', 'New'],
                [STRUCT('ITEM-3' as item_id, 19.99 as price, '2023-03-10' as purchase_date, ['books', 'education'] as item_tags)]
                ),
                (5, 'customer-5@example.com', 'Jonny Customer', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY), 3, 'custom_id_5', STRUCT('Exampletown' as city, '5' as house, 3 as id, 'NY' as state, 'Example Street' as street, 5 as address_id),
                ['Standard', 'New'],
                [STRUCT('ITEM-4' as item_id, 19.99 as price, '2023-04-10' as purchase_date, ['books', 'education'] as item_tags)]
                )
                ;
            """
                )
            )

        yield {
            "emails": [
                "customer-3@example.com",
                "customer-4@example.com",
                "customer-5@example.com",
            ],
            "custom_ids": ["custom_id_3", "custom_id_4", "custom_id_5"],
            "name": "John Customer",
            "rows": [
                {
                    "email": "customer-3@example.com",
                    "name": "John Customer",
                    "address_id": 3,
                },
                {
                    "email": "customer-4@example.com",
                    "name": "Jon Customer",
                    "address_id": 4,
                },
                {
                    "email": "customer-5@example.com",
                    "name": "Jonny Customer",
                    "address_id": 5,
                },
            ],
        }

        # Clean up test data
        try:
            with connector.client().connect() as connection:
                connection.execute(
                    text(
                        "DELETE FROM fidesopstest.customer WHERE email in ('customer-3@example.com', 'customer-4@example.com', 'customer-5@example.com')"
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
            input_data={"email": ["customer-3@example.com"], "address_id": [3, 4, 5]},
        )
        # Delete all 3 customer rows
        assert update_or_delete_ct == 3

        # Verify that we only execute one delete per partition, not per row
        assert execute_spy.call_count == 2

    def test_generate_delete_partitioned_table_with_batched_delete_multiple_identities(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta_and_multiple_identities,
        erasure_policy,
        multiple_customer_data,
        db,
        mocker,
    ):
        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        # Set DELETE masking strategy for the customer collection
        execution_node = (
            execution_node_with_namespace_and_partitioning_meta_and_multiple_identities
        )
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
            rows=multiple_customer_data["rows"],
            input_data={
                "email": multiple_customer_data["emails"],
                "custom_id": multiple_customer_data["custom_ids"],
            },
        )
        # Delete all 3 customer rows
        assert update_or_delete_ct == 3

        # Verify that we only execute one delete per partition, not per row
        assert execute_spy.call_count == 2

    def test_mask_data_missing_input_data(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        mocker,
    ):
        """mask_data should be a no-op when given missing input data"""
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

        deletes = query_config.generate_delete(
            connector.client(),
            input_data={"email": ["customer-1@example.com"], "address_id": [1]},
        )

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
                    "custom id": ["123"],
                },
            )
            # Check that the correct SQL queries were executed and logged by sqlalchemy.engine.Engine
            # This may be not be the best way to test this, but it's the best I could come up with
            # without modifying the BigQueryConnector class to allow for a SQL queries generation
            # that's decoupled from the actual execution of the queries.
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT `address_id`, `created`, `custom id`, `email`, `extra_address_data`, `id`, `name`, `purchase_history`, `tags` FROM `silken-precinct-284918.fidesopstest.customer` WHERE (`email` = %(email)s OR `custom id` = %(custom_id)s) AND (`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP())"
                in loguru_caplog.text
            )
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT `address_id`, `created`, `custom id`, `email`, `extra_address_data`, `id`, `name`, `purchase_history`, `tags` FROM `silken-precinct-284918.fidesopstest.customer` WHERE (`email` = %(email)s OR `custom id` = %(custom_id)s) AND (`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY))"
                in loguru_caplog.text
            )

        assert len(results) == 1
        assert results[0]["email"] == "customer-1@example.com"

    def test_mask_data_sql_dry_run_enabled(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        privacy_request_with_email_identity,
        mocker,
        loguru_caplog,
        db,
    ):
        """Test that when sql_dry_run is enabled, DELETE statements are logged instead of executed"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.erasure.value}}
        )
        db.commit()

        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        execution_node = execution_node_with_namespace_and_partitioning_meta
        execution_node.collection.masking_strategy_override = MaskingStrategyOverride(
            strategy=MaskingStrategies.DELETE
        )

        execute_spy = mocker.spy(sqlalchemy.engine.Connection, "execute")

        update_or_delete_ct = connector.mask_data(
            node=execution_node,
            policy=erasure_policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            rows=[{"email": "customer-1@example.com"}],
            input_data={"email": ["customer-1@example.com"]},
        )

        assert execute_spy.call_count == 0
        assert update_or_delete_ct == 0
        assert "SQL DRY RUN - Would execute SQL:" in loguru_caplog.text

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
        db.commit()

    def test_mask_data_sql_dry_run_disabled(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        privacy_request_with_email_identity,
        mocker,
        loguru_caplog,
        db,
    ):
        """Test that when sql_dry_run is disabled, DELETE statements are actually executed"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
        db.commit()

        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        execution_node = execution_node_with_namespace_and_partitioning_meta
        execution_node.collection.masking_strategy_override = MaskingStrategyOverride(
            strategy=MaskingStrategies.DELETE
        )

        execute_spy = mocker.spy(sqlalchemy.engine.Connection, "execute")

        update_or_delete_ct = connector.mask_data(
            node=execution_node,
            policy=erasure_policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            rows=[{"email": "customer-3@example.com"}],
            input_data={"email": ["customer-3@example.com"]},
        )

        assert execute_spy.call_count > 0
        assert update_or_delete_ct >= 0
        assert "SQL DRY RUN - Would execute SQL:" not in loguru_caplog.text

    def test_sql_dry_run_enabled_comprehensive(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        privacy_request_with_email_identity,
        mocker,
        loguru_caplog,
        db,
    ):
        """Test that when sql_dry_run is enabled, both SELECT and DELETE statements are logged instead of executed"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.erasure.value}}
        )
        db.commit()

        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        execute_spy = mocker.spy(sqlalchemy.engine.Connection, "execute")

        # Test SELECT operations (retrieve_data) - in erasure mode, SELECT should execute normally
        results = connector.retrieve_data(
            node=execution_node_with_namespace_and_partitioning_meta,
            policy=privacy_request_with_email_identity.policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            input_data={"email": ["customer-1@example.com"]},
        )

        # In erasure mode, SELECT should return actual results (not dry run)
        assert len(results) > 0
        assert results[0]["email"] == "customer-1@example.com"

        # Test DELETE operations (mask_data) - in erasure mode, DELETE should be dry run
        execution_node_with_namespace_and_partitioning_meta.collection.masking_strategy_override = MaskingStrategyOverride(
            strategy=MaskingStrategies.DELETE
        )

        loguru_caplog.clear()  # Clear previous logs
        execute_count_before_mask = execute_spy.call_count

        update_or_delete_ct = connector.mask_data(
            node=execution_node_with_namespace_and_partitioning_meta,
            policy=erasure_policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            rows=[{"email": "customer-1@example.com"}],
            input_data={"email": ["customer-1@example.com"]},
        )

        # In erasure mode, DELETE should be dry run (no actual execution, zero affected rows)
        assert update_or_delete_ct == 0
        assert "SQL DRY RUN - Would execute SQL:" in loguru_caplog.text
        # No additional execute calls should have been made for the DELETE operation
        assert execute_spy.call_count == execute_count_before_mask

        # Clean up
        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
        db.commit()

    def test_sql_dry_run_disabled_comprehensive(
        self,
        bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta: DatasetConfig,
        execution_node_with_namespace_and_partitioning_meta,
        erasure_policy,
        privacy_request_with_email_identity,
        mocker,
        loguru_caplog,
        db,
    ):
        """Test that when sql_dry_run is disabled, both SELECT and DELETE statements are executed normally"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
        db.commit()

        dataset_config = (
            bigquery_example_test_dataset_config_with_namespace_and_partitioning_meta
        )
        connector = BigQueryConnector(dataset_config.connection_config)

        execute_spy = mocker.spy(sqlalchemy.engine.Connection, "execute")

        # Test SELECT operations (retrieve_data)
        results = connector.retrieve_data(
            node=execution_node_with_namespace_and_partitioning_meta,
            policy=privacy_request_with_email_identity.policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            input_data={"email": ["customer-1@example.com"]},
        )

        # In normal mode, SELECT should return actual results
        assert isinstance(results, list)
        assert execute_spy.call_count > 0

        # Reset spy count for next test
        execute_spy.reset_mock()

        # Test DELETE operations (mask_data)
        execution_node = execution_node_with_namespace_and_partitioning_meta
        execution_node.collection.masking_strategy_override = MaskingStrategyOverride(
            strategy=MaskingStrategies.DELETE
        )

        update_or_delete_ct = connector.mask_data(
            node=execution_node,
            policy=erasure_policy,
            privacy_request=privacy_request_with_email_identity,
            request_task=RequestTask(),
            rows=[{"email": "customer-3@example.com"}],
            input_data={"email": ["customer-3@example.com"]},
        )

        # In normal mode, operations should execute
        assert execute_spy.call_count > 0
        assert update_or_delete_ct >= 0

        # Check that we don't see sql_dry_run logging
        assert "SQL DRY RUN - Would execute SQL:" not in loguru_caplog.text

    def test_execute_statements_with_sql_dry_run_enabled(self, loguru_caplog):
        """Test _execute_statements_with_sql_dry_run when dry run is enabled"""
        # Create a mock connector
        mock_connection_config = MagicMock()
        mock_connection_config.secrets = {"keyfile_creds": "fake_creds"}

        connector = BigQueryConnector(mock_connection_config)

        # Mock statements
        mock_statements = [
            text("DELETE FROM table1 WHERE id = 1"),
            text("DELETE FROM table2 WHERE id = 2"),
        ]

        # Mock client
        mock_client = MagicMock(spec=Engine)

        # Call the function with sql_dry_run enabled
        result = connector._execute_statements_with_sql_dry_run(
            statements=mock_statements,
            sql_dry_run_enabled=True,
            client=mock_client,
        )

        # Assertions
        assert result == 0  # Should return 0 affected rows in dry run mode
        assert "SQL DRY RUN - Would execute SQL:" in loguru_caplog.text
        assert "DELETE FROM table1 WHERE id = 1" in loguru_caplog.text
        assert "DELETE FROM table2 WHERE id = 2" in loguru_caplog.text

        # Should not attempt to connect to database
        mock_client.connect.assert_not_called()

    def test_execute_statements_with_sql_dry_run_disabled(self):
        """Test _execute_statements_with_sql_dry_run when dry run is disabled"""
        # Create a mock connector
        mock_connection_config = MagicMock()
        mock_connection_config.secrets = {"keyfile_creds": "fake_creds"}

        connector = BigQueryConnector(mock_connection_config)

        # Mock statements
        mock_statements = [
            text("DELETE FROM table1 WHERE id = 1"),
            text("DELETE FROM table2 WHERE id = 2"),
        ]

        # Mock client and connection
        mock_client = MagicMock(spec=Engine)
        mock_connection = MagicMock()
        mock_client.connect.return_value.__enter__.return_value = mock_connection

        # Mock execute results
        mock_result1 = MagicMock()
        mock_result1.rowcount = 3
        mock_result2 = MagicMock()
        mock_result2.rowcount = 5
        mock_connection.execute.side_effect = [mock_result1, mock_result2]

        # Call the function with sql_dry_run disabled
        result = connector._execute_statements_with_sql_dry_run(
            statements=mock_statements,
            sql_dry_run_enabled=False,
            client=mock_client,
        )

        # Assertions
        assert result == 8  # Should return sum of affected rows (3 + 5)
        mock_client.connect.assert_called_once()
        assert mock_connection.execute.call_count == 2
        mock_connection.execute.assert_any_call(mock_statements[0])
        mock_connection.execute.assert_any_call(mock_statements[1])

    def test_execute_statements_with_sql_dry_run_empty_statements(self):
        """Test _execute_statements_with_sql_dry_run with empty statements list"""
        # Create a mock connector
        mock_connection_config = MagicMock()
        mock_connection_config.secrets = {"keyfile_creds": "fake_creds"}

        connector = BigQueryConnector(mock_connection_config)

        # Mock client
        mock_client = MagicMock(spec=Engine)

        # Call the function with empty statements
        result = connector._execute_statements_with_sql_dry_run(
            statements=[],
            sql_dry_run_enabled=False,
            client=mock_client,
        )

        # Assertions
        assert result == 0  # Should return 0 for empty statements
        mock_client.connect.assert_not_called()


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

        deletes = query_config.generate_delete(
            connector.client(),
            input_data={"email": ["customer-1@example.com"], "address_id": [1]},
        )
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
                    "custom id": ["123"],
                },
            )
            # Check that the correct SQL queries were executed and logged by sqlalchemy.engine.Engine
            # This may be not be the best way to test this, but it's the best I could come up with
            # without modifying the BigQueryConnector class to allow for a SQL queries generation
            # that's decoupled from the actual execution of the queries.
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT `address_id`, `created`, `custom id`, `email`, `extra_address_data`, `id`, `name`, `purchase_history`, `tags` FROM `silken-precinct-284918.fidesopstest.customer` WHERE (`email` = %(email)s OR `custom id` = %(custom_id)s) AND (`created` >= CURRENT_TIMESTAMP - INTERVAL 2000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 1000 DAY)"
                in loguru_caplog.text
            )
            assert (
                "INFO     sqlalchemy.engine.Engine:log.py:117 SELECT `address_id`, `created`, `custom id`, `email`, `extra_address_data`, `id`, `name`, `purchase_history`, `tags` FROM `silken-precinct-284918.fidesopstest.customer` WHERE (`email` = %(email)s OR `custom id` = %(custom_id)s) AND (`created` >= CURRENT_TIMESTAMP - INTERVAL 2000 DAY AND `created` <= CURRENT_TIMESTAMP - INTERVAL 1000 DAY)"
                in loguru_caplog.text
            )

        assert len(results) == 1
        assert results[0]["email"] == "customer-1@example.com"


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
class TestBigQueryConnectorTableExists:
    def test_table_exists(
        self, bigquery_example_test_dataset_config_with_namespace_meta: DatasetConfig
    ):
        # Test with actual connection
        dataset_config = bigquery_example_test_dataset_config_with_namespace_meta
        connector = BigQueryConnector(dataset_config.connection_config)
        assert connector.table_exists("silken-precinct-284918.fidesopstest.customer")
        assert not connector.table_exists(
            "silken-precinct-284918.fidesopstest.nonexistent_table"
        )
