from typing import Dict, List

from immutables import Map
from ordered_set import OrderedSet

from fides.api.util.collection_util import (
    append,
    filter_nonempty_values,
    make_immutable,
    make_mutable,
    merge_dicts,
    partition,
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
