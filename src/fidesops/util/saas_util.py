import json
import logging
import re
from collections import defaultdict
from functools import reduce
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from multidimensional_urlencode import urlencode as multidimensional_urlencode

from fidesops.common_exceptions import FidesopsException
from fidesops.graph.config import Collection, CollectionAddress, Dataset, Field

logger = logging.getLogger(__name__)

FIDESOPS_GROUPED_INPUTS = "fidesops_grouped_inputs"


def merge_fields(target: Field, source: Field) -> Field:
    """Replaces source references and identities if they are available from the target"""
    if source.references is not None:
        target.references = source.references
    if source.identity is not None:
        target.identity = source.identity
    return target


def extract_fields(aggregate: Dict, collections: List[Collection]) -> None:
    """
    Takes all of the Fields in the given Collection and places them into an
    dictionary (dict[collection.name][field.name]) merging Fields when necessary
    """
    for collection in collections:
        field_dict = aggregate[collection.name]
        for field in collection.fields:
            if field_dict.get(field.name):
                field_dict[field.name] = merge_fields(field_dict[field.name], field)
            else:
                field_dict[field.name] = field


def get_collection_grouped_inputs(
    collections: List[Collection], name: str
) -> Optional[Set[str]]:
    """Get collection grouped inputs"""
    collection: Collection = next(
        (collect for collect in collections if collect.name == name), {}
    )
    if not collection:
        return set()
    return collection.grouped_inputs


def get_collection_after(
    collections: List[Collection], name: str
) -> Set[CollectionAddress]:
    """If specified, return the collections that need to run before the current collection for saas configs"""
    collection: Collection = next(
        (collect for collect in collections if collect.name == name), {}
    )
    if not collection:
        return set()
    return collection.after


def merge_datasets(dataset: Dataset, config_dataset: Dataset) -> Dataset:
    """
    Merges all Collections and Fields from the config_dataset into the dataset.
    In the event of a collection/field name collision, the target field
    will inherit the identity and field references. This is by design since
    dataset references for SaaS connectors should not have any references.
    """
    field_aggregate: Dict[str, Dict] = defaultdict(dict)
    extract_fields(field_aggregate, dataset.collections)
    extract_fields(field_aggregate, config_dataset.collections)

    collections = []
    for collection_name, field_dict in field_aggregate.items():
        collections.append(
            Collection(
                name=collection_name,
                fields=list(field_dict.values()),
                grouped_inputs=get_collection_grouped_inputs(
                    config_dataset.collections, collection_name
                ),
                after=get_collection_after(config_dataset.collections, collection_name),
            )
        )

    return Dataset(
        name=dataset.name,
        collections=collections,
        connection_key=dataset.connection_key,
    )


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
    for path, value in flat_dict.items():
        if isinstance(value, dict) and len(value) > 0:
            raise FidesopsException(
                "'unflatten_dict' expects a flattened dictionary as input."
            )
        keys = path.split(separator)
        target = reduce(
            lambda current, key: current.setdefault(key, {}),
            keys[:-1],
            output,
        )
        try:
            target[keys[-1]] = value
        except TypeError as exc:
            raise FidesopsException(
                f"Error unflattening dictionary, conflicting levels detected: {exc}"
            )
    return output


def format_body(
    headers: Dict[str, Any],
    body: Optional[str],
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Builds the appropriately formatted body based on the content type,
    adding application/json to the headers if a content type is not provided.
    """

    if body is None:
        return headers, None

    content_type = next(
        (
            value
            for header, value in headers.items()
            if header.lower() == "content-type"
        ),
        None,
    )

    # add Content-Type: application/json if a content type is not provided
    if content_type is None:
        content_type = "application/json"
        headers["Content-Type"] = content_type

    if content_type == "application/json":
        output = body
    elif content_type == "application/x-www-form-urlencoded":
        output = multidimensional_urlencode(json.loads(body))
    elif content_type == "text/plain":
        output = body
    else:
        raise FidesopsException(f"Unsupported Content-Type: {content_type}")

    return headers, output


def assign_placeholders(
    value: Union[str, int], param_values: Dict[str, Any]
) -> Optional[Union[str, int]]:
    """
    Finds all the placeholders (indicated by <>) in the passed in value
    and replaces them with the actual param values

    Returns None if any of the placeholders cannot be found in the param_values
    """
    if value and isinstance(value, str):
        placeholders = re.findall("<([^<>]+)>", value)
        for placeholder in placeholders:
            placeholder_value = param_values.get(placeholder)
            if placeholder_value:
                value = value.replace(f"<{placeholder}>", str(placeholder_value))
            else:
                return None
    return value
