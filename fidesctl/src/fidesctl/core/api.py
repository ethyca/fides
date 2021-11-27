"""A wrapper to make calling the API consistent across Fidesctl."""
from typing import Dict

import requests


def generate_resource_url(
    url: str, resource_type: str = "", resource_id: str = "", version: str = "v1"
) -> str:
    """
    Generate a resource's URL using a base url, the resource type and a version.
    """
    return f"{url}/{resource_type}/{resource_id}"


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
    url: str, resource_type: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Get a list of all of the resources of a certain type.
    """
    resource_url = generate_resource_url(url, resource_type)
    return requests.get(resource_url, headers=headers)


def update(
    url: str,
    resource_type: str,
    resource_id: str,
    json_resource: Dict,
    headers: Dict[str, str],
) -> requests.Response:
    """
    Update an existing resource.
    """
    resource_url = generate_resource_url(url, resource_type, resource_id)
    return requests.post(resource_url, headers=headers, data=json_resource)


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


def db_action(server_url: str, action: str) -> requests.Response:
    """
    Tell the API to perform a database action.
    """
    return requests.post(f"{server_url}/admin/db/{action}")
