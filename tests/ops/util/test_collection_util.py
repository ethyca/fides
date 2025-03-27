from typing import Dict, List

import pytest
from immutables import Map
from ordered_set import OrderedSet

from fides.api.common_exceptions import FidesopsException
from fides.api.util.collection_util import (
    append,
    filter_nonempty_values,
    flatten_dict,
    make_immutable,
    make_mutable,
    merge_dicts,
    partition,
    unflatten_dict,
)


def test_merge_dicts() -> None:
    assert merge_dicts(
        *[{"A": 1, "B": 2}, {"A": 2, "B": 3, "C": 4}, {"A": 4, "C": 5, "D": 6}]
    ) == {"A": 4, "B": 3, "C": 5, "D": 6}
    assert merge_dicts(*[{"A": 1, "B": 2}, {}]) == {"A": 1, "B": 2}
    assert merge_dicts(*[]) == {}


def test_append() -> None:  # d: Dict[T, List[U]], key: T, val: U) -> None:
    """Append to values stored under a dictionary key.

    append({},"A",1) sets dict to {"A":[1]}
    append({"A":[1],"A",2) sets dict to {"A":[1,2]}
    """

    def append_result(
        key: str, value: int, d: Dict[str, List[int]] = {}
    ) -> Dict[str, List[int]]:
        append(d, key, value)
        return d

    assert append_result("A", 1) == {"A": [1]}
    assert append_result("A", 1, {"A": [1]}) == {"A": [1, 1]}
    assert append_result("A", 1, {"B": [2]}) == {"A": [1], "B": [2]}


def test_partition() -> None:
    assert partition(["Aa", "Ab", "Ac", "Dc", "Dcc", "E", "Ef"], lambda x: x[0]) == {
        "A": ["Aa", "Ab", "Ac"],
        "D": ["Dc", "Dcc"],
        "E": ["E", "Ef"],
    }


def test_filter_nonempty_values() -> None:
    assert filter_nonempty_values({"A": 1, "B": None}) == {"A": 1}
    assert filter_nonempty_values({"B": None}) == {}
    assert filter_nonempty_values({}) == {}
    assert filter_nonempty_values(None) == {}


class TestMutabilityConversion:
    def test_make_immutable_with_dict(self):
        mutable_dict = {"a": 1, "b": {"c": 2}}
        immutable_obj = make_immutable(mutable_dict)
        assert isinstance(immutable_obj, Map)
        assert immutable_obj == Map({"a": 1, "b": Map({"c": 2})})
        assert hash(immutable_obj) is not None

    def test_make_immutable_with_list(self):
        mutable_list = [1, [2, 3], {"a": 4}]
        immutable_obj = make_immutable(mutable_list)
        assert isinstance(immutable_obj, tuple)
        assert immutable_obj == (1, (2, 3), Map({"a": 4}))
        assert hash(immutable_obj) is not None

    def test_make_immutable_with_other_types(self):
        int_obj = 42
        str_obj = "hello"
        assert make_immutable(int_obj) == 42
        assert make_immutable(str_obj) == "hello"

    def test_make_mutable_with_immutable_map(self):
        immutable_map = Map({"a": 1, "b": Map({"c": 2})})
        mutable_obj = make_mutable(immutable_map)
        assert isinstance(mutable_obj, dict)
        assert mutable_obj == {"a": 1, "b": {"c": 2}}

    def test_make_mutable_with_tuple(self):
        immutable_tuple = (1, (2, 3), Map({"a": 4}))
        mutable_obj = make_mutable(immutable_tuple)
        assert isinstance(mutable_obj, list)
        assert mutable_obj == [1, [2, 3], {"a": 4}]

    def test_make_mutable_with_ordered_set(self):
        ordered_set = OrderedSet([1, 2, 3])
        mutable_obj = make_mutable(ordered_set)
        assert isinstance(mutable_obj, list)
        assert mutable_obj == [1, 2, 3]

    def test_make_mutable_with_other_types(self):
        int_obj = 42
        str_obj = "hello"
        assert make_mutable(int_obj) == 42
        assert make_mutable(str_obj) == "hello"


@pytest.mark.unit
class TestUnflattenDict:
    def test_empty_dict(self):
        assert unflatten_dict({}) == {}

    def test_empty_dict_value(self):
        assert unflatten_dict({"A": {}}) == {"A": {}}

    def test_unflattened_dict(self):
        assert unflatten_dict({"A": "1"}) == {"A": "1"}

    def test_same_level(self):
        assert unflatten_dict({"A.B": "1", "A.C": "2"}) == {"A": {"B": "1", "C": "2"}}

    def test_mixed_levels(self):
        assert unflatten_dict(
            {
                "A": "1",
                "B.C": "2",
                "B.D": "3",
            }
        ) == {
            "A": "1",
            "B": {"C": "2", "D": "3"},
        }

    def test_long_path(self):
        assert unflatten_dict({"A.B.C.D.E.F.G": "1"}) == {
            "A": {"B": {"C": {"D": {"E": {"F": {"G": "1"}}}}}}
        }

    def test_single_item_array(self):
        assert unflatten_dict({"A.0.B": "C"}) == {"A": [{"B": "C"}]}

    def test_multi_item_array(self):
        assert unflatten_dict({"A.0.B": "C", "A.1.D": "E"}) == {
            "A": [{"B": "C"}, {"D": "E"}]
        }

    def test_multi_value_array(self):
        assert unflatten_dict(
            {"A.0.B": "C", "A.0.D": "E", "A.1.F": "G", "A.1.H": "I"}
        ) == {"A": [{"B": "C", "D": "E"}, {"F": "G", "H": "I"}]}

    def test_array_with_scalar_value(self):
        assert unflatten_dict({"A.0": "B"}) == {"A": ["B"]}

    def test_array_with_scalar_values(self):
        assert unflatten_dict({"A.0": "B", "A.1": "C"}) == {"A": ["B", "C"]}

    def test_overwrite_existing_values(self):
        assert unflatten_dict({"A.B": 1, "A.B": 2}) == {"A": {"B": 2}}

    def test_conflicting_types(self):
        with pytest.raises(ValueError):
            unflatten_dict({"A.B": 1, "A": 2, "A.C": 3})

    def test_mixed_types_in_array(self):
        assert unflatten_dict({"A.0": "B", "A.1.C": "D"}) == {"A": ["B", {"C": "D"}]}

    def test_data_not_completely_flattened(self):
        assert unflatten_dict({"A.B.C": 1, "A": {"B.D": 2}}) == {
            "A": {"B": {"C": 1, "D": 2}}
        }

    def test_response_with_object_fields_specified(self):
        assert unflatten_dict(
            {
                "address.email": "2a3aaa22b2ccce15ef7a1e94ee@email.com",
                "address.name": "MASKED",
                "metadata": {"age": "24", "place": "Bedrock"},
                "return_path": "",
                "substitution_data": {
                    "favorite_color": "SparkPost Orange",
                    "job": "Software Engineer",
                },
                "tags": ["greeting", "prehistoric", "fred", "flintstone"],
            }
        ) == {
            "address": {
                "email": "2a3aaa22b2ccce15ef7a1e94ee@email.com",
                "name": "MASKED",
            },
            "metadata": {"age": "24", "place": "Bedrock"},
            "return_path": "",
            "substitution_data": {
                "favorite_color": "SparkPost Orange",
                "job": "Software Engineer",
            },
            "tags": ["greeting", "prehistoric", "fred", "flintstone"],
        }

    def test_none_separator(self):
        with pytest.raises(IndexError):
            unflatten_dict({"": "1"}, separator=None)


@pytest.mark.unit
class TestFlattenDict:
    def test_empty_dict(self):
        assert flatten_dict({}) == {}

    def test_scalar_value(self):
        with pytest.raises(ValueError) as exc:
            flatten_dict(42)
        assert "Input to flatten_dict must be a dict or list" in str(exc)

    def test_unnested_dict(self):
        assert flatten_dict({"A": "1", "B": "2"}) == {"A": "1", "B": "2"}

    def test_nested_dict(self):
        assert flatten_dict({"A": {"B": "1", "C": "2"}}) == {"A.B": "1", "A.C": "2"}

    def test_deep_nesting(self):
        assert flatten_dict({"A": {"B": {"C": {"D": {"E": {"F": {"G": "1"}}}}}}}) == {
            "A.B.C.D.E.F.G": "1"
        }

    def test_list_values(self):
        assert flatten_dict({"A": ["B", "C"]}) == {"A.0": "B", "A.1": "C"}

    def test_list_nested_dict(self):
        assert flatten_dict({"A": [{"B": "C"}, {"D": "E"}]}) == {
            "A.0.B": "C",
            "A.1.D": "E",
        }

    def test_mixed_nested_structures(self):
        data = {"A": {"B": "1", "C": "2"}, "D": [{"E": "3"}, {"E": "4"}]}
        expected = {"A.B": "1", "A.C": "2", "D.0.E": "3", "D.1.E": "4"}
        assert flatten_dict(data) == expected

    def test_empty_nested_structures(self):
        # Empty dictionaries and arrays don't contribute any keys to the flattened result
        assert flatten_dict({"A": {}, "B": []}) == {}

        # Mixed with non-empty values
        assert flatten_dict({"A": {}, "B": [], "C": "value"}) == {"C": "value"}

    def test_none_values(self):
        assert flatten_dict({"A": None, "B": {"C": None}}) == {"A": None, "B.C": None}

    def test_custom_separator(self):
        assert flatten_dict({"A": {"B": "1"}}, separator="_") == {"A_B": "1"}

    def test_with_prefix(self):
        assert flatten_dict({"A": "1"}, prefix="prefix") == {"prefix.A": "1"}

    def test_with_prefix_and_custom_separator(self):
        assert flatten_dict({"A": "1"}, prefix="prefix", separator="_") == {
            "prefix_A": "1"
        }

    def test_complex_example(self):
        data = {
            "address": {
                "email": "test@example.com",
                "name": "Test User",
            },
            "metadata": {"age": "24", "place": "Anywhere"},
            "empty_field": "",
            "tags": ["greeting", "test", "example"],
        }
        expected = {
            "address.email": "test@example.com",
            "address.name": "Test User",
            "metadata.age": "24",
            "metadata.place": "Anywhere",
            "empty_field": "",
            "tags.0": "greeting",
            "tags.1": "test",
            "tags.2": "example",
        }
        assert flatten_dict(data) == expected
