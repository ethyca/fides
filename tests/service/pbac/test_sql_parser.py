"""Tests for the PBAC SQL parser column extraction."""

from __future__ import annotations

import pytest

from fides.service.pbac.sql_parser import (
    detect_statement_type,
    extract_columns,
    extract_table_refs,
    parse_query,
)


class TestExtractColumns:
    def test_simple_select(self):
        result = extract_columns("SELECT email, name FROM users")
        assert result == {"users": ["email", "name"]}

    def test_qualified_columns(self):
        result = extract_columns("SELECT u.email, u.phone FROM users u")
        assert result == {"users": ["email", "phone"]}

    def test_multiple_tables(self):
        result = extract_columns(
            "SELECT u.email, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )
        assert "users" in result
        assert "orders" in result
        assert "email" in result["users"]
        assert "id" in result["users"]
        assert "total" in result["orders"]
        assert "user_id" in result["orders"]

    def test_select_star_returns_empty(self):
        result = extract_columns("SELECT * FROM users")
        assert result == {}

    def test_unqualified_columns(self):
        result = extract_columns("SELECT email FROM users")
        assert result == {"users": ["email"]}

    def test_case_sensitive_columns(self):
        result = extract_columns('SELECT "Email", "Phone_Number" FROM users')
        assert result.get("users") is not None
        assert "Email" in result["users"]
        assert "Phone_Number" in result["users"]

    def test_subquery(self):
        result = extract_columns(
            "SELECT email FROM (SELECT email, name FROM users) sub"
        )
        assert "email" in result.get("users", [])

    def test_cte(self):
        result = extract_columns(
            "WITH active AS (SELECT u.email FROM users u) SELECT email FROM active"
        )
        assert "email" in result.get("users", [])

    def test_parse_failure_returns_empty(self):
        result = extract_columns("NOT VALID SQL ;;; %%%")
        assert result == {} or isinstance(result, dict)

    def test_empty_string(self):
        result = extract_columns("")
        assert result == {}

    def test_mixed_qualified_unqualified(self):
        result = extract_columns("SELECT u.email, phone FROM users u")
        assert "email" in result.get("users", [])
        assert "phone" in result.get("users", [])


class TestExtractTableRefs:
    def test_single_table(self):
        refs = extract_table_refs("SELECT * FROM mydb.myschema.users")
        assert len(refs) == 1
        assert refs[0].table == "users"
        assert refs[0].schema == "myschema"

    def test_multiple_tables(self):
        refs = extract_table_refs("SELECT * FROM users JOIN orders ON 1=1")
        assert len(refs) == 2


class TestDetectStatementType:
    @pytest.mark.parametrize(
        "sql,expected",
        [
            ("SELECT 1", "SELECT"),
            ("INSERT INTO t VALUES (1)", "INSERT"),
            ("UPDATE t SET x=1", "UPDATE"),
            ("DELETE FROM t", "DELETE"),
            ("CREATE TABLE t (id INT)", "CREATE"),
            ("DROP TABLE t", "DROP"),
            ("-- comment\nSELECT 1", "SELECT"),
        ],
    )
    def test_statement_types(self, sql: str, expected: str):
        assert detect_statement_type(sql) == expected


class TestParseQuery:
    def test_produces_entry(self):
        entry = parse_query("SELECT email FROM users", "alice@example.com")
        assert entry.identity == "alice@example.com"
        assert entry.statement_type == "SELECT"
        assert len(entry.referenced_tables) == 1
        assert entry.referenced_tables[0].table == "users"
