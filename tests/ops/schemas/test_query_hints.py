"""Tests for query hints schemas."""

import pytest
from pydantic import ValidationError

from fides.api.schemas.query_hints.base import QueryHint, QueryHints
from fides.api.schemas.query_hints.mssql_query_hints import MSSQLHintType, MSSQLQueryHint


class TestMSSQLQueryHint:
    """Tests for Microsoft SQL Server query hints."""

    def test_maxdop_hint_valid(self):
        """Test that a valid MAXDOP hint is created successfully."""
        hint = MSSQLQueryHint(hint_type=MSSQLHintType.MAXDOP, value=1)
        assert hint.hint_type == MSSQLHintType.MAXDOP
        assert hint.value == 1
        assert hint.to_sql_option() == "MAXDOP 1"

    def test_maxdop_hint_zero(self):
        """Test that MAXDOP 0 is valid (unlimited parallelism)."""
        hint = MSSQLQueryHint(hint_type=MSSQLHintType.MAXDOP, value=0)
        assert hint.to_sql_option() == "MAXDOP 0"

    def test_maxdop_hint_max_value(self):
        """Test that MAXDOP 64 is valid (max allowed)."""
        hint = MSSQLQueryHint(hint_type=MSSQLHintType.MAXDOP, value=64)
        assert hint.to_sql_option() == "MAXDOP 64"

    def test_maxdop_hint_missing_value(self):
        """Test that MAXDOP hint requires a value."""
        with pytest.raises(ValidationError) as exc_info:
            MSSQLQueryHint(hint_type=MSSQLHintType.MAXDOP)
        assert "MAXDOP hint requires a value" in str(exc_info.value)

    def test_maxdop_hint_negative_value(self):
        """Test that negative MAXDOP values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MSSQLQueryHint(hint_type=MSSQLHintType.MAXDOP, value=-1)
        assert "MAXDOP value must be an integer between 0 and 64" in str(exc_info.value)

    def test_maxdop_hint_value_too_high(self):
        """Test that MAXDOP values > 64 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MSSQLQueryHint(hint_type=MSSQLHintType.MAXDOP, value=65)
        assert "MAXDOP value must be an integer between 0 and 64" in str(exc_info.value)

    def test_from_dict(self):
        """Test creating hint from dictionary (as would come from YAML)."""
        hint_dict = {"hint_type": "maxdop", "value": 1}
        hint = MSSQLQueryHint.model_validate(hint_dict)
        assert hint.hint_type == MSSQLHintType.MAXDOP
        assert hint.value == 1


class TestQueryHint:
    """Tests for the base QueryHint class."""

    def test_mssql_implementation_registered(self):
        """Test that MSSQL implementation is registered."""
        impl = QueryHint.get_implementation("mssql")
        assert impl == MSSQLQueryHint

    def test_unknown_connection_type_returns_none(self):
        """Test that unknown connection types return None."""
        impl = QueryHint.get_implementation("unknown_db")
        assert impl is None

    def test_supported_connection_types(self):
        """Test getting supported connection types."""
        supported = QueryHint.get_supported_connection_types()
        assert "mssql" in supported


class TestQueryHints:
    """Tests for the QueryHints container."""

    def test_empty_hints(self):
        """Test empty hints container."""
        hints = QueryHints(hints=[])
        assert hints.get_hints_for_connection_type("mssql") == []
        assert hints.to_sql_option_clause("mssql") is None

    def test_single_mssql_hint(self):
        """Test single MSSQL hint."""
        hints = QueryHints(hints=[{"hint_type": "maxdop", "value": 1}])
        mssql_hints = hints.get_hints_for_connection_type("mssql")
        assert len(mssql_hints) == 1
        assert mssql_hints[0].to_sql_option() == "MAXDOP 1"

    def test_to_sql_option_clause(self):
        """Test generating full OPTION clause."""
        hints = QueryHints(hints=[{"hint_type": "maxdop", "value": 1}])
        clause = hints.to_sql_option_clause("mssql")
        assert clause == "OPTION (MAXDOP 1)"

    def test_invalid_hints_skipped(self):
        """Test that invalid hints are skipped silently."""
        hints = QueryHints(
            hints=[
                {"hint_type": "maxdop", "value": 1},  # Valid
                {"hint_type": "invalid_hint", "value": 99},  # Invalid
                {"hint_type": "maxdop", "value": -1},  # Invalid value
            ]
        )
        mssql_hints = hints.get_hints_for_connection_type("mssql")
        # Only the valid hint should be returned
        assert len(mssql_hints) == 1
        assert mssql_hints[0].value == 1

    def test_hints_for_unsupported_connection_type(self):
        """Test that unsupported connection types return no hints."""
        hints = QueryHints(hints=[{"hint_type": "maxdop", "value": 1}])
        postgres_hints = hints.get_hints_for_connection_type("postgres")
        assert postgres_hints == []
        assert hints.to_sql_option_clause("postgres") is None
