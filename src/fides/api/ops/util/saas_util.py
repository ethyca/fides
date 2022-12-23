from __future__ import annotations

import json
import re
from collections import defaultdict
from functools import reduce
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from multidimensional_urlencode import urlencode as multidimensional_urlencode

from fides.api.ops.common_exceptions import FidesopsException
from fides.api.ops.graph.config import Collection, CollectionAddress, Dataset, Field
from fides.api.ops.schemas.saas.saas_config import SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import SaaSRequestParams
from fides.core.config.helpers import load_file
from fides.lib.cryptography.cryptographic_util import bytes_to_b64_str

FIDESOPS_GROUPED_INPUTS = "fidesops_grouped_inputs"
PRIVACY_REQUEST_ID = "privacy_request_id"
MASKED_OBJECT_FIELDS = "masked_object_fields"
ALL_OBJECT_FIELDS = "all_object_fields"


def load_yaml_as_string(filename: str) -> str:
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        return file.read()


def load_config(filename: str) -> Dict:
    """Loads the saas config from the yaml file"""
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file).get("saas_config", [])


def load_config_with_replacement(
    filename: str, string_to_replace: str, replacement: str
) -> Dict:
    """Loads the saas config from the yaml file and replaces any string with the given value"""
    yaml_str: str = load_yaml_as_string(filename).replace(
        string_to_replace, replacement
    )
    return yaml.safe_load(yaml_str).get("saas_config", [])


def load_dataset(filename: str) -> Dict:
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file).get("dataset", [])


def load_dataset_with_replacement(
    filename: str, string_to_replace: str, replacement: str
) -> Dict:
    """Loads the dataset from the yaml file and replaces any string with the given value"""
    yaml_str: str = load_yaml_as_string(filename).replace(
        string_to_replace, replacement
    )
    return yaml.safe_load(yaml_str).get("dataset", [])


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
    collection: Collection | None = next(
        (collect for collect in collections if collect.name == name), None
    )
    if not collection:
        return set()
    return collection.grouped_inputs


def get_collection_after(
    collections: List[Collection], name: str
) -> Set[CollectionAddress]:
    """If specified, return the collections that need to run before the current collection for saas configs"""
    collection: Collection | None = next(
        (collect for collect in collections if collect.name == name), None
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


def assign_placeholders(value: Any, param_values: Dict[str, Any]) -> Optional[Any]:
    """
    Finds all the placeholders (indicated by <>) in the passed in value
    and replaces them with the actual param values

    Returns None if any of the placeholders cannot be found in the param_values
    """
    if value and isinstance(value, str):
        placeholders = re.findall("<([^<>]+)>", value)
        for placeholder in placeholders:
            placeholder_value = param_values.get(placeholder)
            if placeholder_value is not None:
                value = value.replace(f"<{placeholder}>", str(placeholder_value))
            else:
                return None
    return value


def map_param_values(
    action: str,
    context: str,
    current_request: SaaSRequest,
    param_values: Dict[str, Any],
) -> SaaSRequestParams:
    """
    Visits path, headers, query, and body params in the current request and replaces
    the placeholders with the request param values.

    The action and context parameters provide more information for the logs

    For example:
        - action: 'read', context: 'transactions collection'
        - action: 'refresh', context: 'Outreach Connector OAuth2'
    """

    path = assign_placeholders(current_request.path, param_values)
    if path is None:
        raise ValueError(
            f"At least one param_value references an invalid field for the '{action}' request of {context}."
        )

    headers: Dict[str, Any] = {}
    for header in current_request.headers or []:
        header_value = assign_placeholders(header.value, param_values)
        # only create header if placeholders were replaced with actual values
        if header_value is not None:
            headers[header.name] = assign_placeholders(header.value, param_values)

    query_params: Dict[str, Any] = {}
    for query_param in current_request.query_params or []:
        query_param_value = assign_placeholders(query_param.value, param_values)
        # only create query param if placeholders were replaced with actual values
        if query_param_value is not None:
            query_params[query_param.name] = query_param_value

    body = assign_placeholders(current_request.body, param_values)
    # if we declared a body and it's None after assigning placeholders we should error the request
    if current_request.body and body is None:
        raise ValueError(
            f"Unable to replace placeholders in body for the '{action}' request of {context}"
        )

    # format the body based on the content type
    updated_headers, formatted_body = format_body(headers, body)

    return SaaSRequestParams(
        method=current_request.method,
        path=path,
        headers=updated_headers,
        query_params=query_params,
        body=formatted_body,
    )


def encode_file_contents(file_path: str) -> str:
    """
    Read file binary and b64 encode it.
    """
    file_path = load_file([file_path])
    with open(file_path, "rb") as file:
        return bytes_to_b64_str(file.read())


def to_pascal_case(s: str) -> str:
    s = s.title()
    s = s.replace("_", "")
    return s
