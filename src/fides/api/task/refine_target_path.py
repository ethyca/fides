from typing import Any, Dict, List, Optional, Union

from loguru import logger

from fides.api.graph.config import FieldPath
from fides.api.util.collection_util import FIDESOPS_DO_NOT_MASK_INDEX, Row

Level = Union[
    str, int
]  # A specific level along the path to a resource. Can be a dictionary key or an array index.
DetailedPath = List[Level]  # A more detailed field path, potentially containing indices
FieldPathNodeInput = Dict[FieldPath, Optional[List[Any]]]


def join_detailed_path(detailed_path: DetailedPath) -> str:
    """Helper method to turn a detailed path of strings and arrays ["A", 0, "B", 1] into "A.0.B.1" """
    return ".".join(map(str, detailed_path))


def build_refined_target_paths(
    row: Row, query_paths: FieldPathNodeInput
) -> List[DetailedPath]:
    """
    Return a list of more detailed path(s) to the data in "row". Runs recursive `refine_target_path` for
    each FieldPath in query_paths. If the given path does not target data in an array, the path should not change.

    :param row: Record retrieved from a dataset
    :param query_paths: FieldPaths mapped to a list of values you want to match along that field path. If you want to
      match all values, map FieldPath to None.
    :return: A list of lists containing more detailed paths to the matched data.

    :Example:
    The field path to the scalar resource did not change, but the field paths to elements in arrays were expanded
    to target the specific indices.
    row = {
        "A": [1, 2],
        "B": 2,
        "C": [{"D": 3, "E": 5}, {"D": 3, "E": 4}, {"D": 3, "E": 4}],
        "G": 3,
    }

    incoming_paths= {FieldPath("A"): [2], FieldPath("C", "E"): [4], FieldPath("G"): [3]}
    build_refined_target_paths(row, incoming_paths)
    [['G'], ['A', 1], ['C', 1, 'E'], ['C', 2, 'E']]

    ------------------------------------------------------------------------------------------------------------------
    :Example:
    We want to build detailed paths to every possible element, so our query paths map FieldPath to None.

    incoming_paths= {FieldPath("A"): None, FieldPath("C", "E"): None, FieldPath("G"): None}
    build_refined_target_paths(row, incoming_paths)

    [['G'], ['A', 0], ['A', 1], ['C', 0, 'E'], ['C', 1, 'E'], ['C', 2, 'E']]
    """
    found_paths: List[DetailedPath] = []
    for target_path, only in query_paths.items():
        path = refine_target_path(row, list(target_path.levels), only)
        if path:
            if isinstance(path[0], list):
                found_paths.extend(path)
            else:
                found_paths.append(path)
    found_paths.sort(key=len)
    return found_paths


def refine_target_path(
    row: Row, target_path: List[str], only: Optional[List[Any]] = None
) -> (
    DetailedPath
):  # Can also return a list of DetailedPaths if there are multiple matches.
    """
    Recursively modify the target_path to be more detailed path(s) to the referenced data. Instead of just strings,
    the path will expand to include indices where applicable.

    :param row: Record retrieved from a dataset
    :param target_path: A list of strings representing the path to the desired field.
    :param only: A list of values that you want to match. If you want to match all possible values, you can omit "only".
    :return: A list or a list of lists containing more detailed path(s) to the data in "only". If data isn't limited in
     "only", we expand the target_path to all possible target_paths.  If there was just one path, we return one list.

    :Example:
    In this example, we want to expand path ["A", "B", "C"] to paths that match values "F" or "G".  We update
    the path to insert the indices to target the specific element.

    refine_target_path({"A": {"B": [{"C": "D"}, {"C": "F"}, {"C": "G"}]}}, ["A", "B", "C"], only=["F", "G"])

    [["A", "B", 1, "C"], ["A", "B", 2, "C"]]

    ------------------------------------------------------------------------------------------------------------------
    :Example:
    Here, we instead want to expand the paths to all possible paths, so we don't specify "only".
    refine_target_path({"A": {"B": [{"C": "D"}, {"C": "F"}, {"C": "G"}]}}, ["A", "B", "C"])

    [['A', 'B', 0, 'C'], ['A', 'B', 1, 'C'], ['A', 'B', 2, 'C']]
    """
    try:
        current_level = target_path[0]
        current_elem = row[current_level]
    except (
        KeyError
    ):  # FieldPath not found in record, this is expected to happen when data doesn't exist in collection
        return []
    except (
        IndexError,
        TypeError,
    ):  # No/invalid field path. Expected when the path has been eliminated.
        logger.warning("Could not locate target path {} on row", target_path)
        return []

    if isinstance(current_elem, list):
        next_levels = _enter_array(current_elem, target_path[1:], only)
        return _update_path(current_level, next_levels)

    if len(target_path[1:]):
        next_levels = refine_target_path(current_elem, target_path[1:], only)
        return _update_path(current_level, next_levels)

    # Simple case - value is a scalar
    return [current_level] if _match_found(current_elem, only) else []


def _enter_array(
    array: List[Any], field_path: List[str], only: Optional[List[Any]]
) -> List:
    """
    Used by recursive "refine_target_path" whenever arrays are encountered in the row.  The existence of array
    data is what makes a single field_path potentially apply to multiple values.
    """
    results: List[Any] = []
    for index, elem in enumerate(array):
        current_result = []

        if field_path:
            next_result = refine_target_path(elem, field_path, only)
            current_result = _update_path(index, next_result)
        else:
            if isinstance(elem, list):
                next_result = _enter_array(
                    elem, field_path, only
                )  # Nested enter_array calls needed for lists in lists
                current_result = _update_path(index, next_result)
            else:
                if _match_found(elem, only):
                    current_result = [index]

        if current_result:  # Match found at lower level
            if isinstance(current_result[0], list):
                # Keeps nested lists at most list of lists
                results.extend(current_result)
            else:
                results.append(current_result)

    return results[0] if len(results) == 1 else results


def _match_found(elem: Any, only: Optional[List[Any]] = None) -> bool:
    """Returns True if the given element is considered a match."""
    if elem == FIDESOPS_DO_NOT_MASK_INDEX:
        # This element has already been marked in post-processing as one that shouldn't be considered a match
        return False

    if not only:
        # If no values are specified to match, we return all possible paths
        return True

    # Otherwise, does this element match a value in only?
    return elem in only


def _update_path(current_level: Level, deeper_levels: DetailedPath) -> DetailedPath:
    """
    Used by "refine_target_path" and "_enter_array" to recursively build a
    more refined target path to the desired data.
    """
    if not deeper_levels:
        # Element did not contain a match
        return []

    if isinstance(deeper_levels[0], list):
        result = []
        for item in deeper_levels:
            # Builds multiple possible paths
            result.append(_update_path(current_level, item))
        return result

    # Consolidates current level with deeper levels
    result = [current_level]
    result.extend(deeper_levels)
    return result
