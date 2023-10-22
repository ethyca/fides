from __future__ import annotations

import json
import re
import socket
from collections import defaultdict, deque
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pydash
import yaml
from multidimensional_urlencode import urlencode as multidimensional_urlencode

from fides.api.common_exceptions import FidesopsException, ValidationError
from fides.api.cryptography.cryptographic_util import bytes_to_b64_str
from fides.api.graph.config import Collection, CollectionAddress, Field, GraphDataset
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.config import CONFIG
from fides.config.helpers import load_file

FIDESOPS_GROUPED_INPUTS = "fidesops_grouped_inputs"
PRIVACY_REQUEST_ID = "privacy_request_id"
MASKED_OBJECT_FIELDS = "masked_object_fields"
ALL_OBJECT_FIELDS = "all_object_fields"
CUSTOM_PRIVACY_REQUEST_FIELDS = "custom_privacy_request_fields"


def deny_unsafe_hosts(host: str) -> str:
    """
    Verify that the provided host isn't a potentially unsafe one.

    WARNING: IPv6 is _not_ supported and will throw an exception!
    """
    if CONFIG.dev_mode:
        return host

    try:
        host_ip: Union[IPv4Address, IPv6Address] = ip_address(
            socket.gethostbyname(host)
        )
    except socket.gaierror:
        raise ValueError(f"Failed to resolve hostname: {host}")

    if host_ip.is_link_local or host_ip.is_loopback:
        raise ValueError(f"Host '{host}' with IP Address '{host_ip}' is not safe!")
    return host


def load_yaml_as_string(filename: str) -> str:
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        return file.read()


def load_config(filename: str) -> Dict:
    """Loads the SaaS config from provided filename"""
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file).get("saas_config", [])


def load_config_from_string(string: str) -> Dict:
    """Loads the SaaS config dict from the yaml string"""
    try:
        return yaml.safe_load(string)["saas_config"]
    except:
        raise ValidationError(
            "Config contents do not contain a 'saas_config' key at the root level. For example, check formatting, specifically indentation."
        )


def load_as_string(filename: str) -> str:
    file_path = load_file([filename])
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def replace_config_placeholders(
    config: str, string_to_replace: str, replacement: str
) -> Dict:
    """Loads the SaaS config from the yaml string and replaces any string with the given value"""
    yaml_str: str = config.replace(string_to_replace, replacement)
    return load_config_from_string(yaml_str)


def load_config_with_replacement(
    filename: str, string_to_replace: str, replacement: str
) -> Dict:
    """Loads the saas config from the yaml file and replaces any string with the given value"""
    yaml_str: str = load_yaml_as_string(filename).replace(
        string_to_replace, replacement
    )
    return load_config_from_string(yaml_str)


def load_datasets(filename: str) -> Dict:
    """Loads the datasets in the provided filename"""
    yaml_file = load_file([filename])
    with open(yaml_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file).get("dataset", [])


def load_dataset_from_string(string: str) -> Dict:
    """Loads the dataset dict from the yaml string"""
    try:
        return yaml.safe_load(string)["dataset"][0]
    except:
        raise ValidationError(
            "Dataset contents do not contain a 'dataset' key at the root level. For example, check formatting, specifically indentation."
        )


def replace_dataset_placeholders(
    dataset: str, string_to_replace: str, replacement: str
) -> Dict:
    """Loads the dataset from the yaml string and replaces any string with the given value"""
    yaml_str: str = dataset.replace(string_to_replace, replacement)
    return load_dataset_from_string(yaml_str)


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


def get_collection_skip_processing(collections: List[Collection], name: str) -> bool:
    """If specified, return skip_processing value"""
    collection: Collection | None = next(
        (collect for collect in collections if collect.name == name), None
    )
    return bool(collection.skip_processing) if collection else False


def get_collection_after(
    collections: List[Collection], name: str
) -> Set[CollectionAddress]:
    """If specified, return the collections that need to be read before the current collection for saas configs"""
    collection: Collection | None = next(
        (collect for collect in collections if collect.name == name), None
    )
    if not collection:
        return set()
    return collection.after


def get_collection_erase_after(
    collections: List[Collection], name: str
) -> Set[CollectionAddress]:
    """If specified, return the collections that need to be erased before the current collection for saas configs"""
    collection: Collection | None = next(
        (collect for collect in collections if collect.name == name), None
    )
    if not collection:
        return set()
    return collection.erase_after


def merge_datasets(dataset: GraphDataset, config_dataset: GraphDataset) -> GraphDataset:
    """
    Merges all Collections and Fields from the "config_dataset" into the "dataset".
    In the event of a collection/field name collision, the target field
    will inherit the identity and field references. This is by design since
    dataset references for SaaS connectors should not have any references.
    """
    field_aggregate: Dict[str, Dict] = defaultdict(dict)
    extract_fields(field_aggregate, dataset.collections)
    extract_fields(field_aggregate, config_dataset.collections)

    collections = []
    for collection_name, field_dict in field_aggregate.items():
        skip_processing: bool = get_collection_skip_processing(
            config_dataset.collections, collection_name
        )
        if skip_processing:
            continue

        collections.append(
            Collection(
                name=collection_name,
                fields=list(field_dict.values()),
                grouped_inputs=get_collection_grouped_inputs(
                    config_dataset.collections, collection_name
                ),
                after=get_collection_after(config_dataset.collections, collection_name),
                erase_after=get_collection_erase_after(
                    config_dataset.collections, collection_name
                ),
            )
        )

    return GraphDataset(
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
    queue = deque(flat_dict.items())

    while queue:
        path, value = queue.popleft()
        keys = path.split(separator)
        target = output
        for i, current_key in enumerate(keys[:-1]):
            next_key = keys[i + 1]
            if next_key.isdigit():
                target = target.setdefault(current_key, [])
            else:
                if isinstance(target, dict):
                    target = target.setdefault(current_key, {})
                elif isinstance(target, list):
                    while len(target) <= int(current_key):
                        target.append({})
                    target = target[int(current_key)]
        try:
            if isinstance(target, list):
                target.append(value)
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
        for full_placeholder in placeholders:
            is_optional = full_placeholder.endswith("?")
            placeholder_key = full_placeholder[:-1] if is_optional else full_placeholder

            placeholder_value = pydash.get(param_values, placeholder_key)

            # removes outer {} wrapper from body for greater flexibility in custom body config
            if isinstance(placeholder_value, dict):
                placeholder_value = json.dumps(placeholder_value)[1:-1]

            if placeholder_value is not None:
                value = value.replace(f"<{full_placeholder}>", str(placeholder_value))
            elif is_optional:
                value = value.replace(f'"<{full_placeholder}>"', "null")
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


def get_identity(privacy_request: Optional[PrivacyRequest]) -> Optional[str]:
    """
    Returns a single identity or raises an exception if more than one identity is defined
    """

    if not privacy_request:
        return None

    identities: List[str] = []
    identity_data: Dict[str, Any] = privacy_request.get_cached_identity_data()
    # filters out keys where associated value is None or empty str
    identities = list({k for k, v in identity_data.items() if v})
    if len(identities) > 1:
        raise FidesopsException(
            "Only one identity can be specified for SaaS connector traversal"
        )
    return identities[0] if identities else None


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


def replace_version(saas_config: str, new_version: str) -> str:
    """
    Replace the version number in the given saas_config string with the provided new_version.
    """
    version_pattern = r"version:\s*[\d\.]+"
    updated_config = re.sub(
        version_pattern, f"version: {new_version}", saas_config, count=1
    )
    return updated_config
