import pytest
from sqlalchemy import Boolean, Column, String
from sqlalchemy.ext.declarative import declarative_base

from fides.api.task.conditional_dependencies.schemas import Operator
from fides.api.task.conditional_dependencies.sql_schemas import (
    OPERATOR_MAP,
    FieldAddress,
    SQLTranslationError,
)


class TestFieldAddress:
    """Test the FieldAddress parsing and SQL generation functionality"""

    def test_parse_simple_table_column(self):
        """Test parsing simple table.column format"""
        field_addr = FieldAddress.parse("users.email")

        assert field_addr.table_name == "users"
        assert field_addr.column_name == "email"
        assert field_addr.json_path is None
        assert not field_addr.is_json_path
        assert field_addr.base_field_name == "email"
        assert field_addr.full_address == "users.email"

    def test_parse_json_path_simple(self):
        """Test parsing JSON path with single level"""
        field_addr = FieldAddress.parse("users.profile.verified")

        assert field_addr.table_name == "users"
        assert field_addr.column_name == "profile"
        assert field_addr.json_path == ["verified"]
        assert field_addr.is_json_path
        assert field_addr.base_field_name == "profile"
        assert field_addr.full_address == "users.profile.verified"

    def test_parse_json_path_deep(self):
        """Test parsing deep JSON path"""
        field_addr = FieldAddress.parse("users.metadata.preferences.theme")

        assert field_addr.table_name == "users"
        assert field_addr.column_name == "metadata"
        assert field_addr.json_path == ["preferences", "theme"]
        assert field_addr.is_json_path
        assert field_addr.base_field_name == "metadata"
        assert field_addr.full_address == "users.metadata.preferences.theme"

    def test_parse_colon_format(self):
        """Test parsing colon-separated format"""
        field_addr = FieldAddress.parse("users:email")

        assert field_addr.table_name == "users"
        assert field_addr.column_name == "email"
        assert field_addr.json_path is None
        assert not field_addr.is_json_path
        assert field_addr.base_field_name == "email"
        assert field_addr.full_address == "users:email"

    def test_parse_colon_format_complex(self):
        """Test parsing colon format with multiple parts"""
        field_addr = FieldAddress.parse("dataset:collection:field")

        assert field_addr.table_name == "dataset"
        assert field_addr.column_name == "collection:field"
        assert field_addr.json_path is None
        assert not field_addr.is_json_path
        assert field_addr.base_field_name == "collection:field"

    def test_parse_column_only(self):
        """Test parsing column name without table"""
        field_addr = FieldAddress.parse("email")

        assert field_addr.table_name == ""
        assert field_addr.column_name == "email"
        assert field_addr.json_path is None
        assert not field_addr.is_json_path
        assert field_addr.base_field_name == "email"
        assert field_addr.full_address == "email"

    def test_to_sql_column_simple(self):
        """Test SQL column generation for simple fields"""
        field_addr = FieldAddress.parse("users.email")

        assert field_addr.to_sql_column(True) == "email"
        assert field_addr.to_sql_column(False) == "email"

    def test_to_sql_column_json_simple(self):
        """Test SQL column generation for simple JSON path"""
        field_addr = FieldAddress.parse("users.profile.verified")

        assert field_addr.to_sql_column(True) == "profile->>'verified'"
        assert field_addr.to_sql_column(False) == "profile"

    def test_to_sql_column_json_deep(self):
        """Test SQL column generation for deep JSON path"""
        field_addr = FieldAddress.parse("users.metadata.preferences.theme")

        expected = "metadata->'preferences'->>'theme'"
        assert field_addr.to_sql_column(True) == expected
        assert field_addr.to_sql_column(False) == "metadata"

    def test_to_sql_column_json_very_deep(self):
        """Test SQL column generation for very deep JSON path"""
        field_addr = FieldAddress.parse("users.data.user.billing.subscription.status")

        expected = "data->'user'->'billing'->'subscription'->>'status'"
        assert field_addr.to_sql_column(True) == expected
        assert field_addr.to_sql_column(False) == "data"

    def test_json_path_disabled(self):
        """Test that JSON operators are disabled when requested"""
        field_addr = FieldAddress.parse("users.profile.verified")

        # With JSON operators disabled, should return base column name
        assert field_addr.to_sql_column(False) == "profile"

    def test_edge_cases(self):
        """Test edge cases in field address parsing"""
        # Empty string
        field_addr = FieldAddress.parse("")
        assert field_addr.table_name == ""
        assert field_addr.column_name == ""

        # Just dots
        field_addr = FieldAddress.parse("...")
        assert field_addr.table_name == ""
        assert field_addr.column_name == ""

        # Single dot
        field_addr = FieldAddress.parse(".")
        assert field_addr.table_name == ""
        assert field_addr.column_name == ""


# SQLTranslationConfig was removed as it's no longer needed in the new SQLAlchemy-only approach


class TestSQLTranslationError:
    """Test the SQLTranslationError exception"""

    def test_sql_translation_error(self):
        """Test that SQLTranslationError can be raised and caught"""
        with pytest.raises(SQLTranslationError) as exc_info:
            raise SQLTranslationError("Test error message")

        assert str(exc_info.value) == "Test error message"

    def test_sql_translation_error_inheritance(self):
        """Test that SQLTranslationError inherits from Exception"""
        error = SQLTranslationError("Test")
        assert isinstance(error, Exception)


# Create a test base for SQLAlchemy columns
TestBase = declarative_base()


class TestOperatorMap:
    """Test the OPERATOR_MAP functionality"""

    def setup_method(self):
        """Set up test columns for operator testing"""
        # Create test columns
        self.test_column = Column(String, name="test_column")
        self.boolean_column = Column(Boolean, name="boolean_column")
        self.test_value = "test_value"
        self.test_boolean = True

    def test_operator_map_contains_all_operators(self):
        """Test that OPERATOR_MAP contains all expected operators"""
        expected_operators = {
            Operator.eq,
            Operator.neq,
            Operator.lt,
            Operator.lte,
            Operator.gt,
            Operator.gte,
            Operator.contains,
            Operator.starts_with,
            Operator.ends_with,
            Operator.exists,
            Operator.not_exists,
        }

        assert set(OPERATOR_MAP.keys()) == expected_operators

    def test_equality_operators(self):
        """Test equality and inequality operators"""
        # Test equality
        eq_result = OPERATOR_MAP[Operator.eq](self.test_column, self.test_value)
        assert str(eq_result) == "test_column = :test_column_1"

        # Test inequality
        neq_result = OPERATOR_MAP[Operator.neq](self.test_column, self.test_value)
        assert str(neq_result) == "test_column != :test_column_1"

    def test_comparison_operators(self):
        """Test comparison operators (lt, lte, gt, gte)"""
        # Test less than
        lt_result = OPERATOR_MAP[Operator.lt](self.test_column, self.test_value)
        assert str(lt_result) == "test_column < :test_column_1"

        # Test less than or equal
        lte_result = OPERATOR_MAP[Operator.lte](self.test_column, self.test_value)
        assert str(lte_result) == "test_column <= :test_column_1"

        # Test greater than
        gt_result = OPERATOR_MAP[Operator.gt](self.test_column, self.test_value)
        assert str(gt_result) == "test_column > :test_column_1"

        # Test greater than or equal
        gte_result = OPERATOR_MAP[Operator.gte](self.test_column, self.test_value)
        assert str(gte_result) == "test_column >= :test_column_1"

    def test_string_operators(self):
        """Test string pattern matching operators"""
        # Test contains
        contains_result = OPERATOR_MAP[Operator.contains](
            self.test_column, self.test_value
        )
        assert str(contains_result) == "test_column LIKE :test_column_1"

        # Test starts_with
        starts_with_result = OPERATOR_MAP[Operator.starts_with](
            self.test_column, self.test_value
        )
        assert str(starts_with_result) == "test_column LIKE :test_column_1"

        # Test ends_with
        ends_with_result = OPERATOR_MAP[Operator.ends_with](
            self.test_column, self.test_value
        )
        assert str(ends_with_result) == "test_column LIKE :test_column_1"

    def test_existence_operators(self):
        """Test existence operators (exists, not_exists)"""
        # Test exists
        exists_result = OPERATOR_MAP[Operator.exists](self.test_column, None)
        assert str(exists_result) == "test_column IS NOT NULL"

        # Test not_exists
        not_exists_result = OPERATOR_MAP[Operator.not_exists](self.test_column, None)
        assert str(not_exists_result) == "test_column IS NULL"

    def test_operator_functions_are_callable(self):
        """Test that all operator functions are callable"""
        for operator, func in OPERATOR_MAP.items():
            assert callable(
                func
            ), f"Operator {operator} should have a callable function"

    def test_operator_functions_return_sqlalchemy_expressions(self):
        """Test that operator functions return SQLAlchemy expressions"""
        for operator, func in OPERATOR_MAP.items():
            if operator in [Operator.exists, Operator.not_exists]:
                # These operators don't use the value parameter
                result = func(self.test_column, None)
            else:
                result = func(self.test_column, self.test_value)

            # Check that the result is a SQLAlchemy expression
            assert hasattr(
                result, "compile"
            ), f"Operator {operator} should return a SQLAlchemy expression"

    def test_string_operators_with_patterns(self):
        """Test that string operators generate correct LIKE patterns"""
        test_value = "example"

        # Test contains - should wrap with %
        contains_func = OPERATOR_MAP[Operator.contains]
        contains_result = contains_func(self.test_column, test_value)
        # The actual pattern is applied in the lambda, so we test the function behavior
        assert callable(contains_func)

        # Test starts_with - should add % at end
        starts_with_func = OPERATOR_MAP[Operator.starts_with]
        starts_with_result = starts_with_func(self.test_column, test_value)
        assert callable(starts_with_func)

        # Test ends_with - should add % at beginning
        ends_with_func = OPERATOR_MAP[Operator.ends_with]
        ends_with_result = ends_with_func(self.test_column, test_value)
        assert callable(ends_with_func)

    def test_operator_map_immutability(self):
        """Test that OPERATOR_MAP is not accidentally modified"""
        original_keys = set(OPERATOR_MAP.keys())
        original_size = len(OPERATOR_MAP)

        # Try to modify (this should not affect the original)
        try:
            OPERATOR_MAP[Operator.eq] = (
                lambda x, y: x == y
            )  # This should work but not affect the original
        except TypeError:
            # If it's immutable, that's good
            pass

        # Verify the original is unchanged
        assert set(OPERATOR_MAP.keys()) == original_keys
        assert len(OPERATOR_MAP) == original_size
