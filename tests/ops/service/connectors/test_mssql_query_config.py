"""Tests for Microsoft SQL Server query configuration."""

from unittest.mock import MagicMock

import pytest

from fides.api.graph.config import Collection, FieldPath, ScalarField
from fides.api.schemas.query_hints.base import QueryHints
from fides.api.service.connectors.query_configs.microsoft_sql_server_query_config import (
    MicrosoftSQLServerQueryConfig,
)


@pytest.fixture
def mock_execution_node():
    """Create a mock execution node for testing."""
    node = MagicMock()
    node.collection = Collection(
        name="test_table",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(name="email"),
            ScalarField(name="name"),
        ],
    )
    node.address = MagicMock()
    node.address.value = "test_dataset:test_table"
    return node


@pytest.fixture
def mock_execution_node_with_hints():
    """Create a mock execution node with query hints configured."""
    node = MagicMock()
    node.collection = Collection(
        name="test_table",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(name="email"),
            ScalarField(name="name"),
        ],
        query_hints=QueryHints(hints=[{"hint_type": "maxdop", "value": 1}]),
    )
    node.address = MagicMock()
    node.address.value = "test_dataset:test_table"
    return node


class TestMicrosoftSQLServerQueryConfig:
    """Tests for MSSQL query configuration."""

    def test_get_formatted_query_string_without_hints(self, mock_execution_node):
        """Test query string generation without hints."""
        config = MicrosoftSQLServerQueryConfig(mock_execution_node)

        query = config.get_formatted_query_string(
            field_list="id, email, name",
            clauses=["email = :email"],
        )

        assert query == "SELECT id, email, name FROM test_table WHERE email = :email"
        assert "OPTION" not in query

    def test_get_formatted_query_string_with_maxdop_hint(
        self, mock_execution_node_with_hints
    ):
        """Test query string generation with MAXDOP hint."""
        config = MicrosoftSQLServerQueryConfig(mock_execution_node_with_hints)

        query = config.get_formatted_query_string(
            field_list="id, email, name",
            clauses=["email = :email"],
        )

        assert (
            query
            == "SELECT id, email, name FROM test_table WHERE email = :email OPTION (MAXDOP 1)"
        )

    def test_get_formatted_query_string_with_multiple_clauses(
        self, mock_execution_node_with_hints
    ):
        """Test query string with multiple WHERE clauses and hints."""
        config = MicrosoftSQLServerQueryConfig(mock_execution_node_with_hints)

        query = config.get_formatted_query_string(
            field_list="id, email, name",
            clauses=["email = :email", "id IN (:id_0, :id_1)"],
        )

        expected = "SELECT id, email, name FROM test_table WHERE email = :email OR id IN (:id_0, :id_1) OPTION (MAXDOP 1)"
        assert query == expected

    def test_get_formatted_query_string_empty_hints(self, mock_execution_node):
        """Test that empty hints don't add OPTION clause."""
        mock_execution_node.collection.query_hints = QueryHints(hints=[])
        config = MicrosoftSQLServerQueryConfig(mock_execution_node)

        query = config.get_formatted_query_string(
            field_list="id, email",
            clauses=["email = :email"],
        )

        assert "OPTION" not in query

    def test_get_formatted_query_string_invalid_hints_ignored(self, mock_execution_node):
        """Test that invalid hints are ignored and don't break query generation."""
        mock_execution_node.collection.query_hints = QueryHints(
            hints=[{"hint_type": "invalid", "value": 999}]
        )
        config = MicrosoftSQLServerQueryConfig(mock_execution_node)

        query = config.get_formatted_query_string(
            field_list="id, email",
            clauses=["email = :email"],
        )

        # Invalid hints should be ignored, no OPTION clause added
        assert "OPTION" not in query
        assert query == "SELECT id, email FROM test_table WHERE email = :email"
