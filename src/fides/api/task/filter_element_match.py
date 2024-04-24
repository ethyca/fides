import copy
from collections import defaultdict
from typing import Any, Dict, List

import pydash
from loguru import logger

from fides.api.task.refine_target_path import (
    DetailedPath,
    FieldPathNodeInput,
    build_refined_target_paths,
    join_detailed_path,
)
from fides.api.util.collection_util import FIDESOPS_DO_NOT_MASK_INDEX, Row
from fides.api.util.logger import Pii


def filter_element_match(
    row: Row,
    query_paths: FieldPathNodeInput,
    delete_elements: bool = True,
) -> Dict[str, Any]:
    """
    Modifies row in place to remove unmatched array elements or unmatched embedded documents within arrays.

    :param row: Record retrieved from a dataset
    :param query_paths: FieldPaths mapped to a list of values you want to match.
    :param delete_elements: If True, *removes* unmatched indices from array. If False, just *replaces* the data,
    so the original indices are preserved.
    :return: A modified record with array elements potentially eliminated if array data was targeted by a query path

    :Example:
    The given row was retrieved from a dataset because an element in row["A"] matched 2 or an element in
    row["C"]["D"] matched 5.  row["A"] is filtered to just contain the matching element, and row["C"] is filtered
    to just contain the objects where "D" = 5. Non-array elements should not be touched.

    filter_element_match(
        row={"A": [1, 2, 3], "B": 2, "C": [{"D": 3, "E": 4}, {"D": 5, "E": 6}, {"D": 5, "E": 7}]},
        query_paths={FieldPath("A"): [2], FieldPath("C, "D"): [5]}
    )

    {"A": [2], "B": 2, "C": [{"D": 5, "E": 6}, {"D": 5, "E": 7}]}

    :Example:
    With delete_elements=False, we replace elements with placeholder text instead.
    filter_element_match(
        row={"A": [1, 2, 3], "B": 2, "C": [{"D": 3, "E": 4}, {"D": 5, "E": 6}, {"D": 5, "E": 7}]},
        query_paths={FieldPath("A"): [2], FieldPath("C, "D"): [5]},
        delete_elements=False
    )

    {
     'A': ['FIDESOPS_DO_NOT_MASK', 2, 'FIDESOPS_DO_NOT_MASK'],
     'B': 2,
     'C': ['FIDESOPS_DO_NOT_MASK', {'D': 5, 'E': 6}, {'D': 5, 'E': 7}]
    }
    """
    detailed_target_paths: List[DetailedPath] = build_refined_target_paths(
        row, query_paths
    )

    array_paths_to_preserve: Dict[str, List[int]] = _expand_array_paths_to_preserve(
        detailed_target_paths
    )

    return _remove_paths_from_row(row, array_paths_to_preserve, delete_elements)


def _remove_paths_from_row(
    row: Dict[str, Any],
    preserve_indices: Dict[str, List[int]],
    delete_elements: bool = True,
) -> Dict[str, Any]:
    """
    Used by filter_element_match, remove array elements from row that are not specified in preserve_indices

    :param row: Record retrieved from a dataset
    :param preserve_indices: A dictionary of dot-separated paths to arrays, where the values are the list of indices
     we want to *keep*
    :param delete_elements: True if we just want to remove the element at the given index, otherwise we replace
     the element with some placeholder text.
    :return: A filtered row that has removed non-specified indices from arrays

    :Example:
    The first element in row["A"]["B"] was the only one specified to preserve, so we remove the other two.
    _remove_paths_from_row({"A": {"B": [{"C": "D"}, {"C": "F"}, {"C": "G"}]}}, {"A.B": [0]})

    {'A': {'B': [{'C': 'D'}]}}
    """
    desc_path_length: Dict[str, List[int]] = (
        dict(  # We want to remove elements from the deepest paths first
            sorted(
                preserve_indices.items(),
                key=lambda item: item[0].count("."),
                reverse=True,
            )
        )
    )
    for path, preserve_index_list in desc_path_length.items():
        matched_array: List = pydash.objects.get(row, path)
        if matched_array is None:
            # This case shouldn't happen - if this gets logged, we've done something wrong
            logger.info(
                "_remove_paths_from_row call: Path {} in row {} not found.",
                path,
                Pii(row),
            )
            continue
        # Loop through array in *reverse* to delete/replace indices
        for index, _ in reversed(list(enumerate(matched_array))):
            if index not in preserve_index_list:  # List of indices that we want to keep
                if delete_elements:  # We delete the element at the given index
                    matched_array.pop(index)
                else:  # We replace the element at the given index
                    matched_array[index] = FIDESOPS_DO_NOT_MASK_INDEX

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
        merge_paths[join_detailed_path(path[0:-1])].append(path[-1])  # type: ignore
    return merge_paths
