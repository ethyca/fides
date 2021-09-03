"""A wrapper to make calling the API consistent across Fidesctl."""
from typing import Dict

import requests


def generate_object_url(
    url: str, object_type: str = "", object_id: str = "", version: str = "v1"
) -> str:
    """
    Generate an object's URL using a base url, the object type and a version.
    """
    return f"{url}/{version}/{object_type.replace('_', '-')}/{object_id}"


def find(
    url: str, object_type: str, object_key: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Get an object by its fidesKey.
    """
    object_url = generate_object_url(url, object_type)
    find_url = f"{object_url}find/{object_key}"
    return requests.get(find_url, headers=headers)


def get(
    url: str, object_type: str, object_id: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Get an object by its id.
    """
    object_url = generate_object_url(url, object_type, object_id)
    return requests.get(object_url, headers=headers)


def create(
    url: str, object_type: str, json_object: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Create a new object.
    """
    object_url = generate_object_url(url, object_type)
    return requests.post(object_url, headers=headers, data=json_object)


def ping(url: str) -> requests.Response:
    """
    Pings the Server on the base url to make sure it's available.
    """
    return requests.get(url)


def delete(
    url: str, object_type: str, object_id: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Delete an object by its id.
    """
    object_url = generate_object_url(url, object_type, object_id)
    return requests.delete(object_url, headers=headers)


def ls(  # pylint: disable=invalid-name
    url: str, object_type: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Get a list of all of the objects of a certain type.
    """
    object_url = generate_object_url(url, object_type)
    return requests.get(object_url, headers=headers)


def update(
    url: str,
    object_type: str,
    object_id: str,
    json_object: Dict,
    headers: Dict[str, str],
) -> requests.Response:
    """
    Update an existing object.
    """
    object_url = generate_object_url(url, object_type, object_id)
    return requests.post(object_url, headers=headers, data=json_object)


def dry_evaluate(
    url: str, object_type: str, json_object: str, headers: Dict[str, str]
) -> requests.Response:
    """
    Dry Evaluate a registry based on organizational policies.
    """
    object_url = generate_object_url(url, object_type)
    url = f"{object_url}evaluate/dry-run"
    return requests.post(url, headers=headers, data=json_object)


def evaluate(
    url: str,
    object_type: str,
    fides_key: str,
    tag: str,
    message: str,
    headers: Dict[str, str],
) -> requests.Response:
    """
    Evaluate a registry based on organizational policies.
    """
    object_url = generate_object_url(url, object_type)
    url = f"{object_url}evaluate/{fides_key}"
    return requests.get(url, headers=headers, params={"tag": tag, "message": message})
