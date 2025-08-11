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
                "not_a_list",
                Operator.not_in_list,
                "test",
                False,
                id="not_in_list_test_no_list",
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


class TestBooleanOperators:
    """Test boolean comparison operators"""

    def test_boolean_comparisons(self):
        """Test boolean comparisons"""
        assert operator_methods[Operator.eq](True, True) is True
        assert operator_methods[Operator.eq](False, False) is True
        assert operator_methods[Operator.neq](True, False) is True
