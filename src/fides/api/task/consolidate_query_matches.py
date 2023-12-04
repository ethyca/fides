from typing import Any, List, Optional

from fides.api.graph.config import FieldPath
from fides.api.util.collection_util import Row


def consolidate_query_matches(
    row: Row,
    target_path: FieldPath,
    flattened_matches: Optional[List] = None,
) -> List[Any]:
    """
    Recursively consolidates values along from the target_path into a single array.

    A target_path can point to a single scalar value, an array, or even multiple values within arrays of embedded
    documents. We consolidate all values into a single flattened list, that are used in subsequent queries
    to locate records in another collection.

    :param row: Retrieved record from dataset
    :param target_path: FieldPath to applicable field
    :param flattened_matches: Recursive list where matched value(s) from the target_path are recursively added
    :return: A consolidated flattened list of matched values.
    """
    if flattened_matches is None:
        flattened_matches = []

    if isinstance(row, list):
        for elem in row:
            consolidate_query_matches(elem, target_path, flattened_matches)

    elif isinstance(row, dict):
        for key, value in row.items():
            if target_path.levels and key == target_path.levels[0]:
                consolidate_query_matches(
                    value, FieldPath(*target_path.levels[1:]), flattened_matches
                )

    elif row:
        flattened_matches.append(row)

    return flattened_matches
