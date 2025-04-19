# pylint: disable=missing-docstring, redefined-outer-name

import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.models.sql_models import CustomFieldDefinition


@pytest.fixture(scope="function")
def clear_custom_metadata_resources(db):
    """
    Fixture run on each test to clear custom field DB tables,
    to ensure each test runs with a clean slate.
    """

    def delete_data(tables):
        for table in tables:
            table.query(db).delete()
        db.commit()

    tables = [
        CustomFieldDefinition,
    ]

    delete_data(tables)

    yield
    delete_data(tables)


def test_custom_field_definition_duplicate_name_rejected_create(db):
    """Assert case-insensitive unique checks on name/resource type upon creation"""
    definition1 = CustomFieldDefinition.create(
        db=db,
        data={
            "name": "test1",
            "description": "test",
            "field_type": "string",
            "resource_type": "system",
            "field_definition": "string",
        },
    )
    with pytest.raises(KeyOrNameAlreadyExists):
        CustomFieldDefinition.create(
            db=db,
            data={
                "name": "Test1",
                "description": "test",
                "field_type": "string",
                "resource_type": "system",
                "field_definition": "string",
            },
        )

    # assert the second record didn't get created
    assert len(CustomFieldDefinition.all(db)) == 1

    # with a different resource type, we should allow creation
    definition2 = CustomFieldDefinition.create(
        db=db,
        data={
            "name": "Test1",
            "description": "test",
            "field_type": "string",
            "resource_type": "privacy_declaration",
            "field_definition": "string",
        },
    )

    # assert we've got two different records created successfully
    assert len(CustomFieldDefinition.all(db)) == 2
    assert definition1.id != definition2.id


def test_custom_field_definition_duplicate_name_different_resource_type_accepted(db):
    """Assert that we can create custom field definition with same name on a different resource type"""
    definition1 = CustomFieldDefinition.create(
        db=db,
        data={
            "name": "test1",
            "description": "test",
            "field_type": "string",
            "resource_type": "system",
            "field_definition": "string",
        },
    )

    definition2 = CustomFieldDefinition.create(
        db=db,
        data={
            "name": "test1",
            "description": "test",
            "field_type": "string",
            "resource_type": "privacy_declaration",  # different resource type, so this should be allowed
            "field_definition": "string",
        },
    )

    # assert we've got two different records created successfully
    assert len(CustomFieldDefinition.all(db)) == 2
    assert definition1.id != definition2.id


def test_custom_field_definition_duplicate_name_rejected_update(db):
    """Assert case-insensitive unique checks on name/resource type upon update"""

    definition1 = CustomFieldDefinition.create(
        db=db,
        data={
            "name": "test1",
            "description": "test",
            "field_type": "string",
            "resource_type": "system",
            "field_definition": "string",
        },
    )

    definition2 = CustomFieldDefinition.create(
        db=db,
        data={
            "name": "Test 1",  # space in name should allow creation, considered unique name
            "description": "test",
            "field_type": "string",
            "resource_type": "system",
            "field_definition": "string",
        },
    )

    # assert we've got two different records created successfully
    assert len(CustomFieldDefinition.all(db)) == 2
    assert definition1.id != definition2.id

    with pytest.raises(KeyOrNameAlreadyExists) as e:
        definition2 = definition2.update(
            db=db,
            data={
                "name": "Test1",  # if we try to update name to remove space, we should hit uniqueness error
            },
        )

    # assert update did not go through
    db.refresh(definition2)
    assert definition2.name == "Test 1"
