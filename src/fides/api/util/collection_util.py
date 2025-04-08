from collections import deque
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


# pylint: disable=too-many-branches
def unflatten_dict(flat_dict: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Converts a dictionary of paths/values into a nested dictionary

    example:

    {"A.B": "1", "A.C": "2"}

    becomes

    {
        "A": {
            "B": "1",
            "C": "2"
        }
    }
    """
    output: Dict[Any, Any] = {}
    queue = deque(flat_dict.items())

    while queue:
        path, value = queue.popleft()
        keys = path.split(separator)
        target = output
        for i, current_key in enumerate(keys[:-1]):
            next_key = keys[i + 1]
            if next_key.isdigit():
                if isinstance(target, dict):  # Only call setdefault on dictionaries
                    target = target.setdefault(current_key, [])
                elif isinstance(
                    target, list
                ):  # If target is a list, handle differently
                    idx = int(current_key)
                    while len(target) <= idx:
                        target.append([])  # Add a list since next_key is a digit
                    target = target[idx]
            else:
                if isinstance(target, dict):
                    target = target.setdefault(current_key, {})
                elif isinstance(target, list):
                    idx = int(current_key)
                    while len(target) <= idx:
                        target.append({})
                    target = target[idx]
        try:
            if isinstance(target, list):
                idx = int(keys[-1]) if keys[-1].isdigit() else len(target)
                while len(target) <= idx:
                    target.append(None)
                target[idx] = value
            else:
                # If the value is a dictionary, add its components to the queue for processing
                if isinstance(value, dict):
                    target = target.setdefault(keys[-1], {})
                    for inner_key, inner_value in value.items():
                        new_key = f"{path}{separator}{inner_key}"
                        queue.append((new_key, inner_value))
                else:
                    target[keys[-1]] = value
        except TypeError as exc:
            raise ValueError(
                f"Error unflattening dictionary, conflicting levels detected: {exc}"
            )
    return output


# pylint: disable=too-many-branches
def flatten_dict(data: Any, prefix: str = "", separator: str = ".") -> Dict[str, Any]:
    """
    Recursively flatten a dictionary or list into a flat dictionary with dot-notation keys.
    Handles nested dictionaries and arrays with proper indices.
    Preserves empty lists and dictionaries.

    example:

    {
        "A": {
            "B": "1",
            "C": "2"
        },
        "D": [
            {"E": "3"},
            {"E": "4"}
        ],
        "E": [],
        "F": {}
    }

    becomes

    {
        "A.B": "1",
        "A.C": "2",
        "D.0.E": "3",
        "D.1.E": "4",
        "E": [],
        "F": {}
    }

    Args:
        data: The data to flatten (dict, list, or scalar value)
        prefix: The current key prefix (used in recursion)
        separator: The separator to use between key segments (default: ".")

    Returns:
        A flattened dictionary with dot-notation keys
    """
    items: Dict[str, Any] = {}

    if isinstance(data, dict):
        # Handle top-level empty dictionary case
        if not data and not prefix:
            return {}

        # If the dictionary is empty but has a prefix, store it as is
        if not data:
            items[prefix] = {}
            return items

        for k, v in data.items():
            new_key = f"{prefix}{separator}{k}" if prefix else k
            if isinstance(v, (dict, list)):
                if not v:  # Handle empty dict or list
                    items[new_key] = v
                else:
                    items.update(flatten_dict(v, new_key, separator))
            else:
                items[new_key] = v
    elif isinstance(data, list):
        # If the list is empty, store it as is
        if not data:
            items[prefix] = []
            return items

        for i, v in enumerate(data):
            new_key = f"{prefix}{separator}{i}"
            if isinstance(v, (dict, list)):
                if not v:  # Handle empty dict or list
                    items[new_key] = v
                else:
                    items.update(flatten_dict(v, new_key, separator))
            else:
                items[new_key] = v
    else:
        raise ValueError(
            f"Input to flatten_dict must be a dict or list, got {type(data).__name__}"
        )

    return items


def replace_none_arrays(
    data: Any,
) -> Any:
    """
    Recursively replace any arrays containing only None values with empty arrays.

    Args:
        data: Any Python object (dict, list, etc.)

    Returns:
        The transformed data structure with None-only arrays replaced by empty arrays
    """
    if isinstance(data, dict):
        # Process each key-value pair in dictionaries
        return {k: replace_none_arrays(v) for k, v in data.items()}

    if isinstance(data, list):
        # Check if list contains only None values
        if all(item is None for item in data):
            return []

        # Otherwise process each item in the list
        return [replace_none_arrays(item) for item in data]

    # Return other data types unchanged
    return data
