import pytest
from sqlalchemy import text

from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_translator import (
    SQLConditionTranslator,
)


class TestSQLTranslatorIntegration:
    """Integration tests for SQL translator against real database"""

    def test_basic_equality_query(self, postgres_integration_db):
        """Test basic equality condition with real database"""
        translator = SQLConditionTranslator("customer")
        condition = ConditionLeaf(
            field_address="email", operator=Operator.eq, value="customer-1@example.com"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email", "name"]
        )

        # Execute the query
        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 1 customer
        assert len(rows) == 1
        assert rows[0].email == "customer-1@example.com"

    def test_numeric_comparison_query(self, postgres_integration_db):
        """Test numeric comparison with real database"""
        translator = SQLConditionTranslator("login")
        condition = ConditionLeaf(
            field_address="customer_id", operator=Operator.gte, value=2
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "customer_id", "time"]
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return logins for customer_id >= 2
        assert len(rows) >= 1
        customer_ids = [row.customer_id for row in rows]
        assert all(customer_id >= 2 for customer_id in customer_ids)

    def test_string_operations_query(self, postgres_integration_db):
        """Test string operations with real database"""
        translator = SQLConditionTranslator("visit")
        condition = ConditionLeaf(
            field_address="email", operator=Operator.starts_with, value="customer-1"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["email", "last_visit"]
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return customer-1@example.com
        assert len(rows) == 1
        assert rows[0].email == "customer-1@example.com"

    def test_existence_operators_query(self, postgres_integration_db):
        """Test existence operators with real database"""
        translator = SQLConditionTranslator("customer")

        # Test exists - all customers should have emails
        condition = ConditionLeaf(field_address="email", operator=Operator.exists)

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email"]
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return all customers (they all have emails)
        assert len(rows) >= 2

    def test_count_query(self, postgres_integration_db):
        """Test COUNT query with real database"""
        translator = SQLConditionTranslator("login")
        condition = ConditionLeaf(
            field_address="customer_id", operator=Operator.eq, value=1
        )

        query, parameters = translator.generate_count_query(condition)

        result = postgres_integration_db.execute(query, parameters)
        count = result.scalar()

        # Should count logins for customer_id = 1
        assert count == 6  # Based on the test data

    def test_group_conditions_query(self, postgres_integration_db):
        """Test group conditions with real database"""
        translator = SQLConditionTranslator("login")
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="customer_id", operator=Operator.eq, value=1
                ),
                ConditionLeaf(field_address="id", operator=Operator.gte, value=3),
            ],
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "customer_id", "time"]
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return logins for customer_id=1 AND id>=3
        assert len(rows) == 4  # IDs 3, 4, 5, 6
        for row in rows:
            assert row.customer_id == 1
            assert row.id >= 3

    def test_field_mapping_query(self, postgres_integration_db):
        """Test field mapping with real database"""
        translator = SQLConditionTranslator("customer")
        condition = ConditionLeaf(
            field_address="customer_email",
            operator=Operator.eq,
            value="customer-1@example.com",
        )

        field_mapping = {"customer_email": "email"}

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email"], field_mapping=field_mapping
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return customer-1@example.com
        assert len(rows) == 1
        assert rows[0].email == "customer-1@example.com"

    def test_limit_and_offset_query(self, postgres_integration_db):
        """Test LIMIT and OFFSET with real database"""
        translator = SQLConditionTranslator("login")
        condition = ConditionLeaf(
            field_address="customer_id", operator=Operator.eq, value=1
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "customer_id"], limit=3, offset=1
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 3 logins (limit) starting from the second (offset)
        assert len(rows) == 3

    def test_query_with_no_matches(self, postgres_integration_db):
        """Test query that returns no matches"""
        translator = SQLConditionTranslator("customer")
        condition = ConditionLeaf(
            field_address="email", operator=Operator.eq, value="nonexistent@example.com"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email"]
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return no rows
        assert len(rows) == 0

    def test_string_contains_query(self, postgres_integration_db):
        """Test string contains operation"""
        translator = SQLConditionTranslator("visit")
        condition = ConditionLeaf(
            field_address="email", operator=Operator.contains, value="customer"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["email", "last_visit"]
        )

        result = postgres_integration_db.execute(query, parameters)
        rows = result.fetchall()

        # Should return all visit records (all emails contain "customer")
        assert len(rows) == 2
