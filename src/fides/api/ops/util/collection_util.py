from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")

NodeInput = Dict[str, List[Any]]  # Of format {node_address: []}
Row = Dict[str, Any]
FIDESOPS_DO_NOT_MASK_INDEX = "FIDESOPS_DO_NOT_MASK"


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
