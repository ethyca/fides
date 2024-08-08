# pylint: disable=missing-docstring, redefined-outer-name
import uuid
from typing import Dict, Generator, List

import pytest
from fideslang import model_list
from fideslang.models import FidesModel

from fides.config import FidesConfig
from fides.core import api as _api
from fides.core import api_helpers as _api_helpers
from tests.ctl.types import FixtureRequest

RESOURCE_CREATION_COUNT = 5
# These resources have tricky validation so the fides_key replacement doesn't work
EXCLUDED_RESOURCE_TYPES = "data_category", "data_use"
PARAM_MODEL_LIST = [
    model for model in model_list if model not in EXCLUDED_RESOURCE_TYPES
]


# Fixtures
@pytest.fixture
def created_resources(
    test_config: FidesConfig, resources_dict: Dict, request: FixtureRequest
) -> Generator:
    """
    Fixture that creates and tears down a set of resources for each test run.
    Only creates resources for a given type based on test parameter
    """
    created_keys = []
    resource_type = request.param
    for _ in range(RESOURCE_CREATION_COUNT):
        base_resource = resources_dict[resource_type].model_copy()
        base_resource.fides_key = "{}_{}".format(
            base_resource.fides_key, str(uuid.uuid4())[:6]
        )
        _api.create(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            json_resource=base_resource.json(exclude_none=True),
            headers=test_config.user.auth_header,
        )
        created_keys.append(base_resource.fides_key)

    # Wait for test to finish before cleaning up resources
    yield resource_type, created_keys

    for created_key in created_keys:
        _api.delete(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            resource_id=created_key,
            headers=test_config.user.auth_header,
        )


def delete_resource_type(test_config: FidesConfig, resource_type: str) -> None:
    """Deletes all of the resources of a certain type."""
    url = test_config.cli.server_url
    fides_keys = [
        resource["fides_key"]
        for resource in _api.ls(
            url,
            resource_type,
            headers=test_config.user.auth_header,
        ).json()
    ]
    for fides_key in fides_keys:
        _api.delete(
            url,
            resource_type,
            fides_key,
            test_config.user.auth_header,
        )


@pytest.mark.integration
class TestGetServerResource:
    @pytest.mark.parametrize(
        "created_resources", PARAM_MODEL_LIST, indirect=["created_resources"]
    )
    def test_get_server_resource_found_resource(
        self, test_config: FidesConfig, created_resources: List
    ) -> None:
        """
        Tests that an existing resource is returned by helper
        """
        resource_type = created_resources[0]
        resource_key = created_resources[1][0]
        result: Dict = _api_helpers.get_server_resource(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            resource_key=resource_key,
            headers=test_config.user.auth_header,
        )
        assert result.get("fides_key") == resource_key

    @pytest.mark.parametrize("resource_type", PARAM_MODEL_LIST)
    def test_get_server_resource_missing_resource(
        self, test_config: FidesConfig, resource_type: str
    ) -> None:
        """
        Tests that a missing resource returns None
        """
        resource_key = str(uuid.uuid4())
        result = _api_helpers.get_server_resource(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            resource_key=resource_key,
            headers=test_config.user.auth_header,
        )
        assert not result


@pytest.mark.integration
class TestGetServerResources:
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "created_resources", PARAM_MODEL_LIST, indirect=["created_resources"]
    )
    def test_get_server_resources_found_resources(
        self, test_config: FidesConfig, created_resources: List
    ) -> None:
        """
        Tests that existing resources are returned by helper
        """
        resource_type = created_resources[0]
        resource_keys = created_resources[1]
        result: List[FidesModel] = _api_helpers.get_server_resources(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            existing_keys=resource_keys,
            headers=test_config.user.auth_header,
        )
        print(result)
        assert set(resource_keys) == set(resource.fides_key for resource in result)

    @pytest.mark.parametrize("resource_type", PARAM_MODEL_LIST)
    def test_get_server_resources_missing_resources(
        self, test_config: FidesConfig, resource_type: str
    ) -> None:
        """
        Tests that a missing resource returns an empty list
        """
        resource_keys = [str(uuid.uuid4())]
        result: List[FidesModel] = _api_helpers.get_server_resources(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            existing_keys=resource_keys,
            headers=test_config.user.auth_header,
        )
        assert result == []


@pytest.mark.integration
class TestListServerResources:
    def test_list_server_resources_passing(self, test_config: FidesConfig) -> None:
        resource_type = "data_category"
        result = _api_helpers.list_server_resources(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            headers=test_config.user.auth_header,
            exclude_keys=[],
        )
        assert result

    def test_list_server_resources_none(self, test_config: FidesConfig) -> None:
        resource_type = "system"
        delete_resource_type(test_config, resource_type)
        result: List[FidesModel] = _api_helpers.list_server_resources(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            headers=test_config.user.auth_header,
            exclude_keys=[],
        )
        assert result == []
