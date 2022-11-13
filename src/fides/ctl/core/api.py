"""A wrapper to make calling the API consistent across fides."""
from types import ModuleType
from typing import Any, Callable, Dict, List, Union

import requests
from starlette.testclient import TestClient

from fides.api.ctl.routes.util import API_PREFIX
from fides.ctl.core.config import get_config

CONFIG = get_config()


def verify_client(func: Callable) -> Callable:
    def api_wrapper(*args: Any, **kwargs: Any) -> requests.Response:
        """Passes the TestClient (and enforces it exists) in test mode to use to call the API,
        otherwise uses the requests library

        We want to use the TestClient in pytest to not make requests against the running webserver,
        but to write and query against the test db.
        """
        client = kwargs.get("client")
        if CONFIG.test_mode:
            if not client:
                raise Exception(
                    f"Supply TestClient as a kwarg to '{func.__name__}' method in test_mode"
                )
        else:
            kwargs["client"] = requests
        return func(*args, **kwargs)

    return api_wrapper


def generate_resource_url(
    url: str,
    resource_type: str = "",
    resource_id: str = "",
) -> str:
    """
    Generate a resource's URL using a base url, the resource type,
    and [optionally] the resource's ID.
    """
    return f"{url}{API_PREFIX}/{resource_type}/{resource_id}"


@verify_client
def get(
    url: str,
    resource_type: str,
    resource_id: str,
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Get a resource by its id.
    """

    resource_url = generate_resource_url(url, resource_type, resource_id)
    return client.get(resource_url, headers=headers)


@verify_client
def create(
    url: str,
    resource_type: str,
    json_resource: str,
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Create a new resource.
    """
    resource_url = generate_resource_url(url, resource_type)
    return client.post(resource_url, headers=headers, data=json_resource)


def ping(url: str) -> requests.Response:
    """
    Pings the Server on the base url to make sure it's available.
    """
    return requests.get(url)


@verify_client
def delete(
    url: str,
    resource_type: str,
    resource_id: str,
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Delete a resource by its id.
    """
    resource_url = generate_resource_url(url, resource_type, resource_id)
    return client.delete(resource_url, headers=headers)


@verify_client
def ls(  # pylint: disable=invalid-name
    url: str,
    resource_type: str,
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Get a list of all of the resources of a certain type.
    """
    resource_url = generate_resource_url(url, resource_type)
    return client.get(resource_url, headers=headers)


@verify_client
def update(
    url: str,
    resource_type: str,
    json_resource: Dict,
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Update an existing resource.
    """
    resource_url = generate_resource_url(url, resource_type)
    return client.put(resource_url, headers=headers, data=json_resource)


@verify_client
def upsert(
    url: str,
    resource_type: str,
    resources: List[Dict],
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    For each resource, insert the resource if it doesn't exist, update the resource otherwise.
    """

    resource_url = generate_resource_url(url, resource_type) + "upsert"
    return client.post(resource_url, headers=headers, json=resources)


@verify_client
def dry_evaluate(
    url: str,
    resource_type: str,
    json_resource: str,
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Dry Evaluate a registry based on organizational policies.
    """
    resource_url = generate_resource_url(url, resource_type)
    url = f"{resource_url}evaluate/dry-run"
    return client.post(url, headers=headers, data=json_resource)


@verify_client
def evaluate(
    url: str,
    resource_type: str,
    fides_key: str,
    tag: str,
    message: str,
    headers: Dict[str, str],
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Evaluate a registry based on organizational policies.
    """
    resource_url = generate_resource_url(url, resource_type)
    url = f"{resource_url}evaluate/{fides_key}"
    return client.get(url, headers=headers, params={"tag": tag, "message": message})


@verify_client
def db_action(
    server_url: str,
    action: str,
    client: Union[TestClient, ModuleType],
) -> requests.Response:
    """
    Tell the API to perform a database action.
    """
    return client.post(f"{server_url}{API_PREFIX}/admin/db/{action}")
