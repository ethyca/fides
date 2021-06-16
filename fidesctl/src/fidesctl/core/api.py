"""A wrapper to make calling the API consistent across Fidesctl."""
from typing import Dict

import requests


def generate_request_headers() -> Dict[str, str]:
    """
    Generate the headers for a request.
    """
    return {"Content-Type": "application/json", "user-id": "1"}


def generate_object_url(
    url: str, object_type: str = "", object_id: str = "", version: str = "v1"
) -> str:
    """
    Generate an object's URL using a base url, the object type and a version.
    """
    return f"{url}/{version}/{object_type}/{object_id}"


def find(url: str, object_type: str, object_key: str) -> requests.Response:
    """
    Get an object by its fidesKey.
    """
    object_url = generate_object_url(url, object_type)
    find_url = f"{object_url}find/{object_key}"
    headers = generate_request_headers()
    return requests.get(find_url, headers=headers)


def get(url: str, object_type: str, object_id: str) -> requests.Response:
    """
    Get an object by its id.
    """
    object_url = generate_object_url(url, object_type, object_id)
    headers = generate_request_headers()
    return requests.get(object_url, headers=headers)


def create(url: str, object_type: str, json_object: str) -> requests.Response:
    """
    Create a new object.
    """
    payload = json_object
    object_url = generate_object_url(url, object_type)
    headers = generate_request_headers()
    return requests.post(object_url, headers=headers, data=payload)


def ping(url: str) -> requests.Response:
    """
    Pings the Server on the base url to make sure it's available.
    """
    return requests.get(url)


def delete(url: str, object_type: str, object_id: str) -> requests.Response:
    """
    Delete an object by its id.
    """
    object_url = generate_object_url(url, object_type, object_id)
    headers = generate_request_headers()
    return requests.delete(object_url, headers=headers)


def show(url: str, object_type: str) -> requests.Response:
    """
    Get a list of all of the objects of a certain type.
    """
    object_url = generate_object_url(url, object_type)
    headers = generate_request_headers()
    return requests.get(object_url, headers=headers)


def update(
    url: str, object_type: str, object_id: str, json_object: Dict
) -> requests.Response:
    """
    Update an existing object.
    """
    object_url = generate_object_url(url, object_type, object_id)
    payload = json_object
    headers = generate_request_headers()
    return requests.post(object_url, headers=headers, data=payload)


def dry_evaluate(url: str, object_type: str, json_object: str) -> requests.Response:
    """
    Dry Evaluate a registry based on organizational policies.
    """
    object_url = generate_object_url(url, object_type)
    url = f"{object_url}evaluate/dry-run"
    payload = json_object
    headers = generate_request_headers()
    return requests.post(url, headers=headers, data=payload)


def evaluate(url: str, object_type: str, fides_key: str) -> requests.Response:
    """
    Evaluate a registry based on organizational policies.
    """
    object_url = generate_object_url(url, object_type)
    url = f"{object_url}evaluate/{fides_key}"
    headers = generate_request_headers()
    return requests.get(url, headers=headers)
