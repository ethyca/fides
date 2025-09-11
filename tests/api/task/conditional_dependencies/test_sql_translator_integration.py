import pytest
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fides.api.models.fides_user import FidesUser
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.client import ClientDetail
from fides.api.models.policy import Policy
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.oauth.roles import APPROVER
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


class TestSQLTranslatorIntegration:
    """Integration tests for SQL translator against real database"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, db):
        """Set up test data for fides models"""
        # Create test users
        self.user1 = FidesUser.create(
            db=db,
            data={
                "username": "test_user_1",
                "email_address": "user1@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "hashed_password": "hashed_password_1",
                "salt": "salt_1",
            },
        )

        self.user2 = FidesUser.create(
            db=db,
            data={
                "username": "test_user_2",
                "email_address": "user2@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "hashed_password": "hashed_password_2",
                "salt": "salt_2",
            },
        )

        self.user3 = FidesUser.create(
            db=db,
            data={
                "username": "test_user_3",
                "email_address": "user3@example.com",
                "first_name": "Bob",
                "last_name": "Johnson",
                "hashed_password": "hashed_password_3",
                "salt": "salt_3",
            },
        )

        # Create test policy
        self.policy = Policy.create(
            db=db,
            data={
                "name": "test_policy",
                "key": "test_policy_key",
            },
        )

        # Create test privacy requests
        self.privacy_request1 = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid4())}",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.utcnow() - timedelta(days=1),
                "status": PrivacyRequestStatus.in_processing,
                "origin": "https://example.com/testing",
                "policy_id": self.policy.id,
                "submitted_by": self.user1.id,
            },
        )

        self.privacy_request2 = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid4())}",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.utcnow() - timedelta(days=2),
                "status": PrivacyRequestStatus.approved,
                "origin": "https://example.com/testing",
                "policy_id": self.policy.id,
                "submitted_by": self.user2.id,
                "reviewed_by": self.user1.id,
                "reviewed_at": datetime.now(timezone.utc) - timedelta(hours=1),
            },
        )

        self.privacy_request3 = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid4())}",
                "started_processing_at": datetime.now(timezone.utc),
                "requested_at": datetime.utcnow() - timedelta(days=3),
                "status": PrivacyRequestStatus.complete,
                "origin": "https://example.com/testing",
                "policy_id": self.policy.id,
                "submitted_by": self.user3.id,
                "reviewed_by": self.user1.id,
                "reviewed_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "finalized_at": datetime.now(timezone.utc) - timedelta(minutes=30),
                "finalized_by": self.user1.id,
            },
        )

        # Create test client
        self.client = ClientDetail(
            hashed_secret="test_secret",
            salt="test_salt",
            roles=[APPROVER],
            scopes=[],
            user_id=self.user1.id,
        )
        db.add(self.client)
        db.commit()
        db.refresh(self.client)

        yield

        # Cleanup
        try:
            self.client.delete(db)
            self.privacy_request1.delete(db)
            self.privacy_request2.delete(db)
            self.privacy_request3.delete(db)
            self.policy.delete(db)
            self.user1.delete(db)
            self.user2.delete(db)
            self.user3.delete(db)
        except Exception:
            pass

    def test_basic_equality_query(self, db):
        """Test basic equality condition with real database"""
        translator = SQLConditionTranslator("fidesuser")
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.eq, value="user1@example.com"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email_address", "username"]
        )

        # Execute the query
        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 1 user
        assert len(rows) == 1
        assert rows[0].email_address == "user1@example.com"

    def test_numeric_comparison_query(self, db):
        """Test numeric comparison with real database"""
        translator = SQLConditionTranslator("privacyrequest")
        condition = ConditionLeaf(
            field_address="id", operator=Operator.gte, value=self.privacy_request2.id
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "status", "requested_at"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return privacy requests with id >= privacy_request2.id
        assert len(rows) >= 1
        ids = [row.id for row in rows]
        assert all(pr_id >= self.privacy_request2.id for pr_id in ids)

    def test_string_operations_query(self, db):
        """Test string operations with real database"""
        translator = SQLConditionTranslator("fidesuser")
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.starts_with, value="user1"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["email_address", "username"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return user1@example.com
        assert len(rows) == 1
        assert rows[0].email_address == "user1@example.com"

    def test_existence_operators_query(self, db):
        """Test existence operators with real database"""
        translator = SQLConditionTranslator("fidesuser")

        # Test exists - all users should have email addresses
        condition = ConditionLeaf(field_address="email_address", operator=Operator.exists)

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email_address"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return all users (they all have email addresses)
        assert len(rows) >= 3

    def test_count_query(self, db):
        """Test COUNT query with real database"""
        translator = SQLConditionTranslator("privacyrequest")
        condition = ConditionLeaf(
            field_address="submitted_by", operator=Operator.eq, value=self.user1.id
        )

        query, parameters = translator.generate_count_query(condition)

        result = db.execute(query, parameters)
        count = result.scalar()

        # Should count privacy requests submitted by user1
        assert count == 1  # Based on the test data

    def test_group_conditions_query(self, db):
        """Test group conditions with real database"""
        translator = SQLConditionTranslator("privacyrequest")
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="submitted_by", operator=Operator.eq, value=self.user2.id
                ),
                ConditionLeaf(field_address="status", operator=Operator.eq, value="approved"),
            ],
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "submitted_by", "status"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return privacy requests for user2 AND status=approved
        assert len(rows) == 1
        for row in rows:
            assert row.submitted_by == self.user2.id
            assert row.status == "approved"

    def test_field_mapping_query(self, db):
        """Test field mapping with real database"""
        translator = SQLConditionTranslator("fidesuser")
        condition = ConditionLeaf(
            field_address="user_email",
            operator=Operator.eq,
            value="user1@example.com",
        )

        field_mapping = {"user_email": "email_address"}

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email_address"], field_mapping=field_mapping
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return user1@example.com
        assert len(rows) == 1
        assert rows[0].email_address == "user1@example.com"

    def test_limit_and_offset_query(self, db):
        """Test LIMIT and OFFSET with real database"""
        translator = SQLConditionTranslator("privacyrequest")
        condition = ConditionLeaf(
            field_address="status", operator=Operator.eq, value="in_processing"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "status"], limit=1, offset=0
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 1 privacy request (limit) starting from the first (offset)
        assert len(rows) == 1

    def test_query_with_no_matches(self, db):
        """Test query that returns no matches"""
        translator = SQLConditionTranslator("fidesuser")
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.eq, value="nonexistent@example.com"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email_address"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return no rows
        assert len(rows) == 0

    def test_string_contains_query(self, db):
        """Test string contains operation"""
        translator = SQLConditionTranslator("fidesuser")
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.contains, value="user"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["email_address", "username"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return all user records (all emails contain "user")
        assert len(rows) == 3

    def test_json_nested_field_access(self, db):
        """Test PostgreSQL JSON operators for nested field access"""
        # Create a test table with JSON data
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_json_table (
                id SERIAL PRIMARY KEY,
                user_data JSONB,
                metadata JSONB
            )
        """
            )
        )

        # Insert test data with nested JSON
        db.execute(
            text(
                """
            INSERT INTO test_json_table (user_data, metadata) VALUES
            ('{"profile": {"name": "John", "verified": true}, "billing": {"subscription": {"status": "active"}}}', '{"source": "web"}'),
            ('{"profile": {"name": "Jane", "verified": false}, "billing": {"subscription": {"status": "inactive"}}}', '{"source": "mobile"}'),
            ('{"profile": {"name": "Bob", "verified": true}, "billing": {"subscription": {"status": "pending"}}}', '{"source": "api"}')
        """
            )
        )

        translator = SQLConditionTranslator("test_json_table")

        # Test nested field access - need to map the field to the actual JSON column
        # Cast JSON values to appropriate types for comparison
        field_mapping = {
            "user.profile.verified": "(user_data->'profile'->>'verified')::boolean",
            "user.billing.subscription.status": "user_data->'billing'->'subscription'->>'status'",
        }

        condition = ConditionLeaf(
            field_address="user.profile.verified", operator=Operator.eq, value=True
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "user_data"], field_mapping=field_mapping
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 2 records where verified is true
        assert len(rows) == 2

        # Test deeper nesting
        condition = ConditionLeaf(
            field_address="user.billing.subscription.status",
            operator=Operator.eq,
            value="active",
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "user_data"], field_mapping=field_mapping
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 1 record where status is active
        assert len(rows) == 1

        # Clean up
        db.execute(text("DROP TABLE IF EXISTS test_json_table"))

    def test_postgresql_array_operations(self, db):
        """Test PostgreSQL array operations with list operators"""
        # Create a test table with array columns
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_array_table (
                id SERIAL PRIMARY KEY,
                tags TEXT[],
                permissions TEXT[],
                scores INTEGER[]
            )
        """
            )
        )

        # Insert test data with arrays
        db.execute(
            text(
                """
            INSERT INTO test_array_table (tags, permissions, scores) VALUES
            ('{"admin", "moderator"}', '{"read", "write"}', '{85, 90, 78}'),
            ('{"user"}', '{"read"}', '{65, 70}'),
            ('{"admin", "user"}', '{"read", "write", "delete"}', '{95, 88, 92}')
        """
            )
        )

        translator = SQLConditionTranslator("test_array_table")

        # Test list_contains with array column (PostgreSQL ANY operator)
        condition = ConditionLeaf(
            field_address="permissions", operator=Operator.list_contains, value="delete"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "permissions"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 1 record that has 'delete' permission
        assert len(rows) == 1
        assert "delete" in rows[0].permissions

        # Test list_contains with user-provided list - check if any of the tags match
        condition = ConditionLeaf(
            field_address="tags",
            operator=Operator.list_contains,
            value="admin",  # Check if 'admin' is in the tags array
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "tags"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 2 records that have 'admin' in their tags
        assert len(rows) == 2

        # Test not_in_list with array column
        condition = ConditionLeaf(
            field_address="permissions", operator=Operator.not_in_list, value="delete"
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "permissions"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return 2 records that don't have 'delete' permission
        assert len(rows) == 2
        for row in rows:
            assert "delete" not in row.permissions

        # Clean up
        db.execute(text("DROP TABLE IF EXISTS test_array_table"))

    def test_complex_nested_conditions(self, db):
        """Test complex nested conditions with real database"""
        translator = SQLConditionTranslator("privacyrequest")

        # Complex nested condition: (submitted_by = user1 AND status = in_processing) OR (submitted_by = user2)
        condition = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionGroup(
                    logical_operator=GroupOperator.and_,
                    conditions=[
                        ConditionLeaf(
                            field_address="submitted_by", operator=Operator.eq, value=self.user1.id
                        ),
                        ConditionLeaf(
                            field_address="status", operator=Operator.eq, value="in_processing"
                        ),
                    ],
                ),
                ConditionLeaf(
                    field_address="submitted_by", operator=Operator.eq, value=self.user2.id
                ),
            ],
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "submitted_by", "status"]
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return privacy requests for (submitted_by=user1 AND status=in_processing) OR submitted_by=user2
        # Expected: privacy_request1 (user1, in_processing) + privacy_request2 (user2, approved) = 2 total
        assert len(rows) == 2

        for row in rows:
            assert (row.submitted_by == self.user1.id and row.status == "in_processing") or row.submitted_by == self.user2.id

    def test_string_operators_comprehensive(self, db):
        """Test all string operators comprehensively"""
        translator = SQLConditionTranslator("fidesuser")

        # Test starts_with
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.starts_with, value="user1"
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["email_address"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0].email_address.startswith("user1")

        # Test ends_with
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.ends_with, value="@example.com"
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["email_address"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        # All user emails end with @example.com
        assert len(rows) == 3
        for row in rows:
            assert row.email_address.endswith("@example.com")

        # Test contains
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.contains, value="user"
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["email_address"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        # All user emails contain "user"
        assert len(rows) == 3

    def test_existence_operators_comprehensive(self, db):
        """Test existence operators with various scenarios"""
        # Create a test table with some NULL values
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_null_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(100)
            )
        """
            )
        )

        db.execute(
            text(
                """
            INSERT INTO test_null_table (name, email, phone) VALUES
            ('John', 'john@example.com', '123-456-7890'),
            ('Jane', NULL, '987-654-3210'),
            ('Bob', 'bob@example.com', NULL),
            ('Alice', NULL, NULL)
        """
            )
        )

        translator = SQLConditionTranslator("test_null_table")

        # Test exists - should return records with non-null email
        condition = ConditionLeaf(field_address="email", operator=Operator.exists)
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "name"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 2  # John and Bob have emails

        # Test not_exists - should return records with null email
        condition = ConditionLeaf(field_address="email", operator=Operator.not_exists)
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "name"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 2  # Jane and Alice have null emails

        # Clean up
        db.execute(text("DROP TABLE IF EXISTS test_null_table"))

    def test_error_handling_invalid_queries(self, db):
        """Test error handling for invalid queries"""
        translator = SQLConditionTranslator("fidesuser")

        # Test with invalid operator (bypassing validation)
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.eq, value="test"
        )
        condition.operator = "invalid_operator"

        with pytest.raises(SQLTranslationError):
            translator.translate_condition_to_sql(condition)

        # Test with empty condition group
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="email_address", operator=Operator.eq, value="test")
            ],
        )
        condition.conditions = []

        with pytest.raises(SQLTranslationError):
            translator.translate_condition_to_sql(condition)

    def test_query_performance_with_large_dataset(self, db):
        """Test query performance with a larger dataset"""
        # Create a larger test table
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_large_table (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50),
                value INTEGER,
                status VARCHAR(20)
            )
        """
            )
        )

        # Insert 1000 test records
        db.execute(
            text(
                """
            INSERT INTO test_large_table (category, value, status)
            SELECT
                CASE (i % 3)
                    WHEN 0 THEN 'A'
                    WHEN 1 THEN 'B'
                    ELSE 'C'
                END,
                (i % 100) + 1,
                CASE (i % 2)
                    WHEN 0 THEN 'active'
                    ELSE 'inactive'
                END
            FROM generate_series(1, 1000) AS i
        """
            )
        )

        translator = SQLConditionTranslator("test_large_table")

        # Test complex query on large dataset
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="category", operator=Operator.eq, value="A"
                ),
                ConditionLeaf(field_address="value", operator=Operator.gte, value=50),
                ConditionLeaf(
                    field_address="status", operator=Operator.eq, value="active"
                ),
            ],
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "category", "value"], limit=10
        )

        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return up to 10 records matching the criteria
        assert len(rows) <= 10
        for row in rows:
            assert row.category == "A"
            assert row.value >= 50

        # Test count query on large dataset
        count_query, count_params = translator.generate_count_query(condition)
        count_result = db.execute(count_query, count_params)
        total_count = count_result.scalar()

        # Should count all matching records (not limited by LIMIT)
        assert total_count > 10

        # Clean up
        db.execute(text("DROP TABLE IF EXISTS test_large_table"))

    def test_edge_cases_and_boundary_conditions(self, db):
        """Test edge cases and boundary conditions"""
        translator = SQLConditionTranslator("privacyrequest")

        # Test with exact boundary values
        condition = ConditionLeaf(field_address="id", operator=Operator.eq, value=self.privacy_request1.id)
        query, parameters = translator.generate_select_query(condition, fields=["id"])
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0].id == self.privacy_request1.id

        # Test with non-existent value
        condition = ConditionLeaf(field_address="id", operator=Operator.eq, value="non-existent-id")
        query, parameters = translator.generate_select_query(condition, fields=["id"])
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 0

        # Test with limit 0
        condition = ConditionLeaf(
            field_address="status", operator=Operator.eq, value="in_processing"
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id"], limit=0
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 0

        # Test with large offset
        query, parameters = translator.generate_select_query(
            condition, fields=["id"], limit=10, offset=100
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 0  # No records at offset 100

    def test_sql_injection_protection(self, db):
        """Test that SQL injection attempts are properly parameterized"""
        translator = SQLConditionTranslator("fidesuser")

        # Test with potentially malicious input
        malicious_input = "'; DROP TABLE fidesuser; --"
        condition = ConditionLeaf(
            field_address="email_address", operator=Operator.eq, value=malicious_input
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "email_address"]
        )

        # The query should be parameterized, not concatenated
        assert ":param_0" in str(query)
        assert malicious_input in parameters.values()

        # Execute the query - it should not cause any damage
        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return no results (no user with that email)
        assert len(rows) == 0

        # Verify the fidesuser table still exists and has data
        verify_query = text("SELECT COUNT(*) FROM fidesuser")
        count_result = db.execute(verify_query)
        count = count_result.scalar()
        assert count > 0  # Table still exists with data

    def test_unicode_and_special_characters(self, db):
        """Test handling of unicode and special characters in queries"""
        # Create a test table with unicode data
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_unicode_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                description TEXT
            )
        """
            )
        )

        db.execute(
            text(
                """
            INSERT INTO test_unicode_table (name, description) VALUES
            ('José María', 'Café con leche'),
            ('François', 'C''est magnifique!'),
            ('北京', '中文测试'),
            ('Müller', 'Straße 123')
        """
            )
        )

        translator = SQLConditionTranslator("test_unicode_table")

        # Test unicode string matching
        condition = ConditionLeaf(
            field_address="name", operator=Operator.eq, value="José María"
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "name"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0].name == "José María"

        # Test special characters in LIKE operations
        condition = ConditionLeaf(
            field_address="description", operator=Operator.contains, value="Café"
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "description"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 1
        assert "Café" in rows[0].description

        # Clean up
        db.execute(text("DROP TABLE IF EXISTS test_unicode_table"))

    def test_numeric_precision_and_types(self, db):
        """Test numeric operations with different precision and types"""
        # Create a test table with various numeric types
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_numeric_table (
                id SERIAL PRIMARY KEY,
                small_int SMALLINT,
                integer_val INTEGER,
                big_int BIGINT,
                decimal_val DECIMAL(10,2),
                real_val REAL,
                double_val DOUBLE PRECISION,
                money_val MONEY
            )
        """
            )
        )

        db.execute(
            text(
                """
            INSERT INTO test_numeric_table (small_int, integer_val, big_int, decimal_val, real_val, double_val, money_val) VALUES
            (100, 1000, 1000000, 123.45, 3.14159, 3.14159265359, 123.45),
            (200, 2000, 2000000, 456.78, 2.71828, 2.71828182846, 456.78),
            (300, 3000, 3000000, 789.01, 1.41421, 1.41421356237, 789.01)
        """
            )
        )

        translator = SQLConditionTranslator("test_numeric_table")

        # Test various numeric comparisons
        condition = ConditionLeaf(
            field_address="integer_val", operator=Operator.gte, value=2000
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "integer_val"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 2
        for row in rows:
            assert row.integer_val >= 2000

        # Test decimal precision
        condition = ConditionLeaf(
            field_address="decimal_val", operator=Operator.gt, value=400.0
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "decimal_val"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 2
        for row in rows:
            assert float(row.decimal_val) > 400.0

        # Clean up
        db.execute(text("DROP TABLE IF EXISTS test_numeric_table"))

    def test_boolean_operations(self, db):
        """Test boolean operations and data types"""
        # Create a test table with boolean columns
        db.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_boolean_table (
                id SERIAL PRIMARY KEY,
                is_active BOOLEAN,
                is_verified BOOLEAN,
                has_permission BOOLEAN
            )
        """
            )
        )

        db.execute(
            text(
                """
            INSERT INTO test_boolean_table (is_active, is_verified, has_permission) VALUES
            (true, true, true),
            (false, true, false),
            (true, false, true),
            (false, false, false)
        """
            )
        )

        translator = SQLConditionTranslator("test_boolean_table")

        # Test boolean equality
        condition = ConditionLeaf(
            field_address="is_active", operator=Operator.eq, value=True
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "is_active"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 2
        for row in rows:
            assert row.is_active is True

        # Test boolean false
        condition = ConditionLeaf(
            field_address="is_verified", operator=Operator.eq, value=False
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "is_verified"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 2
        for row in rows:
            assert row.is_verified is False

        # Test complex boolean logic
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="is_active", operator=Operator.eq, value=True
                ),
                ConditionLeaf(
                    field_address="is_verified", operator=Operator.eq, value=True
                ),
            ],
        )
        query, parameters = translator.generate_select_query(condition, fields=["id"])
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert (
            len(rows) == 1
        )  # Only one record has both is_active=true AND is_verified=true

        # Clean up
        db.execute(text("DROP TABLE IF EXISTS test_boolean_table"))

    def test_date_and_timestamp_operations(self, db):
        """Test date and timestamp operations"""
        translator = SQLConditionTranslator("privacyrequest")

        # Test timestamp comparison - find privacy requests requested after a certain time
        test_time = datetime.now(timezone.utc) - timedelta(days=2, hours=1)
        test_time = test_time.replace(tzinfo=timezone.utc)
        condition = ConditionLeaf(
            field_address="requested_at",
            operator=Operator.gte,
            value=test_time.isoformat(),
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "requested_at"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()

        # Should return privacy requests requested after the test time
        assert len(rows) >= 1
        for row in rows:
            # Convert to timezone-aware for comparison
            if row.requested_at.tzinfo is None:
                row_time = row.requested_at.replace(tzinfo=timezone.utc)
            else:
                row_time = row.requested_at
            assert row_time >= test_time

        # Test exact timestamp match - find privacy request with specific requested_at time
        condition = ConditionLeaf(
            field_address="requested_at",
            operator=Operator.eq,
            value=self.privacy_request1.requested_at.isoformat(),
        )
        query, parameters = translator.generate_select_query(
            condition, fields=["id", "requested_at"]
        )
        result = db.execute(query, parameters)
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0].requested_at == self.privacy_request1.requested_at

    def test_concurrent_query_execution(self, db):
        """Test that queries can be executed concurrently without issues"""
        import threading
        import time

        translator = SQLConditionTranslator("privacyrequest")
        results = []
        errors = []

        def execute_query(user_id):
            try:
                condition = ConditionLeaf(
                    field_address="submitted_by", operator=Operator.eq, value=user_id
                )
                query, parameters = translator.generate_select_query(
                    condition, fields=["id", "submitted_by"]
                )
                result = db.execute(query, parameters)
                rows = result.fetchall()
                results.append((user_id, len(rows)))
            except Exception as e:
                errors.append((user_id, str(e)))

        # Execute queries concurrently
        threads = []
        for user_id in [self.user1.id, self.user2.id, self.user3.id]:
            thread = threading.Thread(target=execute_query, args=(user_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify results
        assert len(results) == 3
        user_1_count = next((count for uid, count in results if uid == self.user1.id), 0)
        user_2_count = next((count for uid, count in results if uid == self.user2.id), 0)
        user_3_count = next((count for uid, count in results if uid == self.user3.id), 0)

        assert user_1_count == 1  # 1 privacy request for user1
        assert user_2_count == 1  # 1 privacy request for user2
        assert user_3_count == 1  # 1 privacy request for user3
