from json import dumps
from typing import Generator, List
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.db.crud import (
    create_resource,
    delete_resource,
    get_custom_fields_filtered,
    get_resource_with_custom_fields,
    list_resource,
)
from fides.api.models import sql_models
from fides.api.util.errors import QueryError
from fides.config import FidesConfig
from fides.core import api as _api
from tests.ctl.types import FixtureRequest


@pytest.fixture(name="created_resources")
def fixture_created_resources(
    test_config: FidesConfig, request: FixtureRequest
) -> Generator:
    """
    Creates a set of resources for testing and cleans them up after the test.
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
    ["data_category", "data_use"],
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


@pytest.mark.integration
async def test_delete_fails_linked_resources(
    linked_dataset,
    async_session: AsyncSession,
) -> None:
    """Deleting a resource should fail if a linked resource (without cascade delete relationship) still exists."""
    with pytest.raises(HTTPException) as e:
        await delete_resource(
            sql_models.Dataset, linked_dataset.fides_key, async_session
        )

    assert "try deleting related resources first" in str(e)


@pytest.fixture(scope="function")
def custom_field_definition_data_use(db):
    custom_field_definition_data = {
        "name": "custom_field_def_string_data_use_1",
        "field_type": "string[]",
        "resource_type": "data_use",
        "field_definition": "string",
    }
    custom_field_definition = sql_models.CustomFieldDefinition.create(
        db=db, data=custom_field_definition_data
    )
    yield custom_field_definition
    db.delete(custom_field_definition)


@pytest.fixture(scope="function")
def custom_fields_data_use(
    db,
    custom_field_definition_data_use,
):
    field_1 = sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition_data_use.resource_type,
            "resource_id": "advertising",
            "custom_field_definition_id": custom_field_definition_data_use.id,
            "value": ["Test value 1"],
        },
    )

    field_2 = sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition_data_use.resource_type,
            "resource_id": "third_party_sharing",
            "custom_field_definition_id": custom_field_definition_data_use.id,
            "value": ["Test value 2"],
        },
    )

    yield field_1, field_2
    db.delete(field_1)
    db.delete(field_2)


@pytest.fixture(scope="function")
def custom_field_definition_system(db):
    custom_field_definition_data = {
        "name": "custom_field_def_string_system_1",
        "field_type": "string[]",
        "resource_type": "system",
        "field_definition": "string",
    }
    custom_field_definition = sql_models.CustomFieldDefinition.create(
        db=db, data=custom_field_definition_data
    )
    yield custom_field_definition
    db.delete(custom_field_definition)


@pytest.fixture(scope="function")
def custom_field_definition_system_2(db):
    custom_field_definition_data = {
        "name": "custom_field_def_string_system_2",
        "field_type": "string",
        "resource_type": "system",
        "field_definition": "string",
    }
    custom_field_definition = sql_models.CustomFieldDefinition.create(
        db=db, data=custom_field_definition_data
    )
    yield custom_field_definition
    db.delete(custom_field_definition)


@pytest.fixture(scope="function")
def custom_field_definition_system_disabled(db):
    """A disabled custom field on system, to ensure its data is filtered out properly"""
    custom_field_definition_data = {
        "name": "disabled custom field",
        "field_type": "string",
        "resource_type": "system",
        "field_definition": "string",
        "active": False,
    }
    custom_field_definition = sql_models.CustomFieldDefinition.create(
        db=db, data=custom_field_definition_data
    )
    yield custom_field_definition
    db.delete(custom_field_definition)


@pytest.fixture(scope="function")
def custom_fields_system(
    db,
    system,
    system_third_party_sharing,
    custom_field_definition_system,
    custom_field_definition_system_2,
    custom_field_definition_system_disabled,
):
    field_1 = sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition_system.resource_type,
            "resource_id": system.fides_key,
            "custom_field_definition_id": custom_field_definition_system.id,
            "value": ["Test value 1"],
        },
    )

    field_2 = sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition_system.resource_type,
            "resource_id": system.fides_key,
            "custom_field_definition_id": custom_field_definition_system.id,
            "value": ["Test value 2"],
        },
    )

    field_3 = sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition_system_2.resource_type,
            "resource_id": system.fides_key,
            "custom_field_definition_id": custom_field_definition_system_2.id,
            "value": ["Test value 3"],
        },
    )

    field_4 = sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition_system_2.resource_type,
            "resource_id": system_third_party_sharing.fides_key,
            "custom_field_definition_id": custom_field_definition_system_2.id,
            "value": ["Test value 4"],
        },
    )
    field_5 = sql_models.CustomField.create(
        db=db,
        data={
            "resource_type": custom_field_definition_system_disabled.resource_type,
            "resource_id": system_third_party_sharing.fides_key,
            "custom_field_definition_id": custom_field_definition_system_disabled.id,
            "value": ["Disabled value, should be filtered out!"],
        },
    )

    yield (field_1, field_2, field_3, field_4, field_5)
    db.delete(field_1)
    db.delete(field_2)
    db.delete(field_3)
    db.delete(field_4)
    db.delete(field_5)


async def test_get_custom_fields_filtered(
    db,
    async_session,
    system,
    system_third_party_sharing,
    custom_fields_system,
    custom_fields_data_use,
):
    # we should get all results because we've specified both systems
    filtered_fields = await get_custom_fields_filtered(
        async_session,
        {
            sql_models.ResourceTypes.system: [
                system.fides_key,
                system_third_party_sharing.fides_key,
            ],
            sql_models.ResourceTypes.data_use: [
                custom_fields_data_use[0].resource_id,
                custom_fields_data_use[1].resource_id,
            ],
        },
    )
    for field in custom_fields_system:
        cfd = sql_models.CustomFieldDefinition.get_by_key_or_id(
            db=db, data={"id": field.custom_field_definition_id}
        )
        if cfd.active:  # only active fields should be in our result
            assert any(
                [
                    (
                        field.resource_id == f["resource_id"]
                        and field.value == f["value"]
                        and cfd.name == f["name"]
                        and cfd.field_type == f["field_type"]
                    )
                    for f in filtered_fields
                ]
            )
        else:  # inactive fields should NOT be in our result
            assert not any(
                [
                    (
                        field.resource_id == f["resource_id"]
                        and field.value == f["value"]
                        and cfd.name == f["name"]
                        and cfd.field_type == f["field_type"]
                    )
                    for f in filtered_fields
                ]
            )

    for field in custom_fields_data_use:
        cfd = sql_models.CustomFieldDefinition.get_by_key_or_id(
            db=db, data={"id": field.custom_field_definition_id}
        )
        assert any(
            [
                (
                    field.resource_id == f["resource_id"]
                    and field.value == f["value"]
                    and cfd.name == f["name"]
                    and cfd.field_type == f["field_type"]
                )
                for f in filtered_fields
            ]
        )

    # we should get only field 4 because we've specified only its system
    filtered_fields = await get_custom_fields_filtered(
        async_session,
        {sql_models.ResourceTypes.system: [system_third_party_sharing.fides_key]},
    )
    assert len(filtered_fields) == 1
    assert (
        filtered_fields[0]["resource_id"] == custom_fields_system[3].resource_id
        and filtered_fields[0]["value"] == custom_fields_system[3].value
    )

    # we should get only first 3 fields because we've specified only their system
    filtered_fields = await get_custom_fields_filtered(
        async_session, {sql_models.ResourceTypes.system: [system.fides_key]}
    )
    assert len(filtered_fields) == 3
    for i in range(0, 3):
        field = custom_fields_system[i]
        cfd = sql_models.CustomFieldDefinition.get_by_key_or_id(
            db=db, data={"id": field.custom_field_definition_id}
        )
        assert any(
            [
                (
                    field.resource_id == f["resource_id"]
                    and field.value == f["value"]
                    and cfd.name == f["name"]
                    and cfd.field_type == f["field_type"]
                )
                for f in filtered_fields
            ]
        )

    # we should get only a single field for each type because of our filtering
    filtered_fields = await get_custom_fields_filtered(
        async_session,
        {
            sql_models.ResourceTypes.system: [
                system_third_party_sharing.fides_key,
            ],
            sql_models.ResourceTypes.data_use: [
                custom_fields_data_use[1].resource_id,
            ],
        },
    )

    assert len(filtered_fields) == 2
    # only system field 4 because we've specified only its system
    assert any(
        (
            custom_fields_system[3].resource_id == f["resource_id"]
            and custom_fields_system[3].value == f["value"]
            and cfd.field_type == f["field_type"]
        )
        for f in filtered_fields
    )
    # only data_use field 2 because we've specified only its data_use
    assert any(
        (
            custom_fields_data_use[1].resource_id == f["resource_id"]
            and custom_fields_data_use[1].value == f["value"]
        )
        for f in filtered_fields
    )


async def test_get_resource_with_custom_field(db, async_session_temp):
    system_data = {
        "name": "my system",
        "system_type": "test",
        "fides_key": str(uuid4()),
    }

    system = await create_resource(sql_models.System, system_data, async_session_temp)

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
        sql_models.System, system.fides_key, async_session_temp
    )

    assert result["name"] == system.name
    assert custom_field_definition.name in result
    assert result[custom_field_definition.name] == "Test value 1, Test value 2"


async def test_get_resource_with_custom_field_no_custom_field(async_session_temp):
    system_data = {
        "name": "my system",
        "system_type": "test",
        "fides_key": str(uuid4()),
    }

    system = await create_resource(sql_models.System, system_data, async_session_temp)
    result = await get_resource_with_custom_fields(
        sql_models.System, system.fides_key, async_session_temp
    )

    assert result["name"] == system.name


async def test_get_resource_with_custom_field_error(async_session, monkeypatch):
    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError

    monkeypatch.setattr("fides.api.db.crud.AsyncSession.execute", mock_execute)
    with pytest.raises(QueryError):
        await get_resource_with_custom_fields(sql_models.System, "ABC", async_session)
