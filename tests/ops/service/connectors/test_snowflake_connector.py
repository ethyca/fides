import base64
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fideslang.models import Dataset
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.schemas.namespace_meta.snowflake_namespace_meta import (
    SnowflakeNamespaceMeta,
)
from fides.api.service.connectors.snowflake_connector import SnowflakeConnector


def _make_base64_der_key() -> str:
    """Produce a base64-encoded DER private key string (Snowflake str format)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return base64.b64encode(der).decode("ascii")


def _make_pem_key() -> str:
    """Produce a PEM-format private key string."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")


class TestSnowflakeConnectorGetConnectArgs:
    """Unit tests for get_connect_args (private key format for Snowflake)."""

    def test_base64_der_passed_through_stripped(self):
        """Base64 DER string is stripped of whitespace and passed as str."""
        key = _make_base64_der_key()
        config = MagicMock()
        config.secrets = {
            "account_identifier": "test",
            "user_login_name": "user",
            "private_key": key,
            "warehouse_name": "wh",
        }
        connector = SnowflakeConnector(config)
        connect_args = connector.get_connect_args()
        assert connect_args["private_key"] == key

    def test_base64_der_with_whitespace_stripped(self):
        """Base64 DER with newlines is normalized to single line."""
        key = _make_base64_der_key()
        wrapped = key[:32] + "\n" + key[32:]
        config = MagicMock()
        config.secrets = {
            "account_identifier": "test",
            "user_login_name": "user",
            "private_key": wrapped,
            "warehouse_name": "wh",
        }
        connector = SnowflakeConnector(config)
        connect_args = connector.get_connect_args()
        assert connect_args["private_key"] == key
        assert "\n" not in connect_args["private_key"]

    def test_pem_converted_to_base64_der_string(self):
        """PEM key is converted to base64-encoded DER string for Snowflake."""
        pem = _make_pem_key()
        config = MagicMock()
        config.secrets = {
            "account_identifier": "test",
            "user_login_name": "user",
            "private_key": pem,
            "warehouse_name": "wh",
        }
        connector = SnowflakeConnector(config)
        connect_args = connector.get_connect_args()
        assert "private_key" in connect_args
        # Should be base64 string (no PEM headers)
        pk = connect_args["private_key"]
        assert "-----BEGIN" not in pk
        assert "-----END" not in pk
        # Should decode to valid DER
        der = base64.b64decode(pk)
        key = serialization.load_der_private_key(
            der, password=None, backend=default_backend()
        )
        assert key is not None

    def test_no_private_key_no_connect_args_key(self):
        """When no private_key in secrets, connect_args has no private_key."""
        config = MagicMock()
        config.secrets = {
            "account_identifier": "test",
            "user_login_name": "user",
            "password": "secret",
            "warehouse_name": "wh",
        }
        connector = SnowflakeConnector(config)
        connect_args = connector.get_connect_args()
        assert "private_key" not in connect_args


@pytest.fixture
def execution_node_with_namespace_meta(
    snowflake_example_test_dataset_config_with_namespace_meta: DatasetConfig,
) -> Generator:
    dataset_config = snowflake_example_test_dataset_config_with_namespace_meta
    graph_dataset = convert_dataset_to_graph(
        Dataset.model_validate(dataset_config.ctl_dataset),
        dataset_config.connection_config.key,
    )
    dataset_graph = DatasetGraph(graph_dataset)
    traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

    yield traversal.traversal_node_dict[
        CollectionAddress("snowflake_example_test_dataset", "customer")
    ].to_mock_execution_node()


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
class TestSnowflakeConnector:
    """
    Tests to verify that the query_config method of SnowflakeConnector
    correctly retrieves namespace metadata from the dataset (if available).
    """

    @pytest.fixture
    def execution_node(
        self, snowflake_example_test_dataset_config: DatasetConfig
    ) -> Generator:
        dataset_config = snowflake_example_test_dataset_config
        graph_dataset = convert_dataset_to_graph(
            Dataset.model_validate(dataset_config.ctl_dataset),
            dataset_config.connection_config.key,
        )
        dataset_graph = DatasetGraph(graph_dataset)
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        yield traversal.traversal_node_dict[
            CollectionAddress("snowflake_example_test_dataset", "customer")
        ].to_mock_execution_node()

    def test_query_config(
        self,
        snowflake_example_test_dataset_config: DatasetConfig,
        execution_node,
    ):
        dataset_config = snowflake_example_test_dataset_config
        connector = SnowflakeConnector(dataset_config.connection_config)
        query_config = connector.query_config(execution_node)
        assert query_config.namespace_meta is None

    def test_query_config_with_namespace_meta(
        self,
        snowflake_example_test_dataset_config_with_namespace_meta: DatasetConfig,
        execution_node_with_namespace_meta,
    ):
        dataset_config = snowflake_example_test_dataset_config_with_namespace_meta
        connector = SnowflakeConnector(dataset_config.connection_config)
        query_config = connector.query_config(execution_node_with_namespace_meta)
        assert query_config.namespace_meta == SnowflakeNamespaceMeta(
            **dataset_config.ctl_dataset.fides_meta["namespace"]
        )


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
class TestSnowflakeConnectorTableExists:
    def test_table_exists(
        self,
        snowflake_example_test_dataset_config_with_namespace_meta: DatasetConfig,
        execution_node_with_namespace_meta,
    ):
        # Test with actual connection using proper qualified table names
        dataset_config = snowflake_example_test_dataset_config_with_namespace_meta
        connector = SnowflakeConnector(dataset_config.connection_config)

        # Use the connector's method to get the proper qualified table name
        qualified_table_name = connector.get_qualified_table_name(
            execution_node_with_namespace_meta
        )
        assert connector.table_exists(qualified_table_name)

        # Test with a nonexistent table using the same schema but different table name
        assert not connector.table_exists('"FIDESOPS_TEST"."TEST"."nonexistent_table"')
