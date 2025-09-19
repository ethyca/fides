import re
import types
from unittest.mock import Mock, create_autospec, patch

import pytest
from pytest import param
from sqlalchemy import ARRAY, Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from fides.api.task.conditional_dependencies.schemas import Operator
from fides.api.task.conditional_dependencies.sql_schemas import (
    OPERATOR_MAP,
    FieldAddress,
    SQLTranslationError,
    _escape_like_pattern,
    _handle_list_contains,
    _validate_and_escape_json_path_component,
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

        real_column = Column(String, name="test_column")

        # Mock the contains and like methods on the real column
        with (
            patch.object(real_column, "contains") as mock_contains,
            patch.object(real_column, "like") as mock_like,
        ):

            mock_contains.side_effect = Exception("Contains not supported")
            mock_like.return_value = "LIKE result"

            result = _handle_list_contains(real_column, "test_value")

            # Should fallback to LIKE with escaped pattern
            mock_contains.assert_called_once_with("test_value")
            mock_like.assert_called_once_with("%test\\_value%", escape="\\")
            assert result == "LIKE result"

    def test_multiple_list_contains_unique_parameters(self):
        """Test that multiple list_contains operations generate unique parameter names"""

        # Create array columns to trigger the parameter binding path
        array_column_1 = Column(ARRAY(Integer), name="array_col_1")
        array_column_2 = Column(ARRAY(Integer), name="array_col_2")

        # Call _handle_list_contains multiple times with single values
        result_1 = _handle_list_contains(array_column_1, 42)
        result_2 = _handle_list_contains(array_column_2, 99)

        # Both should return valid expressions
        assert result_1 is not None
        assert result_2 is not None

        # Convert to strings to inspect the generated SQL
        sql_1 = str(result_1)
        sql_2 = str(result_2)

        # Both should contain different parameter names (no conflict)
        # Extract parameter names from the SQL strings
        param_pattern = r"array_val_[a-f0-9]{8}"

        params_1 = re.findall(param_pattern, sql_1)
        params_2 = re.findall(param_pattern, sql_2)

        # Should have found parameters in both
        assert len(params_1) > 0, f"No unique parameters found in: {sql_1}"
        assert len(params_2) > 0, f"No unique parameters found in: {sql_2}"

        # Parameters should be different to avoid conflicts
        if params_1 and params_2:
            assert (
                params_1[0] != params_2[0]
            ), f"Parameter names should be unique: {params_1[0]} vs {params_2[0]}"


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
                "collection",
                ["field"],
                "dataset:collection:field",
                "collection->>'field'",
                "collection",
                id="simple_table_column_with_colons",
            ),
            param(
                "dataset:collection.field",
                "dataset",
                "collection",
                ["field"],
                "dataset:collection.field",
                "collection->>'field'",
                "collection",
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

    def test_parse_parts_to_components_empty_list(self):
        """Test _parse_parts_to_components with empty list"""
        table_name, column_name, json_path = FieldAddress._parse_parts_to_components([])
        assert table_name == ""
        assert column_name == ""
        assert json_path is None

    def test_parse_parts_to_components_single_part(self):
        """Test _parse_parts_to_components with single part"""
        table_name, column_name, json_path = FieldAddress._parse_parts_to_components(
            ["column"]
        )
        assert table_name == ""
        assert column_name == "column"
        assert json_path is None

    def test_parse_parts_to_components_two_parts(self):
        """Test _parse_parts_to_components with two parts"""
        table_name, column_name, json_path = FieldAddress._parse_parts_to_components(
            ["table", "column"]
        )
        assert table_name == "table"
        assert column_name == "column"
        assert json_path is None

    def test_parse_parts_to_components_multiple_parts(self):
        """Test _parse_parts_to_components with multiple parts"""
        table_name, column_name, json_path = FieldAddress._parse_parts_to_components(
            ["table", "column", "path1", "path2"]
        )
        assert table_name == "table"
        assert column_name == "column"
        assert json_path == ["path1", "path2"]

    @pytest.mark.parametrize(
        "field_address, expected_table_name, expected_column_name, expected_json_path",
        [
            param(":", "", "", None, id="single_colon"),
            param("table:", "table", "", None, id="table_with_trailing_colon"),
            param(":column", "", "column", None, id="leading_colon"),
            param(
                "table:column:path1:path2:path3",
                "table",
                "column",
                ["path1", "path2", "path3"],
                id="many_colons",
            ),
            param(
                "table:column.path1.path2",
                "table",
                "column",
                ["path1", "path2"],
                id="colon_then_dots",
            ),
            param(
                "table:column.path1:path2",
                "table",
                "column",
                ["path1:path2"],
                id="mixed_colon_dot_colon",
            ),
        ],
    )
    def test_complex_parsing_edge_cases(
        self,
        field_address,
        expected_table_name,
        expected_column_name,
        expected_json_path,
    ):
        """Test complex parsing edge cases"""
        field_addr = FieldAddress.parse(field_address)
        assert field_addr.table_name == expected_table_name
        assert field_addr.column_name == expected_column_name
        assert field_addr.json_path == expected_json_path
        assert field_addr.full_address == field_address


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
            param(
                Operator.contains,
                "test_column LIKE :test_column_1 ESCAPE '\\'",
                id="contains",
            ),
            param(
                Operator.starts_with,
                "test_column LIKE :test_column_1 ESCAPE '\\'",
                id="starts_with",
            ),
            param(
                Operator.ends_with,
                "test_column LIKE :test_column_1 ESCAPE '\\'",
                id="ends_with",
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
        """Test that OPERATOR_MAP is truly immutable"""
        # Verify OPERATOR_MAP is a MappingProxyType (immutable)
        assert isinstance(OPERATOR_MAP, types.MappingProxyType)

        original_keys = set(OPERATOR_MAP.keys())
        original_size = len(OPERATOR_MAP)
        # Test the original behavior
        original_eq_result = str(
            OPERATOR_MAP[Operator.eq](self.test_column, "test_value")
        )

        # Try to modify - this should raise TypeError since it's immutable
        with pytest.raises(TypeError, match="does not support item assignment"):
            OPERATOR_MAP[Operator.eq] = lambda x, y: x == y

        # Try to clear - this should also raise TypeError
        with pytest.raises(AttributeError):
            OPERATOR_MAP.clear()

        # Try to update - this should also raise AttributeError
        with pytest.raises(AttributeError):
            OPERATOR_MAP.update({})

        # Verify the original is unchanged (should be identical)
        assert set(OPERATOR_MAP.keys()) == original_keys
        assert len(OPERATOR_MAP) == original_size
        # Verify the function behavior is the same
        current_eq_result = str(
            OPERATOR_MAP[Operator.eq](self.test_column, "test_value")
        )
        assert current_eq_result == original_eq_result


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


class TestSecurityFeatures:
    """Test security features for preventing injection attacks"""

    class TestLikePatternEscaping:
        """Test LIKE pattern escaping to prevent wildcard injection"""

        test_column = Column(String, name="test_column")

        @pytest.mark.parametrize(
            "input_val,expected_escaped",
            [
                param("normal_text", "normal\\_text", id="normal_text"),
                param("admin%", "admin\\%", id="wildcard_percent"),
                param("test_user", "test\\_user", id="wildcard_underscore"),
                param("admin%_attack", "admin\\%\\_attack", id="both_wildcards"),
                param("path\\injection", "path\\\\injection", id="backslash_escape"),
                param("complex%_\\test", "complex\\%\\_\\\\test", id="complex_pattern"),
                param("", "", id="empty_string"),
                param(None, "", id="none_value"),
                param(123, "123", id="numeric_value"),
                param("%%__%%", "\\%\\%\\_\\_\\%\\%", id="multiple_wildcards"),
            ],
        )
        def test_escape_like_pattern(self, input_val, expected_escaped):
            """Test that LIKE wildcards are properly escaped"""
            result = _escape_like_pattern(input_val)
            assert result == expected_escaped

        @pytest.mark.parametrize(
            "operator,malicious_input",
            [
                param(Operator.contains, "admin%", id="contains_wildcard_percent"),
                param(Operator.contains, "user_", id="contains_wildcard_underscore"),
                param(
                    Operator.contains,
                    "%' OR '1'='1",
                    id="contains_sql_injection_attempt",
                ),
                param(Operator.starts_with, "admin%", id="starts_with_wildcard"),
                param(Operator.starts_with, "test_", id="starts_with_underscore"),
                param(Operator.ends_with, "%admin", id="ends_with_wildcard"),
                param(Operator.ends_with, "_user", id="ends_with_underscore"),
            ],
        )
        def test_operator_map_escapes_like_patterns(self, operator, malicious_input):
            """Test that OPERATOR_MAP properly escapes malicious LIKE patterns"""
            operator_func = OPERATOR_MAP[operator]
            result = operator_func(self.test_column, malicious_input)

            # Extract the pattern from the LIKE clause
            like_pattern = str(result.right.value)

            # Verify that wildcards are escaped
            assert "\\%" in like_pattern or "%" not in malicious_input
            assert "\\_" in like_pattern or "_" not in malicious_input

            # Verify escape character is set
            assert result.modifiers.get("escape") == "\\"

        def test_like_escaping_prevents_unintended_matches(self):
            """Test that escaping prevents unintended wildcard matching"""
            # Test case where unescaped % would match everything
            malicious_pattern = "admin%"
            escaped_result = _escape_like_pattern(malicious_pattern)

            # The escaped version should only match literal "admin%" not "admin*"
            assert escaped_result == "admin\\%"

            # Test case where unescaped _ would match any single character
            malicious_underscore = "test_user"
            escaped_underscore = _escape_like_pattern(malicious_underscore)

            # The escaped version should only match literal "test_user" not "testXuser"
            assert escaped_underscore == "test\\_user"

        def test_handle_list_contains_escapes_like_fallback(self):
            """Test that _handle_list_contains escapes LIKE patterns in fallback case"""
            # Mock a column that doesn't support contains() to trigger LIKE fallback
            mock_column = create_autospec(Column, instance=True)
            mock_column.contains.side_effect = Exception("Not supported")

            malicious_value = "admin%_attack"

            # Mock the like method to capture what pattern is used
            mock_like_result = Mock()
            mock_column.like.return_value = mock_like_result

            result = _handle_list_contains(mock_column, malicious_value)

            # Verify like was called with escaped pattern
            expected_escaped = "admin\\%\\_attack"
            mock_column.like.assert_called_once_with(
                f"%{expected_escaped}%", escape="\\"
            )
            assert result == mock_like_result

    class TestJsonPathSecurity:
        """Test JSON path component validation and escaping"""

        @pytest.mark.parametrize(
            "component,expected_escaped",
            [
                param("normal_field", "normal_field", id="normal_field"),
                param("field'name", "field''name", id="single_quote_escape"),
                param("field''name", "field''''name", id="double_quote_escape"),
                param(
                    "field'with'multiple'quotes",
                    "field''with''multiple''quotes",
                    id="multiple_quotes",
                ),
                param("field123", "field123", id="alphanumeric"),
                param(
                    "field_with_underscores", "field_with_underscores", id="underscores"
                ),
                param("field-with-dashes", "field-with-dashes", id="dashes"),
            ],
        )
        def test_validate_and_escape_json_path_component_valid(
            self, component, expected_escaped
        ):
            """Test that valid JSON path components are properly escaped"""
            result = _validate_and_escape_json_path_component(component)
            assert result == expected_escaped

        @pytest.mark.parametrize(
            "invalid_component,expected_error_pattern",
            [
                param("", "Invalid JSON path component.*non-empty", id="empty_string"),
                param(None, "Invalid JSON path component.*non-empty", id="none_value"),
                param(
                    123, "Invalid JSON path component.*non-empty", id="numeric_value"
                ),
                param("a" * 101, "JSON path component too long", id="too_long"),
            ],
        )
        def test_validate_and_escape_json_path_component_invalid(
            self, invalid_component, expected_error_pattern
        ):
            """Test that invalid JSON path components raise appropriate errors"""
            with pytest.raises(SQLTranslationError, match=expected_error_pattern):
                _validate_and_escape_json_path_component(invalid_component)

        def test_field_address_to_sql_column_escapes_json_paths(self):
            """Test that FieldAddress.to_sql_column() properly escapes JSON path components"""
            # Test single component with quote
            addr1 = FieldAddress(
                table_name="users",
                column_name="profile",
                json_path=["field'name"],
                full_address="users.profile.field'name",
            )
            result1 = addr1.to_sql_column()
            assert result1 == "profile->>'field''name'"

            # Test multiple components with quotes
            addr2 = FieldAddress(
                table_name="users",
                column_name="data",
                json_path=["user'info", "contact'details", "email'address"],
                full_address="users.data.user'info.contact'details.email'address",
            )
            result2 = addr2.to_sql_column()
            expected = "data->'user''info'->'contact''details'->>'email''address'"
            assert result2 == expected

        def test_field_address_validates_json_path_components(self):
            """Test that FieldAddress validates JSON path components during SQL generation"""
            # Test with invalid component
            addr = FieldAddress(
                table_name="users",
                column_name="profile",
                json_path=[""],  # Empty component
                full_address="users.profile.",
            )

            with pytest.raises(
                SQLTranslationError, match="Invalid JSON path component"
            ):
                addr.to_sql_column()

        def test_json_path_injection_prevention(self):
            """Test that JSON path injection attempts are prevented"""
            # Attempt to inject SQL through JSON path
            malicious_paths = [
                "field'; DROP TABLE users; --",
                "field' OR '1'='1",
                "field'; SELECT * FROM secrets; --",
            ]

            for malicious_path in malicious_paths:
                addr = FieldAddress(
                    table_name="users",
                    column_name="data",
                    json_path=[malicious_path],
                    full_address=f"users.data.{malicious_path}",
                )

                # The escaped result should have quotes doubled, making injection impossible
                result = addr.to_sql_column()

                # Verify the malicious content is escaped (quotes are doubled)
                assert malicious_path.replace("'", "''") in result
                # Verify no unescaped single quotes remain that could break out
                # The pattern should be: ->>'escaped_content'
                assert re.match(
                    r"data->>'[^']*(?:''[^']*)*'$", result
                ), f"Malicious injection not properly escaped: {result}"

    class TestIntegratedSecurityScenarios:
        """Test security in realistic usage scenarios"""

        def test_sql_injection_through_like_operators_prevented(self):
            """Test that SQL injection attempts through LIKE operators are prevented"""
            test_column = Column(String, name="email")

            # Common SQL injection payloads that might be attempted through LIKE operators
            injection_attempts = [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "' UNION SELECT password FROM users --",
                "%' OR username='admin",
                "_' OR '1'='1' --",
            ]

            for payload in injection_attempts:
                # Test each LIKE-based operator
                for operator in [
                    Operator.contains,
                    Operator.starts_with,
                    Operator.ends_with,
                ]:
                    operator_func = OPERATOR_MAP[operator]
                    result = operator_func(test_column, payload)

                    # The result should be a proper SQLAlchemy expression with escaped pattern
                    assert hasattr(result, "left")  # Column part
                    assert hasattr(result, "right")  # Value part
                    assert hasattr(
                        result, "modifiers"
                    )  # Should include escape character

                    # Verify escape character is set
                    assert result.modifiers.get("escape") == "\\"

                    # The pattern should be escaped
                    pattern = str(result.right.value)
                    # Single quotes in the payload should be escaped as literals, not SQL
                    if "'" in payload:
                        # The quotes should be treated as literal characters in the LIKE pattern
                        # They should not be able to break out of the parameter binding
                        assert (
                            "'" in pattern
                        )  # The literal quotes should still be there
                        # But they should be in a parameterized context, not as SQL syntax

        def test_json_path_and_like_combination_security(self):
            """Test security when JSON paths and LIKE operations are combined"""
            # Create a field address with potentially malicious JSON path
            malicious_json_path = "field'; DROP TABLE users; --"

            addr = FieldAddress(
                table_name="users",
                column_name="profile",
                json_path=[malicious_json_path],
                full_address=f"users.profile.{malicious_json_path}",
            )

            # Generate the SQL column reference
            sql_column = addr.to_sql_column()

            # The malicious content should be escaped
            expected_escaped = malicious_json_path.replace("'", "''")
            assert expected_escaped in sql_column

            # The final SQL should be safe - verify it follows expected pattern
            expected_pattern = f"profile->>'{expected_escaped}'"
            assert expected_pattern == sql_column
