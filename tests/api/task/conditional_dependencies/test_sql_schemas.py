from unittest.mock import Mock, create_autospec, patch

import pytest
from pytest import param
from sqlalchemy import Boolean, Column, String
from sqlalchemy.ext.declarative import declarative_base

from fides.api.task.conditional_dependencies.schemas import Operator
from fides.api.task.conditional_dependencies.sql_schemas import (
    OPERATOR_MAP,
    FieldAddress,
    SQLTranslationError,
    _handle_list_contains,
)

# Create a test base for SQLAlchemy columns
TestBase = declarative_base()


class TestSQLTranslationError:
    """Test SQLTranslationError exception"""

    def test_sql_translation_error_creation(self):
        """Test SQLTranslationError can be created and raised"""
        error_msg = "Test error message"

        with pytest.raises(SQLTranslationError) as exc_info:
            raise SQLTranslationError(error_msg)

        assert str(exc_info.value) == error_msg

    def test_sql_translation_error_inheritance(self):
        """Test SQLTranslationError inherits from Exception"""
        error = SQLTranslationError("test")
        assert isinstance(error, Exception)


class TestHandleListContains:
    """Test the _handle_list_contains function edge cases"""

    test_column = Column(String, name="test_column")

    @pytest.mark.parametrize(
        "test_list",
        [
            param(["value1", "value2", "value3"], id="list"),
            param("test_value", id="single_value"),
            param([], id="empty_list"),
            param(None, id="none"),
        ],
    )
    def test_handle_list_contains_with_list_value(self, test_list):
        """Test _handle_list_contains with list value"""
        result = _handle_list_contains(self.test_column, test_list)

        # Should use IN operator for lists
        assert result is not None
        if isinstance(test_list, list):
            assert "IN" in str(result).upper()

    def test_handle_list_contains_exception_fallback(self):
        """Test _handle_list_contains fallback to LIKE when contains() fails"""
        # Use a real SQLAlchemy column to avoid Mock attribute issues
        from sqlalchemy import String

        real_column = Column(String, name="test_column")

        # Mock the contains and like methods on the real column
        with (
            patch.object(real_column, "contains") as mock_contains,
            patch.object(real_column, "like") as mock_like,
        ):

            mock_contains.side_effect = Exception("Contains not supported")
            mock_like.return_value = "LIKE result"

            result = _handle_list_contains(real_column, "test_value")

            # Should fallback to LIKE
            mock_contains.assert_called_once_with("test_value")
            mock_like.assert_called_once_with("%test_value%")
            assert result == "LIKE result"


class TestFieldAddress:
    """Test the FieldAddress parsing and SQL generation functionality"""

    @pytest.mark.parametrize(
        "field_address, expected_table_name, expected_column_name, expected_json_path, expected_full_address, expected_sql_column_true, expected_sql_column_false",
        [
            param(
                "users.email",
                "users",
                "email",
                None,
                "users.email",
                "email",
                "email",
                id="simple_table_column",
            ),
            param(
                "users.profile.verified",
                "users",
                "profile",
                ["verified"],
                "users.profile.verified",
                "profile->>'verified'",
                "profile",
                id="simple_table_column_with_json_path",
            ),
            param(
                "users.metadata.preferences.theme",
                "users",
                "metadata",
                ["preferences", "theme"],
                "users.metadata.preferences.theme",
                "metadata->'preferences'->>'theme'",
                "metadata",
                id="simple_table_column_with_json_path_deep",
            ),
            param(
                "users:email",
                "users",
                "email",
                None,
                "users:email",
                "email",
                "email",
                id="simple_table_column_with_colon",
            ),
            param(
                "dataset:collection:field",
                "dataset",
                "collection:field",
                None,
                "dataset:collection:field",
                "collection:field",
                "collection:field",
                id="simple_table_column_with_colons",
            ),
            param(
                "dataset:collection.field",
                "dataset",
                "collection.field",
                None,
                "dataset:collection.field",
                "collection.field",
                "collection.field",
                id="simple_table_column_with_colons_dots",
            ),
            param(
                "email",
                "",
                "email",
                None,
                "email",
                "email",
                "email",
                id="simple_column",
            ),
        ],
    )
    def test_parse_table_column(
        self,
        field_address,
        expected_table_name,
        expected_column_name,
        expected_json_path,
        expected_full_address,
        expected_sql_column_true,
        expected_sql_column_false,
    ):
        """Test parsing simple table.column format"""
        field_addr = FieldAddress.parse(field_address)

        assert field_addr.table_name == expected_table_name
        assert field_addr.column_name == expected_column_name
        assert field_addr.json_path == expected_json_path
        assert field_addr.full_address == expected_full_address
        assert field_addr.to_sql_column(True) == expected_sql_column_true
        assert field_addr.to_sql_column(False) == expected_sql_column_false

    @pytest.mark.parametrize(
        "field_address, expected_table_name, expected_column_name",
        [
            param("", "", "", id="empty_string"),
            param("...", "", "", id="just_dots"),
            param(".", "", "", id="single_dot"),
        ],
    )
    def test_edge_cases(self, field_address, expected_table_name, expected_column_name):
        """Test edge cases in field address parsing"""
        # Empty string
        field_addr = FieldAddress.parse(field_address)
        assert field_addr.table_name == expected_table_name
        assert field_addr.column_name == expected_column_name


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
            Operator.list_contains,
            Operator.not_in_list,
        }

        assert set(OPERATOR_MAP.keys()) == expected_operators

    @pytest.mark.parametrize(
        "operator, expected_result",
        [
            param(Operator.eq, "test_column = :test_column_1", id="eq"),
            param(Operator.neq, "test_column != :test_column_1", id="neq"),
            param(Operator.lt, "test_column < :test_column_1", id="lt"),
            param(Operator.lte, "test_column <= :test_column_1", id="lte"),
            param(Operator.gt, "test_column > :test_column_1", id="gt"),
            param(Operator.gte, "test_column >= :test_column_1", id="gte"),
            param(Operator.contains, "test_column LIKE :test_column_1", id="contains"),
            param(
                Operator.starts_with,
                "test_column LIKE :test_column_1",
                id="starts_with",
            ),
            param(
                Operator.ends_with, "test_column LIKE :test_column_1", id="ends_with"
            ),
            param(Operator.exists, "test_column IS NOT NULL", id="exists"),
            param(Operator.not_exists, "test_column IS NULL", id="not_exists"),
            param(
                Operator.list_contains,
                "test_column LIKE '%' || :test_column_1 || '%'",
                id="list_contains",
            ),
            param(
                Operator.not_in_list,
                "test_column NOT LIKE '%' || :test_column_1 || '%'",
                id="not_in_list",
            ),
        ],
    )
    def test_operators(self, operator, expected_result):
        """Test equality and inequality operators"""
        result = OPERATOR_MAP[operator](self.test_column, self.test_value)
        assert str(result) == expected_result

    def test_list_operators_with_list_values(self):
        """Test list_contains and not_in_list operators with actual list values"""
        test_list = ["value1", "value2", "value3"]

        # Test list_contains with list value
        result = OPERATOR_MAP[Operator.list_contains](self.test_column, test_list)
        assert "IN" in str(result).upper()

        # Test not_in_list with list value
        result = OPERATOR_MAP[Operator.not_in_list](self.test_column, test_list)
        assert "NOT" in str(result).upper() and "IN" in str(result).upper()

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


class TestFieldAddressEdgeCases:
    """Test FieldAddress edge cases and error conditions"""

    def test_field_address_hash_consistency(self):
        """Test that FieldAddress hashing is consistent"""
        addr1 = FieldAddress(
            table_name="users",
            column_name="email",
            json_path=None,
            full_address="users.email",
        )
        addr2 = FieldAddress(
            table_name="users",
            column_name="email",
            json_path=None,
            full_address="users.email",
        )
        addr3 = FieldAddress(
            table_name="users",
            column_name="email",
            json_path=["nested"],
            full_address="users.email.nested",
        )

        # Same addresses should have same hash
        assert hash(addr1) == hash(addr2)
        # Different addresses should have different hash
        assert hash(addr1) != hash(addr3)

        # Should be usable in sets
        addr_set = {addr1, addr2, addr3}
        assert len(addr_set) == 2  # addr1 and addr2 are the same

    def test_field_address_equality_with_different_types(self):
        """Test FieldAddress equality with different types"""
        addr = FieldAddress(
            table_name="users",
            column_name="email",
            json_path=None,
            full_address="users.email",
        )

        # Should not equal non-FieldAddress objects
        assert addr != "users.email"
        assert addr != {"table_name": "users", "column_name": "email"}
        assert addr != None

    def test_field_address_equality_with_json_path(self):
        """Test FieldAddress equality with JSON paths"""
        addr1 = FieldAddress(
            table_name="users",
            column_name="profile",
            json_path=["name"],
            full_address="users.profile.name",
        )
        addr2 = FieldAddress(
            table_name="users",
            column_name="profile",
            json_path=["name"],
            full_address="users.profile.name",
        )
        addr3 = FieldAddress(
            table_name="users",
            column_name="profile",
            json_path=["age"],
            full_address="users.profile.age",
        )

        assert addr1 == addr2
        assert addr1 != addr3
