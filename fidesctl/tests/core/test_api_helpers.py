import uuid
from typing import Optional, List
import pytest

from fidesctl.core import api_helpers as _api_helpers
from fidesctl.core import api as _api

from fideslang import model_list, FidesModel

RESOURCE_CREATION_COUNT = 5
# These resources have tricky validation so the fides_key replacement doesn't work
EXCLUDED_RESOURCE_TYPES = "data_category", "data_use", "data_qualifier"
PARAM_MODEL_LIST = [
    model for model in model_list if model not in EXCLUDED_RESOURCE_TYPES
]

# Fixtures
@pytest.fixture
def created_resources(test_config, resources_dict, request):
    """
    Fixture that creates and tears down a set of resources for each test run.
    Only creates resources for a given type based on test parameter
    """
    created_keys = []
    resource_type = request.param
    for _ in range(RESOURCE_CREATION_COUNT):
        base_resource = resources_dict[resource_type].copy()
        base_resource.fides_key = "{}_{}".format(
            base_resource.fides_key, str(uuid.uuid4())[:6]
        )
        _api.create(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            json_resource=base_resource.json(exclude_none=True),
            headers=test_config.user.request_headers,
        )
        created_keys.append(base_resource.fides_key)

    # Wait for test to finish before cleaning up resources
    yield resource_type, created_keys

    for created_key in created_keys:
        _api.delete(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            resource_id=created_key,
            headers=test_config.user.request_headers,
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "created_resources", PARAM_MODEL_LIST, indirect=["created_resources"]
)
def test_get_server_resource_found_resource(test_config, created_resources):
    """
    Tests that an existing resource is returned by helper
    """
    resource_type = created_resources[0]
    resource_key = created_resources[1][0]
    result: Optional[FidesModel] = _api_helpers.get_server_resource(
        url=test_config.cli.server_url,
        resource_type=resource_type,
        resource_key=resource_key,
        headers=test_config.user.request_headers,
    )
    assert result.fides_key == resource_key


@pytest.mark.integration
@pytest.mark.parametrize("resource_type", PARAM_MODEL_LIST)
def test_get_server_resource_missing_resource(test_config, resource_type):
    """
    Tests that a missing resource returns None
    """
    resource_key = str(uuid.uuid4())
    result: Optional[FidesModel] = _api_helpers.get_server_resource(
        url=test_config.cli.server_url,
        resource_type=resource_type,
        resource_key=resource_key,
        headers=test_config.user.request_headers,
    )
    assert result is None


@pytest.mark.integration
@pytest.mark.parametrize(
    "created_resources", PARAM_MODEL_LIST, indirect=["created_resources"]
)
def test_get_server_resources_found_resources(test_config, created_resources):
    """
    Tests that existing resources are returned by helper
    """
    resource_type = created_resources[0]
    resource_keys = created_resources[1]
    result: List[FidesModel] = _api_helpers.get_server_resources(
        url=test_config.cli.server_url,
        resource_type=resource_type,
        existing_keys=resource_keys,
        headers=test_config.user.request_headers,
    )
    assert set(resource_keys) == set([resource.fides_key for resource in result])


@pytest.mark.integration
@pytest.mark.parametrize("resource_type", PARAM_MODEL_LIST)
def test_get_server_resources_missing_resources(test_config, resource_type):
    """
    Tests that a missing resource returns an empty list
    """
    resource_keys = [str(uuid.uuid4())]
    result: List[FidesModel] = _api_helpers.get_server_resources(
        url=test_config.cli.server_url,
        resource_type=resource_type,
        existing_keys=resource_keys,
        headers=test_config.user.request_headers,
    )
    assert result == []
