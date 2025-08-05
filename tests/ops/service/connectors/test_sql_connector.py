from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel
from sqlalchemy import text

from fides.api.common_exceptions import ConnectionException, TableNotFound
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

    def test_should_dry_run_default_never_set(self, mock_connector, db):
        """Test that should_dry_run returns False for both modes when sql_dry_run has never been set"""
        from fides.api.schemas.application_config import SqlDryRunMode

        # Don't set any config - use default/unset state
        # Test that both access and erasure modes return False when config is unset
        assert mock_connector.should_dry_run(SqlDryRunMode.access) is False
        assert mock_connector.should_dry_run(SqlDryRunMode.erasure) is False

    def test_should_dry_run_explicit_none(self, mock_connector, db):
        """Test that should_dry_run returns False for both modes when sql_dry_run is explicitly set to 'none'"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
        db.commit()

        # Test that both access and erasure modes return False when mode is 'none'
        assert mock_connector.should_dry_run(SqlDryRunMode.access) is False
        assert mock_connector.should_dry_run(SqlDryRunMode.erasure) is False

    def test_should_dry_run_null_value(self, mock_connector, db):
        """Test that should_dry_run returns False for both modes when sql_dry_run is set to null"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(db, {"execution": {"sql_dry_run": None}})
        db.commit()

        # Test that both access and erasure modes return False when mode is null
        assert mock_connector.should_dry_run(SqlDryRunMode.access) is False
        assert mock_connector.should_dry_run(SqlDryRunMode.erasure) is False

    def test_should_dry_run_access_mode_only_matches_access(self, mock_connector, db):
        """Test that when mode is 'access', only access returns True, erasure returns False"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.access.value}}
        )
        db.commit()

        # Test that only access mode returns True
        assert mock_connector.should_dry_run(SqlDryRunMode.access) is True
        assert mock_connector.should_dry_run(SqlDryRunMode.erasure) is False

        # Clean up
        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
        db.commit()

    def test_should_dry_run_erasure_mode_only_matches_erasure(self, mock_connector, db):
        """Test that when mode is 'erasure', only erasure returns True, access returns False"""
        from fides.api.models.application_config import ApplicationConfig
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.erasure.value}}
        )
        db.commit()

        # Test that only erasure mode returns True
        assert mock_connector.should_dry_run(SqlDryRunMode.access) is False
        assert mock_connector.should_dry_run(SqlDryRunMode.erasure) is True

        # Clean up
        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
        db.commit()

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
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.access.value}}
        )
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

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
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
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
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
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.access.value}}
        )
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

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
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
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.erasure.value}}
        )
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

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
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
        from fides.api.schemas.application_config import SqlDryRunMode

        ApplicationConfig.update_api_set(
            db, {"execution": {"sql_dry_run": SqlDryRunMode.none.value}}
        )
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

    def test_mask_data_table_not_found_leaf_collection(
        self,
        mock_connector,
        mock_execution_node,
        mock_privacy_request,
        mock_request_task,
        db,
    ):
        """Test that mask_data raises TableNotFound when table doesn't exist for leaf collection"""
        mock_query_config = MagicMock()
        mock_query_config.generate_update_stmt.return_value = text(
            "UPDATE test_table SET name = NULL WHERE id = :id"
        )

        mock_connection = MagicMock()
        mock_connection.execute.side_effect = Exception("Table doesn't exist")

        # Mock as leaf collection (no dependencies)
        mock_execution_node.has_outgoing_dependencies.return_value = False

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
            patch.object(mock_connector, "set_schema"),
            patch.object(
                mock_connector, "get_qualified_table_name", return_value="test_table"
            ),
            patch.object(mock_connector, "table_exists", return_value=False),
        ):
            mock_client.return_value.connect.return_value.__enter__.return_value = (
                mock_connection
            )

            with pytest.raises(TableNotFound):
                mock_connector.mask_data(
                    node=mock_execution_node,
                    policy=MagicMock(),
                    privacy_request=mock_privacy_request,
                    request_task=mock_request_task,
                    rows=[{"id": 1, "name": "test"}],
                )

    def test_mask_data_table_not_found_collection_with_dependencies(
        self,
        mock_connector,
        mock_execution_node,
        mock_privacy_request,
        mock_request_task,
        db,
    ):
        """Test that mask_data raises ConnectionException when table doesn't exist for collection with dependencies"""
        mock_query_config = MagicMock()
        mock_query_config.generate_update_stmt.return_value = text(
            "UPDATE customer SET name = NULL WHERE id = :id"
        )

        mock_connection = MagicMock()
        mock_connection.execute.side_effect = Exception("Table doesn't exist")

        # Mock as collection with dependencies
        mock_execution_node.has_outgoing_dependencies.return_value = True

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
            patch.object(mock_connector, "set_schema"),
            patch.object(
                mock_connector, "get_qualified_table_name", return_value="customer"
            ),
            patch.object(mock_connector, "table_exists", return_value=False),
        ):
            mock_client.return_value.connect.return_value.__enter__.return_value = (
                mock_connection
            )

            with pytest.raises(ConnectionException):
                mock_connector.mask_data(
                    node=mock_execution_node,
                    policy=MagicMock(),
                    privacy_request=mock_privacy_request,
                    request_task=mock_request_task,
                    rows=[{"id": 1, "name": "test"}],
                )

    def test_mask_data_table_exists_error_passthrough(
        self,
        mock_connector,
        mock_execution_node,
        mock_privacy_request,
        mock_request_task,
        db,
    ):
        """Test that mask_data re-raises original exception when table exists but other error occurs"""
        mock_query_config = MagicMock()
        mock_query_config.generate_update_stmt.return_value = text(
            "UPDATE test_table SET name = NULL WHERE id = :id"
        )

        mock_connection = MagicMock()
        mock_connection.execute.side_effect = Exception("Permission denied")

        with (
            patch.object(
                mock_connector, "query_config", return_value=mock_query_config
            ),
            patch.object(mock_connector, "client") as mock_client,
            patch.object(mock_connector, "set_schema"),
            patch.object(
                mock_connector, "get_qualified_table_name", return_value="test_table"
            ),
            patch.object(
                mock_connector, "table_exists", return_value=True
            ),  # Table exists
        ):
            mock_client.return_value.connect.return_value.__enter__.return_value = (
                mock_connection
            )

            # Should re-raise original exception when table exists
            with pytest.raises(Exception, match="Permission denied"):
                mock_connector.mask_data(
                    node=mock_execution_node,
                    policy=MagicMock(),
                    privacy_request=mock_privacy_request,
                    request_task=mock_request_task,
                    rows=[{"id": 1, "name": "test"}],
                )
