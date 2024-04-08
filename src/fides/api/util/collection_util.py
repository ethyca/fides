from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Optional, TypeVar, Union

import immutables
from ordered_set import OrderedSet

T = TypeVar("T")
U = TypeVar("U")

NodeInput = Dict[str, List[Any]]  # Of format {node_address: []}
Row = Dict[str, Any]
FIDESOPS_DO_NOT_MASK_INDEX = "FIDESOPS_DO_NOT_MASK"


def make_immutable(obj: Any) -> Any:
    """
    Recursively converts a mutable object into an immutable version.
    Dictionaries are converted to immutable `Map`s from the `immutables` library,
    lists are converted to tuples, and other objects are returned unchanged.
    """
    if isinstance(obj, dict):
        return immutables.Map(
            {key: make_immutable(value) for key, value in obj.items()}
        )
    if isinstance(obj, list):
        return tuple(make_immutable(item) for item in obj)
    return obj


def make_mutable(obj: Any) -> Any:
    """
    Recursively converts an immutable object into a mutable version.
    `Map`s from the `immutables` library and dictionaries are converted to mutable dictionaries,
    tuples and `OrderedSet`s are converted to lists, and other objects are returned unchanged.
    """
    if isinstance(obj, (dict, immutables.Map)):
        return {key: make_mutable(value) for key, value in obj.items()}
    if isinstance(obj, (tuple, OrderedSet)):
        return [make_mutable(item) for item in obj]
    return obj


def merge_dicts(*dicts: Dict[T, U]) -> Dict[T, U]:
    """Merge any number of dictionaries.

    Right-hand values take precedence. That is,
    merge_dicts({"A": 1, "B": 2}, {"A": 2, "C": 4})
    =>  {'A': 2, 'B': 2, 'C': 4}
    """
    if dicts:
        return reduce(lambda x, y: {**x, **y}, dicts) or {}
    return {}


def append(d: Dict[T, List[U]], key: T, value: U) -> None:
    """Append to values stored under a dictionary key.

    append({},"A",1) sets dict to {"A":[1]}
    append({"A":[1],"A",2) sets dict to {"A":[1,2]}
    append({"A":[1],"A",[2, 3, 4]) sets dict to {"A":[1, 2, 3, 4]}
    """
    if value:
        if key in d:
            if isinstance(value, list):
                d[key].extend(value)
            else:
                d[key].append(value)
        else:
            d[key] = value if isinstance(value, list) else [value]


def append_unique(d: Dict[T, OrderedSet[U]], key: T, value: Union[U, List[U]]) -> None:
    """Append to values stored under a dictionary key.

    append_unique({}, "A", 1) sets dict to {"A": {1}}
    append_unique({"A": {1}}, "A", 2) sets dict to {"A": {1, 2}}
    append_unique({"A": {1}}, "A", [2, 3, 4]) sets dict to {"A": {1, 2, 3, 4}}
    append_unique({"A": {1, 2}}, "A", [2, 3, 4]) sets dict to {"A": {1, 2, 3, 4}}
    """
    if value:
        if key not in d:
            d[key] = OrderedSet()

        if isinstance(value, list):
            d[key].update(make_immutable(value))
        else:
            d[key].add(make_immutable(value))


def partition(_iterable: Iterable[T], extractor: Callable[[T], U]) -> Dict[U, List[T]]:
    """partition a collection by the output of an arbitrary extractor function"""
    out: Dict[U, List[T]] = {}
    for t in _iterable:
        append(out, extractor(t), t)
    return out


def filter_nonempty_values(d: Optional[Dict[Any, Any]]) -> Dict[Any, Any]:
    """Return the input map with empty values removed. On an input of None
    will return an empty Dict."""
    if d:
        return {e[0]: e[1] for e in d.items() if e[1]}
    return {}


def extract_key_for_address(
    full_request_id: str, number_of_leading_strings_to_exclude: int
) -> str:
    """
    Handles extracting the correct Dataset:Collection to map to extracted
    values.

    Due to differences in the number of leading strings based on access or
    erasure, a parameter is used to ensure the correct values are returned.

    Handles an edge case where double underscores exist in either the fides_key
    of the Dataset or the Collection name.
    """
    request_id_dataset, collection = full_request_id.split(":")
    dataset = request_id_dataset.split("__", number_of_leading_strings_to_exclude)[-1]
    return f"{dataset}:{collection}"
