"""A wrapper to make calling the API consistent across fides."""

from typing import Dict, List, Optional, Union

import requests

# Not using the constant value from fides.api.util.endpoint_utils to reduce the startup time for the CLI
API_PREFIX = "/api/v1"


def generate_resource_url(
    url: str,
    resource_type: str = "",
    resource_id: str = "",
    query_params: Optional[Union[Dict[str, str], Dict[str, List[str]]]] = None,
) -> str:
    """
    Generate a resource's URL using a base url, the resource type,
    and [optionally] the resource's ID.
    """
    base_url = f"{url}{API_PREFIX}/{resource_type}/{resource_id}"

    if not query_params:
        return base_url

    processed_query_params = []
    for key, value in query_params.items():
        if isinstance(value, list):
            processed_query_params.extend([f"{key}={v}" for v in value])
        else:
            processed_query_params.append(f"{key}={value}")

    query_string = "&".join(processed_query_params)
    return f"{url}{API_PREFIX}/{resource_type}/{resource_id}?{query_string}"


def get(
    url: str, resource_type: str, resource_id: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Get a resource by its id.
    """
    resource_url = generate_resource_url(url, resource_type, resource_id)
    return requests.get(resource_url, headers=headers)


def create(
    url: str, resource_type: str, json_resource: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Create a new resource.
    """
    resource_url = generate_resource_url(url, resource_type)
    return requests.post(resource_url, headers=headers, data=json_resource)


def ping(url: str) -> requests.Response:
    """
    Pings the Server on the base url to make sure it's available.
    """
    return requests.get(url)


def delete(
    url: str, resource_type: str, resource_id: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Delete a resource by its id.
    """
    resource_url = generate_resource_url(url, resource_type, resource_id)
    return requests.delete(resource_url, headers=headers)


def ls(  # pylint: disable=invalid-name
    url: str,
    resource_type: str,
    headers: Dict[str, str],
    query_params: Optional[Dict[str, str]] = None,
) -> requests.Response:
    """
    Get a list of all of the resources of a certain type.
    """
    resource_url = generate_resource_url(url, resource_type, query_params=query_params)
    return requests.get(resource_url, headers=headers)


def update(
    url: str,
    resource_type: str,
    json_resource: Dict,
    headers: Dict[str, str],
) -> requests.Response:
    """
    Update an existing resource.
    """
    resource_url = generate_resource_url(url, resource_type)
    return requests.put(resource_url, headers=headers, data=json_resource)


def upsert(
    url: str,
    resource_type: str,
    resources: List[Dict],
    headers: Dict[str, str],
) -> requests.Response:
    """
    For each resource, insert the resource if it doesn't exist, update the resource otherwise.
    """

    resource_url = generate_resource_url(url, resource_type) + "upsert"
    return requests.post(resource_url, headers=headers, json=resources)


def dry_evaluate(
    url: str, resource_type: str, json_resource: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Dry Evaluate a registry based on organizational policies.
    """
    resource_url = generate_resource_url(url, resource_type)
    url = f"{resource_url}evaluate/dry-run"
    return requests.post(url, headers=headers, data=json_resource)


def evaluate(
    url: str,
    resource_type: str,
    fides_key: str,
    tag: str,
    message: str,
    headers: Dict[str, str],
) -> requests.Response:
    """
    Evaluate a registry based on organizational policies.
    """
    resource_url = generate_resource_url(url, resource_type)
    url = f"{resource_url}evaluate/{fides_key}"
    return requests.get(url, headers=headers, params={"tag": tag, "message": message})


def db_action(
    server_url: str,
    headers: Dict[str, str],
    action: str,
) -> requests.Response:
    """
    Tell the API to perform a database action.
    """
    return requests.post(
        f"{server_url}{API_PREFIX}/admin/db/{action}",
        headers=headers,
        allow_redirects=False,
        timeout=30,
    )
