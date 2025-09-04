"""Fixtures for safe_crud tests"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.db.safe_crud import create_resource
from fides.api.models import sql_models
from fides.api.models.sql_models import CustomField, CustomFieldDefinition, System


@pytest.fixture(scope="function")
def test_system_data():
    """Provides basic test data for a System resource"""
    return {
        "fides_key": f"test_system_{uuid4().hex[:8]}",
        "name": "Test System",
        "system_type": "test",
        "description": "A system for testing safe_crud operations",
    }


@pytest.fixture(scope="function")
def test_data_category_data():
    """Provides basic test data for a DataCategory resource"""
    return {
        "fides_key": f"test_data_category_{uuid4().hex[:8]}",
        "name": "Test Data Category",
        "description": "A data category for testing safe_crud operations",
    }


@pytest.fixture(scope="function")
async def created_test_system(
    test_system_data: dict, async_session: AsyncSession
) -> sql_models.System:
    """Creates a test System"""

    system = await create_resource(sql_models.System, test_system_data, async_session)
    await async_session.commit()
    return system


@pytest.fixture(scope="function")
async def created_test_data_category(
    test_data_category_data: dict, async_session: AsyncSession
) -> sql_models.DataCategory:
    """Creates a test DataCategory"""

    data_category = await create_resource(
        sql_models.DataCategory, test_data_category_data, async_session
    )
    await async_session.commit()
    return data_category


@pytest.fixture(scope="function")
def custom_field_definition_system_data(db):
    """Creates a CustomFieldDefinition for system resources"""
    custom_field_definition_data = {
        "name": f"test_custom_field_def_{uuid4().hex[:8]}",
        "field_type": "string[]",
        "resource_type": "system",
        "field_definition": "string",
        "active": True,
    }
    return CustomFieldDefinition.create(db=db, data=custom_field_definition_data)


@pytest.fixture(scope="function")
def custom_field_definition_system_inactive(db):
    """Creates an inactive CustomFieldDefinition for system resources"""
    custom_field_definition_data = {
        "name": f"test_inactive_custom_field_def_{uuid4().hex[:8]}",
        "field_type": "string",
        "resource_type": "system",
        "field_definition": "string",
        "active": False,
    }
    return CustomFieldDefinition.create(db=db, data=custom_field_definition_data)


@pytest.fixture(scope="function")
def custom_field_for_system(
    db,
    custom_field_definition_system_data: CustomFieldDefinition,
    created_test_system: System,
):
    """Creates a CustomField for a system resource"""
    custom_field_data = {
        "resource_type": custom_field_definition_system_data.resource_type,
        "resource_id": created_test_system.fides_key,
        "custom_field_definition_id": custom_field_definition_system_data.id,
        "value": ["Test custom field value"],
    }
    return CustomField.create(db=db, data=custom_field_data)


@pytest.fixture(scope="function")
def multiple_test_systems_data():
    """Provides test data for multiple System resources for batch operations"""
    base_name = f"test_system_batch_{uuid4().hex[:8]}"
    return [
        {
            "fides_key": f"{base_name}_1",
            "name": f"Test System 1 - {base_name}",
            "system_type": "test",
            "description": "First system for batch testing",
        },
        {
            "fides_key": f"{base_name}_2",
            "name": f"Test System 2 - {base_name}",
            "system_type": "test",
            "description": "Second system for batch testing",
        },
        {
            "fides_key": f"{base_name}_3",
            "name": f"Test System 3 - {base_name}",
            "system_type": "test",
            "description": "Third system for batch testing",
        },
    ]


@pytest.fixture(scope="function")
def hierarchical_data_category_data():
    """Provides hierarchical test data for DataCategory resources with parent-child relationships"""
    base_key = f"test_hierarchy_{uuid4().hex[:8]}"
    return [
        {
            "fides_key": base_key,
            "name": f"Parent Category - {base_key}",
            "description": "Parent category for testing hierarchical delete",
            "parent_key": None,
        },
        {
            "fides_key": f"{base_key}.child1",
            "name": f"Child Category 1 - {base_key}",
            "description": "First child category",
            "parent_key": base_key,
        },
        {
            "fides_key": f"{base_key}.child2",
            "name": f"Child Category 2 - {base_key}",
            "description": "Second child category",
            "parent_key": base_key,
        },
        {
            "fides_key": f"{base_key}.child1.grandchild",
            "name": f"Grandchild Category - {base_key}",
            "description": "Grandchild category",
            "parent_key": f"{base_key}.child1",
        },
    ]
