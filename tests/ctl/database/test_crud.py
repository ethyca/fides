from json import dumps
from typing import Generator, List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.ctl import sql_models
from fides.api.ctl.database.crud import delete_resource, list_resource
from fides.core import api as _api
from fides.core.config import FidesConfig
from tests.ctl.types import FixtureRequest


@pytest.fixture(name="created_resources")
def fixture_created_resources(
    test_config: FidesConfig, request: FixtureRequest
) -> Generator:
    """
    Fixture that creates and tears down a set of resources for each test run.
    Only creates resources for a given type based on test parameter
    """
    created_keys = []
    resource_type = request.param
    to_create = ["foo", "foo.bar", "foo.bar.baz", "foo.boo"]

    for key in to_create:
        parent_key = ".".join(key.split(".")[:-1]) if "." in key else None

        _api.create(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            json_resource=dumps({"fides_key": key, "parent_key": parent_key}),
            headers=test_config.user.auth_header,
        )
        created_keys.append(key)

    # Wait for test to finish before cleaning up resources
    yield resource_type, created_keys

    for created_key in created_keys:
        _api.delete(
            url=test_config.cli.server_url,
            resource_type=resource_type,
            resource_id=created_key,
            headers=test_config.user.auth_header,
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "created_resources",
    ["data_category", "data_use", "data_qualifier"],
    indirect=["created_resources"],
)
async def test_cascade_delete_taxonomy_children(
    created_resources: List, async_session: AsyncSession
) -> None:
    """Deleting a parent taxonomy should delete all of its children too"""
    resource_type, keys = created_resources
    sql_model = sql_models.sql_model_map[resource_type]
    await delete_resource(sql_model, keys[0], async_session)
    resources = await list_resource(sql_model, async_session)
    remaining_keys = {resource.fides_key for resource in resources}
    assert len(set(keys).intersection(remaining_keys)) == 0
