from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel
from sqlalchemy import text

from fides.api.graph.execution import ExecutionNode
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.sql_connector import SQLConnector


class MockSecretsSchema(BaseModel):
    """Minimal secrets schema for testing"""

    pass


class MockSQLConnector(SQLConnector):
    """Mock SQL connector for testing base functionality"""

    secrets_schema = MockSecretsSchema

    def build_uri(self):
        return "sqlite:///:memory:"


class TestSQLConnectorDryRun:
    """Test sql_dry_run functionality for the base SQLConnector class"""

    @pytest.fixture
    def mock_connection_config(self):
        """Create a mock connection config"""
        mock_config = MagicMock()
        mock_config.secrets = {}
        return mock_config

    @pytest.fixture
    def mock_connector(self, mock_connection_config):
        """Create a mock SQL connector"""
        connector = MockSQLConnector(mock_connection_config)
        return connector

    @pytest.fixture
    def mock_execution_node(self):
        """Create a mock execution node"""
        node = MagicMock(spec=ExecutionNode)
        node.address = MagicMock()
        node.address.collection = "test_table"

        # Mock the collection attribute and its methods
        node.collection = MagicMock()
        node.collection.custom_request_fields.return_value = ["field1", "field2"]

        return node

    @pytest.fixture
    def mock_privacy_request(self):
        """Create a mock privacy request"""
        return MagicMock(spec=PrivacyRequest)

    @pytest.fixture
    def mock_request_task(self):
        """Create a mock request task"""
        return MagicMock(spec=RequestTask)

    def test_retrieve_data_sql_dry_run_enabled(
        self,
        mock_connector,
        mock_execution_node,
        mock_privacy_request,
        mock_request_task,
        loguru_caplog,
        db,
    ):
        """Test that retrieve_data logs SQL instead of executing when sql_dry_run is enabled"""
        from fides.api.models.application_config import ApplicationConfig

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": True}})
        db.commit()

        mock_query_config = MagicMock()
        mock_query_config.generate_query.return_value = text(
            "SELECT * FROM test_table WHERE id = :id"
        )

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
        ):

            results = mock_connector.retrieve_data(
                node=mock_execution_node,
                policy=MagicMock(),
                privacy_request=mock_privacy_request,
                request_task=mock_request_task,
                input_data={"id": [1, 2, 3]},
            )

            assert results == []
            assert "SQL DRY RUN - Would execute SQL:" in loguru_caplog.text
            mock_client.return_value.connect.assert_not_called()

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": False}})
        db.commit()

    def test_retrieve_data_sql_dry_run_disabled(
        self,
        mock_connector,
        mock_execution_node,
        mock_privacy_request,
        mock_request_task,
        loguru_caplog,
        db,
    ):
        """Test that retrieve_data executes SQL normally when sql_dry_run is disabled"""
        from fides.api.models.application_config import ApplicationConfig

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": False}})
        db.commit()

        mock_query_config = MagicMock()
        mock_query_config.generate_query.return_value = text(
            "SELECT * FROM test_table WHERE id = :id"
        )
        mock_query_config.partitioning = None

        mock_connection = MagicMock()
        mock_results = MagicMock()
        mock_connection.execute.return_value = mock_results

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
            patch.object(
                mock_connector, "cursor_result_to_rows", return_value=[{"id": 1}]
            ),
            patch.object(mock_connector, "set_schema"),
        ):

            mock_client.return_value.connect.return_value.__enter__.return_value = (
                mock_connection
            )

            results = mock_connector.retrieve_data(
                node=mock_execution_node,
                policy=MagicMock(),
                privacy_request=mock_privacy_request,
                request_task=mock_request_task,
                input_data={"id": [1, 2, 3]},
            )

            assert results == [{"id": 1}]
            assert "SQL DRY RUN - Would execute SQL:" not in loguru_caplog.text
            mock_connection.execute.assert_called_once()

    def test_execute_standalone_retrieval_query_sql_dry_run_enabled(
        self,
        mock_connector,
        mock_execution_node,
        loguru_caplog,
        db,
    ):
        """Test that execute_standalone_retrieval_query logs SQL instead of executing when sql_dry_run is enabled"""
        from fides.api.models.application_config import ApplicationConfig

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": True}})
        db.commit()

        mock_query_config = MagicMock()
        mock_query_config.generate_raw_query.return_value = text(
            "SELECT field1, field2 FROM test_table WHERE id = :id"
        )

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
        ):

            results = mock_connector.execute_standalone_retrieval_query(
                node=mock_execution_node,
                fields=["field1", "field2"],
                filters={"id": [1, 2, 3]},
            )

            assert results == []
            assert "SQL DRY RUN - Would execute SQL:" in loguru_caplog.text
            mock_client.return_value.connect.assert_not_called()

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": False}})
        db.commit()

    def test_mask_data_sql_dry_run_enabled(
        self,
        mock_connector,
        mock_execution_node,
        mock_privacy_request,
        mock_request_task,
        loguru_caplog,
        db,
    ):
        """Test that mask_data logs SQL instead of executing when sql_dry_run is enabled"""
        from fides.api.models.application_config import ApplicationConfig

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": True}})
        db.commit()

        mock_query_config = MagicMock()
        mock_query_config.generate_update_stmt.return_value = text(
            "UPDATE test_table SET name = NULL WHERE id = :id"
        )

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
        ):

            affected_rows = mock_connector.mask_data(
                node=mock_execution_node,
                policy=MagicMock(),
                privacy_request=mock_privacy_request,
                request_task=mock_request_task,
                rows=[{"id": 1, "name": "test"}],
            )

            assert affected_rows == 0
            assert "SQL DRY RUN - Would execute SQL:" in loguru_caplog.text
            mock_client.return_value.connect.assert_not_called()

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": False}})
        db.commit()

    def test_mask_data_sql_dry_run_disabled(
        self,
        mock_connector,
        mock_execution_node,
        mock_privacy_request,
        mock_request_task,
        loguru_caplog,
        db,
    ):
        """Test that mask_data executes SQL normally when sql_dry_run is disabled"""
        from fides.api.models.application_config import ApplicationConfig

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": False}})
        db.commit()

        mock_query_config = MagicMock()
        mock_query_config.generate_update_stmt.return_value = text(
            "UPDATE test_table SET name = NULL WHERE id = :id"
        )

        mock_connection = MagicMock()
        mock_results = MagicMock()
        mock_results.rowcount = 1
        mock_connection.execute.return_value = mock_results

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
            patch.object(mock_connector, "set_schema"),
        ):

            mock_client.return_value.connect.return_value.__enter__.return_value = (
                mock_connection
            )

            affected_rows = mock_connector.mask_data(
                node=mock_execution_node,
                policy=MagicMock(),
                privacy_request=mock_privacy_request,
                request_task=mock_request_task,
                rows=[{"id": 1, "name": "test"}],
            )

            assert affected_rows == 1
            assert "SQL DRY RUN - Would execute SQL:" not in loguru_caplog.text
            mock_connection.execute.assert_called_once()
