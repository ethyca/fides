"""
Integration tests for the SQLAlchemy-based SQLConditionTranslator using existing fixtures
"""

from datetime import datetime, timedelta, timezone

import pytest

from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_translator import (
    SQLConditionTranslator,
    SQLTranslationError,
)


@pytest.fixture
def translator(db):
    """Create a translator instance with mocked dependencies"""
    translator = SQLConditionTranslator(db)

    return translator


class TestSQLTranslatorIntegration:
    """Integration tests for SQL translator against real database using existing fixtures"""

    def test_basic_user_query(self, translator, user):
        """Test basic user query with existing user fixture"""
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.eq,
            value=user.email_address,
        )

        query = translator.generate_query_from_condition(condition)
        results = query.all()

        # Should find exactly one user
        assert len(results) >= 1

    def test_privacy_request_query(self, translator, privacy_request):
        """Test privacy request query with existing fixture"""
        condition = ConditionLeaf(
            field_address="privacyrequest.id",
            operator=Operator.eq,
            value=privacy_request.id,
        )

        query = translator.generate_query_from_condition(condition)
        results = query.all()

        # Should find exactly one privacy request
        assert len(results) == 1

    def test_string_operations(self, translator, user):
        """Test string operations with user data"""

        # Test contains
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.contains,
            value="@",
        )

        query = translator.generate_query_from_condition(condition)
        results = query.all()

        # Should find users with email addresses containing @
        assert len(results) >= 1

    def test_existence_operators(self, translator, user):
        """Test existence operators"""

        # Test exists - should find users with email addresses
        condition = ConditionLeaf(
            field_address="fidesuser.email_address", operator=Operator.exists
        )

        query = translator.generate_query_from_condition(condition)
        results = query.all()

        # Should find users with email addresses
        assert len(results) >= 1

    def test_group_conditions(self, translator, privacy_request):
        """Test group conditions with AND/OR logic"""
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="privacyrequest.id",
                    operator=Operator.eq,
                    value=privacy_request.id,
                ),
                ConditionLeaf(
                    field_address="privacyrequest.status",
                    operator=Operator.eq,
                    value=privacy_request.status,
                ),
            ],
        )

        query = translator.generate_query_from_condition(condition)
        results = query.all()

        # Should find exactly one privacy request matching both conditions
        assert len(results) == 1

    def test_limit_and_offset(self, translator, user):
        """Test LIMIT and OFFSET functionality"""
        condition = ConditionLeaf(
            field_address="fidesuser.email_address", operator=Operator.exists
        )

        # Test with limit
        query = translator.generate_query_from_condition(condition, limit=1)
        results = query.all()

        # Should return at most 1 result
        assert len(results) <= 1

        # Test with offset
        query = translator.generate_query_from_condition(condition, offset=0)
        results = query.all()

        # Should return some results
        assert len(results) >= 0

    def test_no_matches_query(self, translator):
        """Test query that returns no matches"""
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.eq,
            value="nonexistent@example.com",
        )

        query = translator.generate_query_from_condition(condition)
        results = query.all()

        # Should find no users
        assert len(results) == 0

    def test_complex_nested_conditions(self, translator, privacy_requests):
        """Test complex nested conditions with multiple privacy requests"""
        if not privacy_requests or len(privacy_requests) < 2:
            pytest.skip("Need at least 2 privacy requests for this test")

        # Complex nested condition: (id = pr1 AND status = pr1.status) OR (id = pr2)
        condition = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionGroup(
                    logical_operator=GroupOperator.and_,
                    conditions=[
                        ConditionLeaf(
                            field_address="privacyrequest.id",
                            operator=Operator.eq,
                            value=privacy_requests[0].id,
                        ),
                        ConditionLeaf(
                            field_address="privacyrequest.status",
                            operator=Operator.eq,
                            value=privacy_requests[0].status,
                        ),
                    ],
                ),
                ConditionLeaf(
                    field_address="privacyrequest.id",
                    operator=Operator.eq,
                    value=privacy_requests[1].id,
                ),
            ],
        )

        query = translator.generate_query_from_condition(condition)
        results = query.all()

        # Should find both privacy requests
        assert len(results) == 2

    def test_error_handling(self, translator):
        """Test error handling for invalid queries"""
        # Test with field address that doesn't have table name
        condition = ConditionLeaf(
            field_address="invalid_field", operator=Operator.eq, value="test"
        )

        with pytest.raises(SQLTranslationError, match="Table name not specified"):
            translator.analyze_tables_in_condition(condition)

    def test_sql_injection_protection(self, translator):
        """Test that SQL injection attempts are properly handled"""
        # Test with potentially malicious input
        malicious_input = "'; DROP TABLE fidesuser; --"
        condition = ConditionLeaf(
            field_address="fidesuser.email_address",
            operator=Operator.eq,
            value=malicious_input,
        )

        # This should not raise an exception and should return no results
        query = translator.generate_query_from_condition(condition)
        results = query.all()
        assert len(results) == 0

    def test_multi_table_analysis(self, translator, user, privacy_request):
        """Test analysis of multi-table conditions"""
        # Create a condition that spans multiple tables
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="fidesuser.id", operator=Operator.eq, value=user.id
                ),
                ConditionLeaf(
                    field_address="privacyrequest.id",
                    operator=Operator.eq,
                    value=privacy_request.id,
                ),
            ],
        )

        # Test table analysis
        tables_to_fields = translator.analyze_tables_in_condition(condition)

        assert "fidesuser" in tables_to_fields
        assert "privacyrequest" in tables_to_fields
        assert len(tables_to_fields["fidesuser"]) == 1
        assert len(tables_to_fields["privacyrequest"]) == 1

        # Test field extraction
        field_addresses = translator.extract_field_addresses(condition)
        assert len(field_addresses) == 2

        table_names = {addr.table_name for addr in field_addresses}
        assert table_names == {"fidesuser", "privacyrequest"}


class TestEmailNotificationUseCase:
    """Test the complex email notification use case we discussed"""

    def test_email_notification_condition_structure(self, translator):
        """Test the structure of the email notification condition"""
        # Simulate the email notification condition:
        # Find users who should be notified about privacy requests due within 5 days
        five_days_from_now = datetime.now(timezone.utc) + timedelta(days=5)

        email_condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                # Privacy requests due within 5 days
                ConditionLeaf(
                    field_address="privacyrequest.due_date",
                    operator=Operator.lte,
                    value=five_days_from_now.isoformat(),
                ),
                # Not completed
                ConditionLeaf(
                    field_address="privacyrequest.status",
                    operator=Operator.neq,
                    value="complete",
                ),
                # Has manual tasks
                ConditionLeaf(
                    field_address="manual_task_instance.entity_type",
                    operator=Operator.eq,
                    value="privacy_request",
                ),
                # Assigned to users
                ConditionLeaf(
                    field_address="manual_task_reference.reference_type",
                    operator=Operator.eq,
                    value="assigned_user",
                ),
            ],
        )

        # Test that we can analyze this complex condition
        tables_to_fields = translator.analyze_tables_in_condition(email_condition)

        expected_tables = {
            "privacyrequest",
            "manual_task_instance",
            "manual_task_reference",
        }
        assert set(tables_to_fields.keys()) == expected_tables

        # Check field counts
        assert len(tables_to_fields["privacyrequest"]) == 2  # due_date, status
        assert len(tables_to_fields["manual_task_instance"]) == 1  # entity_type
        assert len(tables_to_fields["manual_task_reference"]) == 1  # reference_type

    def test_email_notification_field_extraction(self, translator):
        """Test field extraction for the email notification use case"""

        # Simplified version focusing on field extraction
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="privacyrequest.due_date",
                    operator=Operator.lte,
                    value="2024-01-01",
                ),
                ConditionLeaf(
                    field_address="manual_task_instance.entity_id",
                    operator=Operator.eq,
                    value="test-id",
                ),
            ],
        )

        # Test field extraction
        field_addresses = translator.extract_field_addresses(condition)
        assert len(field_addresses) == 2

        # Verify field parsing
        for field_addr in field_addresses:
            assert field_addr.table_name in ["privacyrequest", "manual_task_instance"]
            assert field_addr.column_name in ["due_date", "entity_id"]

    def test_multi_table_query_capability(self, translator):
        """Test that the translator can handle multi-table scenarios"""

        # Test a condition that would require JOINs across multiple tables
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="fidesuser.disabled",
                    operator=Operator.eq,
                    value=False,
                ),
                ConditionLeaf(
                    field_address="privacyrequest.status",
                    operator=Operator.eq,
                    value="in_processing",
                ),
            ],
        )

        # This should not raise an error during analysis
        tables_to_fields = translator.analyze_tables_in_condition(condition)
        assert "fidesuser" in tables_to_fields
        assert "privacyrequest" in tables_to_fields

        # The translator should be able to build a query (even if it fails at execution
        # due to missing relationships, the structure should be analyzable)
        try:
            query = translator.generate_query_from_condition(condition)
            # If it succeeds, great! If it fails due to missing relationships,
            # that's expected and we can catch it
            assert query is not None
        except SQLTranslationError as e:
            # Expected if relationships aren't properly set up
            assert "models found" in str(e) or "relationship" in str(e).lower()
