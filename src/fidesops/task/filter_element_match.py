import copy
import logging
from collections import defaultdict

from typing import List, Any, Dict

import pydash

from fidesops.graph.config import FieldPath
from fidesops.task.refine_target_path import (
    build_incoming_refined_target_paths,
    DetailedPath,
)

logger = logging.getLogger(__name__)


def filter_element_match(
    row: Dict[str, Any], query_paths: Dict[FieldPath, List[Any]]
) -> Dict[str, Any]:
    """
    Modifies row in place to remove unmatched array elements or unmatched embedded documents within arrays.

    :param row: Record retrieved from a dataset
    :param query_paths: FieldPaths mapped to query values
    :return: A modified record with array elements potentially eliminated if array data was targeted by a query path

    :Example:
    The given row was retrieved from a dataset because an element in row["A"] matched 2 or an element in
    row["C"]["D"] matched 5.  row["A"] is filtered to just contain the matching element, and row["C"] is filtered
    to just contain the objects where "D" = 5. Non-array elements should not be touched.

    filter_element_match(
        row={"A": [1, 2, 3], "B": 2, "C": [{"D": 3, "E": 4}, {"D": 5, "E": 6}, {"D": 5, "E": 7}]},
        query_paths={FieldPath("A"): [2], FieldPath("C, "D"): 5}
    )

    {"A": [2], "B": 2, "C": [{"D": 5, "E": 6}, {"D": 5, "E": 7}]}
    """
    detailed_target_paths: List[DetailedPath] = build_incoming_refined_target_paths(
        row, query_paths
    )

    array_paths_to_preserve: Dict[str, List[int]] = _expand_array_paths_to_preserve(
        detailed_target_paths
    )

    return _remove_paths_from_row(row, array_paths_to_preserve)


def _remove_paths_from_row(
    row: Dict[str, Any], preserve_indices: Dict[str, List[int]]
) -> Dict[str, Any]:
    """
    Used by filter_element_match, remove array elements from row that are not specified in preserve_indices

    :param row: Record retrieved from a dataset
    :param preserve_indices: A dictionary of dot-separated paths to arrays, where the values are the list of indices
    we want to *keep*
    :return: A filtered row that has removed non-specified indices from arrays

    :Example:
    The first element in row["A"]["B"] was the only one specified to preserve, so we remove the other two.
    _remove_paths_from_row({"A": {"B": [{"C": "D"}, {"C": "F"}, {"C": "G"}]}}, {"A.B": [0]})

    {'A': {'B': [{'C': 'D'}]}}
    """
    desc_path_length: Dict[
        str, List[int]
    ] = dict(  # We want to remove elements from the deepest paths first
        sorted(
            preserve_indices.items(),
            key=lambda item: item[0].count("."),
            reverse=True,
        )
    )
    for path, preserve_index_list in desc_path_length.items():
        matched_array: List = pydash.objects.get(row, path)
        if matched_array is None:
            # This case shouldn't happen - if this gets logged, we've done something wrong
            logger.info(
                f"_remove_paths_from_row call: Path {path} in row {row} not found."
            )
            continue
        # Loop through array in reverse to delete indices
        for i, _ in reversed(list(enumerate(matched_array))):
            if i not in preserve_index_list:
                matched_array.pop(i)

    return row


def _expand_array_paths_to_preserve(paths: List[DetailedPath]) -> Dict[str, List[int]]:
    """
    Used by "filter_element_match" - Returns a dictionary of string paths mapped to array indices that we want
    to preserve.

    :param paths: A list of lists of detailed paths (containing strings and array indices) to elements that matched query criteria
    :return: A dict where the keys are a dot-separated path to an array, and the values are a list of indices
    in that array that we want to keep.  If there are no indices in the original path, that path will be ignored.
    Some paths may be expanded into multiple paths where there are multiple levels of indices (arrays of arrays).

    :Example:
    _expand_array_paths_to_preserve([["F", 1, 2], ["F", 1, 3], ["G", "H"], ["L", 1, "M"]])
    {'F': [1], 'F.1': [2, 3], 'L': [1]}

    This data will be used to remove all elements from row["F"][1] that are not at index 2, and 3.
    We'll then remove all elements from "F" that are not at index [1], and all elements from "L" that are not at index 1.

    """
    # Break path into multiple paths if array elements in path
    expanded: List[DetailedPath] = []
    for path in paths:
        while path != [] and not isinstance(path[-1], int):
            path.pop()
        new_path: DetailedPath = []
        for elem in path:
            new_path.append(elem)
            if isinstance(elem, int) and new_path not in expanded:
                expanded.append(copy.deepcopy(new_path))

    # Combine paths where the key is a dot-separated path to the array, and the value are the indices
    # of the array we want to preserve
    merge_paths: Dict[str, List[int]] = defaultdict(list)
    for path in expanded:
        merge_paths[".".join(map(str, path[0:-1]))].append(path[-1])  # type: ignore
    return merge_paths
