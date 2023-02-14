from json import dumps
from typing import Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.ctl import sql_models
from fides.api.ctl.database.crud import (
    create_resource,
    delete_resource,
    get_resource_with_custom_fields,
    list_resource,
)
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


async def test_get_resource_with_custom_field(db, async_session):
    system_data = {
        "name": "my system",
        "registry_id": "1",
        "system_type": "test",
        "fides_key": str(uuid4()),
    }

    system = await create_resource(sql_models.System, system_data, async_session)

    custom_definition_data = {
        "name": "test1",
        "description": "test",
        "field_type": "string",
        "resource_type": "system",
        "field_definition": "string",
    }

    custom_field_definition = sql_models.CustomFieldDefinition.create(
        db=db, data=custom_definition_data
    )

    sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition.resource_type,
            "resource_id": system.fides_key,
            "custom_field_definition_id": custom_field_definition.id,
            "value": ["Test value 1"],
        },
    )

    sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition.resource_type,
            "resource_id": system.fides_key,
            "custom_field_definition_id": custom_field_definition.id,
            "value": ["Test value 2"],
        },
    )

    result = await get_resource_with_custom_fields(
        sql_models.System, system.fides_key, async_session
    )

    assert result["name"] == system.name
    assert custom_field_definition.name in result
    assert result[custom_field_definition.name] == "Test value 1, Test value 2"


async def test_get_resource_with_custom_field_no_custom_field(async_session):
    system_data = {
        "name": "my system",
        "registry_id": "1",
        "system_type": "test",
        "fides_key": str(uuid4()),
    }

    system = await create_resource(sql_models.System, system_data, async_session)
    result = await get_resource_with_custom_fields(
        sql_models.System, system.fides_key, async_session
    )

    assert result["name"] == system.name
