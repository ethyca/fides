import pytest
from pytest import param

from fides.api.task.conditional_dependencies.operators import operator_methods
from fides.api.task.conditional_dependencies.schemas import Operator


class TestCommonOperators:
    """Test basic comparison and existence operators"""

    @pytest.mark.parametrize(
        "data_value,operator,user_input_value,expected_result",
        [
            # Basic operators
            param("some_value", Operator.exists, None, True, id="exists"),
            param(None, Operator.exists, None, False, id="exists None"),
            param(None, Operator.not_exists, None, True, id="not_exists None"),
            param("some_value", Operator.not_exists, None, False, id="not_exists"),
            param("test", Operator.eq, "test", True, id="eq"),
            param("test", Operator.eq, "different", False, id="eq different"),
            param("test", Operator.neq, "different", True, id="neq"),
            param("test", Operator.neq, "test", False, id="neq test"),
        ],
    )
    def test_basic_operators(
        self, data_value, operator, user_input_value, expected_result
    ):
        """Test basic operators (exists, not_exists, eq, neq)"""
        result = operator_methods[operator](data_value, user_input_value)
        assert result is expected_result

    def test_edge_case_comparisons(self):
        """Test edge case comparisons"""
        assert operator_methods[Operator.eq]("", "") is True
        assert operator_methods[Operator.eq](0, 0) is True
        assert operator_methods[Operator.eq](False, False) is True


class TestNumericOperators:
    """Test numeric comparison operators"""

    @pytest.mark.parametrize(
        "data_value,operator,user_input_value,expected_result",
        [
            # Numeric comparison operators
            param(5, Operator.lt, 10, True, id="5_lt_10_success"),
            param(15, Operator.lt, 10, False, id="15_lt_10_failure"),
            param(None, Operator.lt, 10, False, id="None_lt_10_failure"),
            param(10, Operator.lte, 10, True, id="10_lte_10_success"),
            param(5, Operator.lte, 10, True, id="5_lte_10_success"),
            param(15, Operator.lte, 10, False, id="15_lte_10_failure"),
            param(15, Operator.gt, 10, True, id="15_gt_10_success"),
            param(5, Operator.gt, 10, False, id="5_gt_10_failure"),
            param(10, Operator.gte, 10, True, id="10_gte_10_success"),
            param(15, Operator.gte, 10, True, id="15_gte_10_success"),
            param(5, Operator.gte, 10, False, id="5_gte_10_failure"),
            # Additional edge cases for None values
            param(None, Operator.lte, 10, False, id="None_lte_10_failure"),
            param(None, Operator.gt, 10, False, id="None_gt_10_failure"),
            param(None, Operator.gte, 10, False, id="None_gte_10_failure"),
            # Non-numeric types with numeric operators
            param("not_a_number", Operator.lt, 10, False, id="string_lt_10_failure"),
            param(True, Operator.lt, 10, False, id="boolean_lt_10_failure"),
            param([1, 2, 3], Operator.lt, 10, False, id="list_lt_10_failure"),
        ],
    )
    def test_comparison_operators(
        self, data_value, operator, user_input_value, expected_result
    ):
        """Test comparison operators (lt, lte, gt, gte)"""
        result = operator_methods[operator](data_value, user_input_value)
        assert result is expected_result

    def test_numeric_comparisons(self):
        """Test numeric comparisons with different types"""
        # Integer comparisons
        assert operator_methods[Operator.lt](5, 10.0) is True
        assert operator_methods[Operator.eq](10.0, 10) is True
        assert operator_methods[Operator.gt](15.5, 10) is True

        # Edge cases with None and invalid types
        assert operator_methods[Operator.lt](None, 10) is False
        assert operator_methods[Operator.lt]("invalid", 10) is False
        assert operator_methods[Operator.lt](True, 10) is False


class TestStringOperators:
    """Test string-specific operators"""

    @pytest.mark.parametrize(
        "data_value,operator,user_input_value,expected_result",
        [
            # String operators
            param(
                "hello world",
                Operator.starts_with,
                "hello",
                True,
                id="starts_with_matching",
            ),
            param(
                "hello world",
                Operator.starts_with,
                "world",
                False,
                id="starts_with_non_matching",
            ),
            param(
                "hello world",
                Operator.ends_with,
                "world",
                True,
                id="ends_with_matching",
            ),
            param(
                "hello world",
                Operator.ends_with,
                "hello",
                False,
                id="ends_with_non_matching",
            ),
            param(
                "hello world",
                Operator.contains,
                "lo wo",
                True,
                id="contains_matching",
            ),
            param(
                "hello world",
                Operator.contains,
                "xyz",
                False,
                id="contains_non_matching",
            ),
            param(
                None,
                Operator.starts_with,
                "hello",
                False,
                id="starts_with_none",
            ),
            param(
                123,
                Operator.starts_with,
                "123",
                False,
                id="starts_with_non_string",
            ),
            param(
                "",
                Operator.starts_with,
                "hello",
                False,
                id="starts_with_empty_string",
            ),
            param(
                "hello world",
                Operator.starts_with,
                "",
                True,
                id="starts_with_empty_prefix",
            ),
            param(
                "hello world",
                Operator.ends_with,
                "",
                True,
                id="ends_with_empty_suffix",
            ),
            param(
                "hello world",
                Operator.contains,
                "",
                True,
                id="contains_empty_substring",
            ),
            # Additional edge cases for None values
            param(
                None,
                Operator.ends_with,
                "world",
                False,
                id="ends_with_none",
            ),
            param(
                None,
                Operator.contains,
                "hello",
                False,
                id="contains_none",
            ),
            # Non-string types with string operators
            param(
                123,
                Operator.ends_with,
                "123",
                False,
                id="ends_with_non_string",
            ),
            param(
                123,
                Operator.contains,
                "123",
                False,
                id="contains_non_string",
            ),
            param(
                True,
                Operator.starts_with,
                "True",
                False,
                id="starts_with_boolean",
            ),
            param(
                [1, 2, 3],
                Operator.ends_with,
                "3",
                False,
                id="ends_with_list",
            ),
        ],
    )
    def test_string_operators(
        self, data_value, operator, user_input_value, expected_result
    ):
        """Test string operators (starts_with, ends_with, contains)"""
        result = operator_methods[operator](data_value, user_input_value)
        assert result == expected_result

    def test_string_comparisons(self):
        """Test string comparisons"""
        assert operator_methods[Operator.eq]("abc", "abc") is True
        assert operator_methods[Operator.neq]("abc", "def") is True
        assert operator_methods[Operator.starts_with]("hello world", "hello") is True
        assert operator_methods[Operator.ends_with]("hello world", "world") is True
        assert operator_methods[Operator.contains]("hello world", "lo wo") is True


class TestListOperators:
    """Test list membership operators"""

    @pytest.mark.parametrize(
        "data_value,operator,user_input_value,expected_result",
        [
            # List operators
            param(
                ["apple", "banana", "cherry"],
                Operator.list_contains,
                "banana",
                True,
                id="list_contains_banana",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_contains,
                "orange",
                False,
                id="list_contains_orange",
            ),
            param(
                [1, 3, 5, 7, 9], Operator.list_contains, 5, True, id="list_contains_5"
            ),
            param(
                [1, "test", True, 3.14],
                Operator.list_contains,
                True,
                True,
                id="list_contains_True",
            ),
            param(
                [],
                Operator.list_contains,
                "anything",
                False,
                id="list_contains_anything",
            ),
            param(
                "not_a_list",
                Operator.list_contains,
                "test",
                False,
                id="list_contains_not_a_list",
            ),
            # Test non-empty list with empty list
            param(
                ["apple", "banana"],
                Operator.list_contains,
                [],
                False,
                id="list_contains_non_empty_empty_list",
            ),
            param(None, Operator.list_contains, "test", False, id="list_contains_None"),
            param(
                ["apple", "banana", "cherry"],
                Operator.not_in_list,
                "orange",
                True,
                id="not_in_list_orange",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.not_in_list,
                "apple",
                False,
                id="not_in_list_apple",
            ),
            param(
                [],
                Operator.not_in_list,
                "anything",
                True,
                id="not_in_list_anything",
            ),
            param(
                "anything",
                Operator.not_in_list,
                [],
                True,
                id="not_in_list_empty_list",
            ),
            # Additional empty list edge cases
            param(
                [],
                Operator.list_contains,
                None,
                False,
                id="list_contains_empty_list_none",
            ),
            param(
                [],
                Operator.list_contains,
                0,
                False,
                id="list_contains_empty_list_zero",
            ),
            param(
                [],
                Operator.list_contains,
                False,
                False,
                id="list_contains_empty_list_false",
            ),
            # Test empty list with empty list (bidirectional behavior)
            param(
                [],
                Operator.list_contains,
                [],
                False,
                id="list_contains_empty_list_empty_list",
            ),
            param(
                [],
                Operator.not_in_list,
                None,
                True,
                id="not_in_list_empty_list_none",
            ),
            param(
                [],
                Operator.not_in_list,
                0,
                True,
                id="not_in_list_empty_list_zero",
            ),
            param(
                [],
                Operator.not_in_list,
                False,
                True,
                id="not_in_list_empty_list_false",
            ),
            # Test empty list with empty list (bidirectional behavior)
            param(
                [],
                Operator.not_in_list,
                [],
                True,
                id="not_in_list_empty_list_empty_list",
            ),
            param(
                "not_a_list",
                Operator.not_in_list,
                "test",
                False,
                id="not_in_list_test_no_list",
            ),
            # Test None values in list operations
            param(
                None,
                Operator.list_contains,
                ["test", None],
                True,
                id="list_contains_none_in_list",
            ),
            param(
                None,
                Operator.not_in_list,
                ["test"],
                True,
                id="not_in_list_none_not_in_list",
            ),
            # Test non-empty list with empty list
            param(
                ["apple", "banana"],
                Operator.not_in_list,
                [],
                True,
                id="not_in_list_non_empty_empty_list",
            ),
            # Additional edge cases for None values
            param(
                None,
                Operator.not_in_list,
                ["test"],
                True,
                id="not_in_list_None",
            ),
            # Test with mixed data types in lists
            param(
                ["apple", 123, True, None],
                Operator.list_contains,
                None,
                True,
                id="list_contains_mixed_types_none",
            ),
            param(
                ["apple", 123, True, None],
                Operator.not_in_list,
                None,
                False,
                id="not_in_list_mixed_types_none",
            ),
            param(
                ["apple", 123, True, None],
                Operator.list_contains,
                123,
                True,
                id="list_contains_mixed_types_number",
            ),
            param(
                ["apple", 123, True, None],
                Operator.not_in_list,
                "orange",
                True,
                id="not_in_list_mixed_types",
            ),
            # Test with duplicate elements
            param(
                ["apple", "apple", "banana"],
                Operator.list_contains,
                "apple",
                True,
                id="list_contains_duplicate",
            ),
            param(
                ["apple", "apple", "banana"],
                Operator.not_in_list,
                "cherry",
                True,
                id="not_in_list_duplicate",
            ),
        ],
    )
    def test_list_operators(
        self, data_value, operator, user_input_value, expected_result
    ):
        """Test list operators (list_contains, not_in_list)"""
        result = operator_methods[operator](data_value, user_input_value)
        assert result == expected_result

    def test_bidirectional_list_operators(self):
        """Test that list operators work in both directions"""
        # Test list_contains - user provides list, check if column value is in it
        assert (
            operator_methods[Operator.list_contains]("admin", ["admin", "user"]) is True
        )
        assert (
            operator_methods[Operator.list_contains]("guest", ["admin", "user"])
            is False
        )

        # Test list_contains - column value is list, check if user value is in it
        assert (
            operator_methods[Operator.list_contains](["admin", "user"], "admin") is True
        )
        assert (
            operator_methods[Operator.list_contains](["admin", "user"], "guest")
            is False
        )

        # Test not_in_list - user provides list, check if column value is NOT in it
        assert (
            operator_methods[Operator.not_in_list]("admin", ["banned", "suspended"])
            is True
        )
        assert (
            operator_methods[Operator.not_in_list]("banned", ["banned", "suspended"])
            is False
        )

        # Test not_in_list - column value is list, check if user value is NOT in it
        assert (
            operator_methods[Operator.not_in_list](["admin", "user"], "banned") is True
        )
        assert (
            operator_methods[Operator.not_in_list](["admin", "banned"], "banned")
            is False
        )


class TestAdvancedListOperators:
    """Test advanced list-to-list comparison operators"""

    @pytest.mark.parametrize(
        "data_value,operator,user_input_value,expected_result",
        [
            # Test list_intersects operator
            param(
                ["apple", "banana", "cherry"],
                Operator.list_intersects,
                ["banana", "orange"],
                True,
                id="list_intersects_common_elements",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_intersects,
                ["orange", "grape"],
                False,
                id="list_intersects_no_common_elements",
            ),
            param(
                [1, 3, 5, 7, 9],
                Operator.list_intersects,
                [2, 4, 6, 8, 10],
                False,
                id="list_intersects_numbers_no_common",
            ),
            param(
                [1, 3, 5, 7, 9],
                Operator.list_intersects,
                [5, 10, 15],
                True,
                id="list_intersects_numbers_common",
            ),
            param(
                [],
                Operator.list_intersects,
                ["anything"],
                False,
                id="list_intersects_empty_first",
            ),
            param(
                ["anything"],
                Operator.list_intersects,
                [],
                False,
                id="list_intersects_empty_second",
            ),
            param(
                "not_a_list",
                Operator.list_intersects,
                ["test"],
                False,
                id="list_intersects_not_a_list_first",
            ),
            param(
                ["test"],
                Operator.list_intersects,
                "not_a_list",
                False,
                id="list_intersects_not_a_list_second",
            ),
            param(
                None,
                Operator.list_intersects,
                ["test"],
                False,
                id="list_intersects_none_first",
            ),
            param(
                ["test"],
                Operator.list_intersects,
                None,
                False,
                id="list_intersects_none_second",
            ),
            # Test list_subset operator
            param(
                ["apple", "banana"],
                Operator.list_subset,
                ["apple", "banana", "cherry"],
                True,
                id="list_subset_proper_subset",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_subset,
                ["apple", "banana", "cherry"],
                True,
                id="list_subset_equal_sets",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_subset,
                ["apple", "banana"],
                False,
                id="list_subset_not_subset",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_subset,
                ["orange", "grape"],
                False,
                id="list_subset_completely_different",
            ),
            param(
                [],
                Operator.list_subset,
                ["anything"],
                True,
                id="list_subset_empty_first",
            ),
            param(
                ["anything"],
                Operator.list_subset,
                [],
                False,
                id="list_subset_empty_second",
            ),
            # Test list_superset operator
            param(
                ["apple", "banana", "cherry"],
                Operator.list_superset,
                ["apple", "banana"],
                True,
                id="list_superset_proper_superset",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_superset,
                ["apple", "banana", "cherry"],
                True,
                id="list_superset_equal_sets",
            ),
            param(
                ["apple", "banana"],
                Operator.list_superset,
                ["apple", "banana", "cherry"],
                False,
                id="list_superset_not_superset",
            ),
            param(
                ["apple", "banana"],
                Operator.list_superset,
                ["orange", "grape"],
                False,
                id="list_superset_completely_different",
            ),
            param(
                [],
                Operator.list_superset,
                ["anything"],
                False,
                id="list_superset_empty_first",
            ),
            param(
                ["anything"],
                Operator.list_superset,
                [],
                True,
                id="list_superset_empty_second",
            ),
            # Test list_disjoint operator
            param(
                ["apple", "banana", "cherry"],
                Operator.list_disjoint,
                ["orange", "grape"],
                True,
                id="list_disjoint_no_common_elements",
            ),
            param(
                ["apple", "banana", "cherry"],
                Operator.list_disjoint,
                ["banana", "orange"],
                False,
                id="list_disjoint_has_common_elements",
            ),
            param(
                [1, 3, 5, 7, 9],
                Operator.list_disjoint,
                [2, 4, 6, 8, 10],
                True,
                id="list_disjoint_numbers_no_common",
            ),
            param(
                [1, 3, 5, 7, 9],
                Operator.list_disjoint,
                [5, 10, 15],
                False,
                id="list_disjoint_numbers_has_common",
            ),
            param(
                [],
                Operator.list_disjoint,
                ["anything"],
                True,
                id="list_disjoint_empty_first",
            ),
            param(
                ["anything"],
                Operator.list_disjoint,
                [],
                True,
                id="list_disjoint_empty_second",
            ),
            param(
                [],
                Operator.list_disjoint,
                [],
                True,
                id="list_disjoint_both_empty",
            ),
            # Both lists empty edge cases
            param(
                [],
                Operator.list_intersects,
                [],
                False,
                id="list_intersects_both_empty",
            ),
            param(
                [],
                Operator.list_subset,
                [],
                True,
                id="list_subset_both_empty",
            ),
            param(
                [],
                Operator.list_superset,
                [],
                True,
                id="list_superset_both_empty",
            ),
            # Additional edge cases for None values
            param(
                None,
                Operator.list_subset,
                ["test"],
                False,
                id="list_subset_none_first",
            ),
            param(
                ["test"],
                Operator.list_subset,
                None,
                False,
                id="list_subset_none_second",
            ),
            param(
                None,
                Operator.list_superset,
                ["test"],
                False,
                id="list_superset_none_first",
            ),
            param(
                ["test"],
                Operator.list_superset,
                None,
                False,
                id="list_superset_none_second",
            ),
            # Test with mixed data types in lists
            param(
                ["apple", 123, True, None],
                Operator.list_intersects,
                ["banana", 123, False],
                True,
                id="list_intersects_mixed_types_common",
            ),
            param(
                ["apple", 123, True, None],
                Operator.list_subset,
                ["apple", 123, True, None, "extra"],
                True,
                id="list_subset_mixed_types",
            ),
            param(
                ["apple", 123, True, None, "extra"],
                Operator.list_superset,
                ["apple", 123, True, None],
                True,
                id="list_superset_mixed_types",
            ),
            param(
                ["apple", 123, True, None],
                Operator.list_disjoint,
                ["banana", 456, False],
                True,
                id="list_disjoint_mixed_types",
            ),
        ],
    )
    def test_advanced_list_operators(
        self, data_value, operator, user_input_value, expected_result
    ):
        """Test advanced list operators (list_intersects, list_subset, list_superset, list_disjoint)"""
        result = operator_methods[operator](data_value, user_input_value)
        assert result == expected_result

    def test_empty_list_edge_cases(self):
        """Test edge cases with empty lists"""
        # Empty lists should work correctly with all operators
        assert operator_methods[Operator.list_contains]([], "anything") is False
        assert operator_methods[Operator.not_in_list]([], "anything") is True

        # Empty list subset/superset relationships
        assert operator_methods[Operator.list_subset]([], ["anything"]) is True
        assert operator_methods[Operator.list_superset](["anything"], []) is True

        # Empty lists are disjoint
        assert operator_methods[Operator.list_disjoint]([], ["anything"]) is True
        assert operator_methods[Operator.list_disjoint](["anything"], []) is True
        assert operator_methods[Operator.list_disjoint]([], []) is True

        # Empty lists don't intersect
        assert operator_methods[Operator.list_intersects]([], ["anything"]) is False
        assert operator_methods[Operator.list_intersects](["anything"], []) is False

    def test_comprehensive_empty_list_scenarios(self):
        """Test comprehensive empty list scenarios with all operators"""
        # Test empty list with different data types
        empty_list = []

        # list_contains with empty list
        assert operator_methods[Operator.list_contains](empty_list, None) is False
        assert operator_methods[Operator.list_contains](empty_list, 0) is False
        assert operator_methods[Operator.list_contains](empty_list, False) is False
        assert operator_methods[Operator.list_contains](empty_list, "") is False
        assert operator_methods[Operator.list_contains](empty_list, []) is False

        # not_in_list with empty list
        assert operator_methods[Operator.not_in_list](empty_list, None) is True
        assert operator_methods[Operator.not_in_list](empty_list, 0) is True
        assert operator_methods[Operator.not_in_list](empty_list, False) is True
        assert operator_methods[Operator.not_in_list](empty_list, "") is True
        assert operator_methods[Operator.not_in_list](empty_list, []) is True

        # Test non-empty list with empty list
        non_empty_list = ["apple", "banana"]

        # list_contains with empty list
        assert operator_methods[Operator.list_contains](non_empty_list, []) is False
        assert operator_methods[Operator.list_contains](non_empty_list, []) is False

        # not_in_list with empty list
        assert operator_methods[Operator.not_in_list](non_empty_list, []) is True
        assert operator_methods[Operator.not_in_list](non_empty_list, []) is True

        # Test empty list with empty list for all advanced operators
        assert operator_methods[Operator.list_intersects]([], []) is False
        assert operator_methods[Operator.list_subset]([], []) is True
        assert operator_methods[Operator.list_superset]([], []) is True
        assert operator_methods[Operator.list_disjoint]([], []) is True


class TestBooleanOperators:
    """Test boolean comparison operators"""

    def test_boolean_comparisons(self):
        """Test boolean comparisons"""
        assert operator_methods[Operator.eq](True, True) is True
        assert operator_methods[Operator.eq](False, False) is True
        assert operator_methods[Operator.neq](True, False) is True


class TestTypeCompatibility:
    """Test operator behavior with different data types and edge cases"""

    def test_none_with_all_operators(self):
        """Test that None values are handled correctly with all operators"""
        # Basic operators
        assert operator_methods[Operator.exists](None, None) is False
        assert operator_methods[Operator.not_exists](None, None) is True

        # Comparison operators
        assert operator_methods[Operator.eq](None, "test") is False
        assert operator_methods[Operator.neq](None, "test") is True

        # Numeric operators
        assert operator_methods[Operator.lt](None, 10) is False
        assert operator_methods[Operator.lte](None, 10) is False
        assert operator_methods[Operator.gt](None, 10) is False
        assert operator_methods[Operator.gte](None, 10) is False

        # String operators
        assert operator_methods[Operator.starts_with](None, "test") is False
        assert operator_methods[Operator.ends_with](None, "test") is False
        assert operator_methods[Operator.contains](None, "test") is False

        # List operators
        assert operator_methods[Operator.list_contains](None, ["test"]) is False
        assert operator_methods[Operator.not_in_list](None, ["test"]) is True
        assert operator_methods[Operator.list_intersects](None, ["test"]) is False
        assert operator_methods[Operator.list_subset](None, ["test"]) is False
        assert operator_methods[Operator.list_superset](None, ["test"]) is False
        assert operator_methods[Operator.list_disjoint](None, ["test"]) is False

    def test_invalid_types_with_operators(self):
        """Test that invalid types return False for type-specific operators"""
        # String operators with non-string types
        assert operator_methods[Operator.starts_with](123, "123") is False
        assert operator_methods[Operator.ends_with](True, "True") is False
        assert operator_methods[Operator.contains](["list"], "list") is False

        # Numeric operators with non-numeric types
        assert operator_methods[Operator.lt]("string", 10) is False
        assert operator_methods[Operator.lte](True, 10) is False
        assert operator_methods[Operator.gt](None, 10) is False
        assert operator_methods[Operator.gte](["list"], 10) is False

        # List operators with non-list types
        assert operator_methods[Operator.list_intersects]("string", ["test"]) is False
        assert operator_methods[Operator.list_subset](123, ["test"]) is False
        assert operator_methods[Operator.list_superset](True, ["test"]) is False
        assert operator_methods[Operator.list_disjoint](None, ["test"]) is False

    def test_empty_and_falsy_values(self):
        """Test behavior with empty strings, lists, and other falsy values"""
        # Empty strings
        assert operator_methods[Operator.starts_with]("", "anything") is False
        assert operator_methods[Operator.ends_with]("", "anything") is False
        assert operator_methods[Operator.contains]("", "anything") is False

        # Empty lists
        assert operator_methods[Operator.list_contains]([], "anything") is False
        assert operator_methods[Operator.not_in_list]([], "anything") is True

        # Zero values
        assert operator_methods[Operator.lt](0, 10) is True
        assert operator_methods[Operator.gt](0, -10) is True
        assert operator_methods[Operator.eq](0, 0) is True

    def test_mixed_type_comparisons(self):
        """Test comparisons between different types"""
        # String vs number
        assert operator_methods[Operator.eq]("123", 123) is False
        assert operator_methods[Operator.neq]("123", 123) is True

        # Boolean vs number - Python treats bool as a subclass of int
        assert operator_methods[Operator.eq](True, 1) is True
        assert operator_methods[Operator.neq](False, 0) is False

        # List vs string
        assert operator_methods[Operator.eq](["test"], "test") is False
        assert operator_methods[Operator.neq](["test"], "test") is True
