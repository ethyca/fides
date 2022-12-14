import itertools
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Union

from loguru import logger

from fides.api.ops.graph.config import CollectionAddress, FieldPath
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.util.collection_util import Row


def filter_data_categories(
    access_request_results: Dict[str, List[Dict[str, Optional[Any]]]],
    target_categories: Set[str],
    data_category_fields: Dict[CollectionAddress, Dict[FidesOpsKey, List[FieldPath]]],
    rule_key: str = "",
    fides_connector_datasets: Optional[Set[str]] = None,
) -> Dict[str, List[Dict[str, Optional[Any]]]]:
    """Filter access request results to only return fields associated with the target data categories
    and subcategories.

    Regarding subcategories,if data category "user.contact" is specified on one of the rule
    targets, for example, all fields on subcategories also apply, so ["user.contact.address.city",
    "user.contact.address.street", ...], etc.

    :param access_request_results: Dictionary of access request results for each of your collections
    :param target_categories: A set of data categories that we'd like to extract from access_request_results
    :param data_category_fields: Data categories mapped to applicable fields for each collection

    :return: Filtered access request results that only contain fields matching the desired data categories.
    """
    logger.info(
        "Filtering Access Request results to return fields associated with data categories"
    )
    filtered_access_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for node_address, results in access_request_results.items():
        if not results:
            continue

        # Results from fides connectors are a special case:
        # they've already been filtered and stored in a dict keyed by rule key.
        # So here, we simply find the results corresponding to our current rule
        # and unpack the result so that its stored at the "top level"
        # of the results dict
        if fides_connector_datasets and (
            CollectionAddress.from_string(node_address).dataset
            in fides_connector_datasets
        ):
            unpack_fides_connector_results(
                results, filtered_access_results, rule_key, node_address
            )
            # do not do any further processing on fides connector results
            # as they have already been pre-filtered
            continue

        # Gets all FieldPaths on this traversal_node associated with the requested data
        # categories and sub data categories
        target_field_paths: Set[FieldPath] = set(
            itertools.chain(
                *[
                    field_paths
                    for cat, field_paths in data_category_fields[
                        CollectionAddress.from_string(node_address)
                    ].items()
                    if any(cat.startswith(tar) for tar in target_categories)
                ]
            )
        )

        if not target_field_paths:
            continue

        for row in results:
            filtered_results: Dict[str, Any] = {}
            for field_path in target_field_paths:
                select_and_save_field(filtered_results, row, field_path)
            remove_empty_containers(filtered_results)
            filtered_access_results[node_address].append(filtered_results)

    return filtered_access_results


def select_and_save_field(saved: Any, row: Row, target_path: FieldPath) -> Dict:
    """Extract the data located along the given `target_path` from the row and add to the "saved" dictionary.

    Entire rows are returned from your collections; this function will incrementally just pull the PII from the rows,
    by retrieving data along target_paths to relevant data categories.

    To use, pass in an empty dict for "saved" and loop through a list of FieldPaths you want,
    continuing to pass in the ever-growing new "saved" dict that was returned from the previous iteration.

    :param saved: Call with an empty dict to start, it will recursively update as data along the target_path is added.
    :param row: Call with retrieved row to start, it will recursively be called with a variety of object types until we
    reach the most deeply nested value.
    :param target_path: FieldPath to the data we want to retrieve

    :return: modified saved dictionary with given field path if found
    """

    def _defaultdict_or_array(resource: Any) -> Any:
        """Helper for building new nested resource - can return an empty dict, empty array or resource itself"""
        return type(resource)() if isinstance(resource, (list, dict)) else resource

    if isinstance(row, list):
        for i, elem in enumerate(row):
            try:
                saved[i] = select_and_save_field(saved[i], elem, target_path)
            except IndexError:
                saved.append(
                    select_and_save_field(
                        _defaultdict_or_array(elem), elem, target_path
                    )
                )

    elif isinstance(row, dict):
        for key in row:
            if target_path.levels and key == target_path.levels[0]:
                if key not in saved:
                    saved[key] = _defaultdict_or_array(row[key])
                saved[key] = select_and_save_field(
                    saved[key], row[key], FieldPath(*target_path.levels[1:])
                )
    return saved


RecursiveRow = Union[Dict[Any, Any], List[Any]]


def remove_empty_containers(row: RecursiveRow) -> RecursiveRow:
    """
    Recursively updates row in place to remove empty dictionaries and empty arrays at any level in collection or
    from embedded collections in arrays.

    `select_and_save_field` recursively builds a nested structure based on desired field paths.
    If no input data was found along a deeply nested field path, we may have empty dicts to clean up
    before supplying response to user.  Also empty arrays and empty dicts do not contain PII.

    :param row: Pass in retrieved row, and it will recursively go through objects and arrays and filter out empty collections.
    :return: Updated row with empty objects and arrays removed
    """
    if isinstance(row, dict):
        for key, value in row.copy().items():
            if isinstance(value, (dict, list)):
                value = remove_empty_containers(value)

            if value in [{}, []]:
                del row[key]

    elif isinstance(row, list):
        for index, elem in reversed(list(enumerate(row))):
            if isinstance(elem, (dict, list)):
                elem = remove_empty_containers(elem)

            if elem in [{}, []]:
                row.pop(index)

    return row


def unpack_fides_connector_results(
    connector_results: List[Dict[str, Any]],
    filtered_access_results: Dict[str, List[Dict[str, Any]]],
    rule_key: str,
    node_address: str,
) -> None:
    """
    Unpacks the pre-filtered results from a Fides connector
    that are associated with the given `rule_key`.
    These results are stored in the provided aggregate `filtered_acces_results` dict.
    """
    # there should only ever be one element in the list here, since the
    # "real" data is nested one level deeper. but we will iterate through
    # anyway, just to be safe.
    for results in connector_results:
        try:
            rule_results = results[rule_key]
        except KeyError:
            logger.error(
                "Did not find a result entry on Fides connector {} for rule {}",
                node_address,
                rule_key,
            )
            continue

        try:
            filtered_access_results.update(rule_results)
        except ValueError:
            # if we get a ValueError, a given CollectionAddress key
            # already exists in the results dict. Handle that here.
            for key, value in rule_results.items():
                filtered: Optional[
                    List[Dict[str, Optional[Any]]]
                ] = filtered_access_results.get(key)
                if not filtered:
                    filtered_access_results[key] = value  # type: ignore
                else:
                    if value:
                        logger.info("Appending child rows to {}", key)
                        filtered.extend(value)  # type: ignore
