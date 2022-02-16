import logging
from typing import Dict, Any, List, Union

from fidesops.graph.config import FieldPath

Level = Union[str, int]
DetailedPath = List[
    Level
]  # A more detailed path to a field, potentially containing indices

logger = logging.getLogger(__name__)


def build_incoming_refined_target_paths(
    row: Dict[str, Any], query_paths: Dict[FieldPath, List[Any]]
) -> List[DetailedPath]:
    """
    Return a list of more detailed path(s) to the matched data that caused that row to be returned. Runs
    recursive `refine_target_path` for each FieldPath in query_paths. If there are no array paths, the paths
    will not change.

    :param row: Record retrieved from a dataset
    :param query_paths: FieldPaths mapped to query values
    :return: A list of lists containing more detailed paths to the matched data

    :Example:
    row = {
        "A": [1, 2],
        "B": 2,
        "C": [{"D": 3, "E": 5}, {"D": 3, "E": 4}, {"D": 3, "E": 4}],
        "G": 3,
    }
    incoming_paths= {FieldPath("A"): [2], FieldPath("C", "E"): [4], FieldPath("G"): [3]}

    build_incoming_refined_target_paths(row, incoming_paths)
    [["G"], ["A", 1], ["C", 1, "E"], ["C", 2, "E"]]
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
    row: Dict[str, Any], target_path: List[str], only: List[Any]
) -> DetailedPath:  # Can also return a list of DetailedPaths if there are multiple matches.
    """
    Recursively modify the target_path to be more detailed path(s) to the referenced data. Instead of just strings,
    the path will be expanded to include indices where applicable.

    :param row: Record retrieved from a dataset
    :param target_path: A list of strings representing the path to the desired field.
    :param only: A list of values that were used to build the query.
    :return: A list or a list of lists containing more detailed path(s) to the data in "only".  If there
    was just one path, we return one list.

    :Example:
    In this example, path ["A", "B", "C"] points to two elements that match values "F" or "G".  We update
    the path to insert the indices to locate the appropriate value.

    refine_target_path({"A": {"B": [{"C": "D"}, {"C": "F"}, {"C": "G"}]}}, ["A", "B", "C"], only=["F", "G"])

    [["A", "B", 1, "C"], ["A", "B", 2, "C"]]
    """
    try:
        current_level = target_path[0]
        current_elem = row[current_level]
    except KeyError:  # FieldPath not found in record, this is expected to happen when data doesn't exist in collection
        return []
    except (IndexError, TypeError):  # No field path or invalid field path
        logger.warning(f"Error with locating {target_path} on row")
        return []

    if isinstance(current_elem, dict):
        next_levels = refine_target_path(current_elem, target_path[1:], only)
        return _update_path(current_level, next_levels)

    if isinstance(current_elem, list):
        next_levels = _enter_array(current_elem, target_path[1:], only)
        return _update_path(current_level, next_levels)

    # Simple case - value is a scalar
    return [current_level] if _match_found(current_elem, only) else []


def _enter_array(array: List[Any], field_path: List[str], only: List[Any]) -> List:
    """
    Used by recursive "refine_target_path" whenever arrays are encountered in the row.
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


def _match_found(elem: Any, only: List[Any]) -> bool:
    """The given scalar element matches one of the input values"""
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
