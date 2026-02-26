from copy import deepcopy
from typing import Dict, Generator, List

import pytest
from fideslang.models import Dataset
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.graph.config import CollectionAddress
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.namespace_meta.google_cloud_sql_postgres_namespace_meta import (
    GoogleCloudSQLPostgresNamespaceMeta,
)
from fides.api.service.connectors.query_configs.google_cloud_postgres_query_config import (
    GoogleCloudSQLPostgresQueryConfig,
)


@pytest.mark.integration
@pytest.mark.integration_postgres
class TestGoogleCloudSQLPostgresQueryConfig:
    """
    Verify that GoogleCloudSQLPostgresQueryConfig correctly adjusts the table
    name based on the available namespace info in the dataset's fides_meta.
    """

    @pytest.fixture
    def gcs_postgres_dataset_config_with_namespace_meta(
        self,
        connection_config: ConnectionConfig,
        db: Session,
        example_datasets: List[Dict],
    ) -> Generator:
        postgres_dataset = deepcopy(example_datasets[0])
        postgres_dataset["fides_meta"] = {"namespace": {"schema": "billing"}}
        fides_key = postgres_dataset["fides_key"]

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, postgres_dataset)

        dataset_config = DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": fides_key,
                "ctl_dataset_id": ctl_dataset.id,
            },
        )
        yield dataset_config
        dataset_config.delete(db=db)
        ctl_dataset.delete(db=db)

    @pytest.fixture
    def execution_node(
        self,
        gcs_postgres_dataset_config_with_namespace_meta: DatasetConfig,
    ) -> Generator:
        dataset_config = gcs_postgres_dataset_config_with_namespace_meta
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.fixture
    def address_node(
        self,
        gcs_postgres_dataset_config_with_namespace_meta: DatasetConfig,
    ) -> Generator:
        dataset_config = gcs_postgres_dataset_config_with_namespace_meta
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "address")
        ].to_mock_execution_node()

    @pytest.mark.parametrize(
        "namespace_meta, expected_query",
        [
            (
                GoogleCloudSQLPostgresNamespaceMeta(schema="billing"),
                'SELECT address_id, created, email, id, name FROM "billing"."customer" WHERE (email = :email)',
            ),
            (
                GoogleCloudSQLPostgresNamespaceMeta(
                    database_name="prod_db", schema="billing"
                ),
                'SELECT address_id, created, email, id, name FROM "prod_db"."billing"."customer" WHERE (email = :email)',
            ),
            # Namespace meta will be a dict / JSON when retrieved from the DB
            (
                {"schema": "billing"},
                'SELECT address_id, created, email, id, name FROM "billing"."customer" WHERE (email = :email)',
            ),
            (
                {
                    "schema": "billing",
                    "connection_type": "google_cloud_sql_postgres",
                },
                'SELECT address_id, created, email, id, name FROM "billing"."customer" WHERE (email = :email)',
            ),
            (
                None,
                'SELECT address_id, created, email, id, name FROM "customer" WHERE (email = :email)',
            ),
        ],
    )
    def test_generate_query_with_namespace_meta(
        self, execution_node: ExecutionNode, namespace_meta, expected_query
    ):
        query_config = GoogleCloudSQLPostgresQueryConfig(execution_node, namespace_meta)
        assert (
            query_config.generate_query(
                input_data={"email": ["customer-1@example.com"]}
            ).text
            == expected_query
        )

    def test_generate_query_with_invalid_namespace_meta(
        self, execution_node: ExecutionNode
    ):
        with pytest.raises(ValidationError) as exc:
            GoogleCloudSQLPostgresQueryConfig(
                execution_node,
                GoogleCloudSQLPostgresNamespaceMeta(database_name="some_db"),
            )
        assert "Field required" in str(exc)

    def test_generate_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
    ):
        """Test non-namespaced update statement uses quoted table name."""
        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmt = GoogleCloudSQLPostgresQueryConfig(
            address_node
        ).generate_update_stmt(
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
        )
        assert (
            str(update_stmt)
            == 'UPDATE "address" SET city = :masked_city, house = :masked_house, state = :masked_state, street = :masked_street, zip = :masked_zip WHERE id = :id'
        )

    def test_generate_namespaced_update_stmt(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
    ):
        """Test namespaced update statement prepends schema to table name."""
        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmt = GoogleCloudSQLPostgresQueryConfig(
            address_node,
            GoogleCloudSQLPostgresNamespaceMeta(schema="billing"),
        ).generate_update_stmt(
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
        )
        assert (
            str(update_stmt)
            == 'UPDATE "billing"."address" SET city = :masked_city, house = :masked_house, state = :masked_state, street = :masked_street, zip = :masked_zip WHERE id = :id'
        )

    def test_generate_namespaced_update_stmt_with_database(
        self,
        db,
        address_node,
        erasure_policy,
        privacy_request,
    ):
        """Test namespaced update with database_name prepends database.schema."""
        erasure_policy.rules[0].targets[0].data_category = "user"
        erasure_policy.rules[0].targets[0].save(db)
        update_stmt = GoogleCloudSQLPostgresQueryConfig(
            address_node,
            GoogleCloudSQLPostgresNamespaceMeta(
                database_name="prod_db", schema="billing"
            ),
        ).generate_update_stmt(
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
        )
        assert (
            str(update_stmt)
            == 'UPDATE "prod_db"."billing"."address" SET city = :masked_city, house = :masked_house, state = :masked_state, street = :masked_street, zip = :masked_zip WHERE id = :id'
        )
