"""Tests for safe_crud module functions"""

from typing import List
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fides.api.db import safe_crud
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.sql_models import (
    CustomField,
    CustomFieldDefinition,
    DataCategory,
    ResourceTypes,
    System,
)
from fides.api.util.errors import AlreadyExistsError, NotFoundError, QueryError


class TestSafeCrudCreateResource:
    """Tests for safe_crud.create_resource function"""

    async def test_create_resource_success(
        self, test_system_data: dict, async_session: AsyncSession
    ):
        """Test successfully creating a new resource"""
        result = await safe_crud.create_resource(
            System, test_system_data, async_session
        )

        assert result is not None
        assert result.fides_key == test_system_data["fides_key"]
        assert result.name == test_system_data["name"]
        assert result.system_type == test_system_data["system_type"]

    async def test_create_resource_already_exists_error(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test creating a duplicate resource raises AlreadyExistsError"""
        duplicate_data = {
            "fides_key": created_test_system.fides_key,
            "name": "Duplicate System",
            "system_type": "test",
        }

        with pytest.raises(AlreadyExistsError) as exc_info:
            await safe_crud.create_resource(System, duplicate_data, async_session)

        assert created_test_system.fides_key in str(exc_info.value)

    async def test_create_resource_sqlalchemy_error(
        self, test_system_data: dict, async_session: AsyncSession, monkeypatch
    ):
        """Test handling SQLAlchemy errors during creation"""

        async def mock_execute(*args, **kwargs):
            raise SQLAlchemyError("Database connection failed")

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.create_resource(System, test_system_data, async_session)

    async def test_create_resource_validation_error(self, async_session: AsyncSession):
        """Test creating resource with invalid data"""
        invalid_data = {
            "fides_key": None,  # None fides_key should cause database constraint violation
            "name": "Invalid System",
            "system_type": "test",
        }

        with pytest.raises((QueryError, SQLAlchemyError)):
            await safe_crud.create_resource(System, invalid_data, async_session)


class TestSafeCrudGetResource:
    """Tests for safe_crud.get_resource function"""

    async def test_get_resource_success(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test successfully retrieving an existing resource"""
        result = await safe_crud.get_resource(
            System, created_test_system.fides_key, async_session
        )

        assert result is not None
        assert result.fides_key == created_test_system.fides_key
        assert result.name == created_test_system.name

    async def test_get_resource_not_found_with_raise(self, async_session: AsyncSession):
        """Test retrieving non-existent resource with raise_not_found=True"""
        non_existent_key = f"non_existent_{uuid4().hex[:8]}"

        with pytest.raises(NotFoundError) as exc_info:
            await safe_crud.get_resource(
                System, non_existent_key, async_session, raise_not_found=True
            )

        assert non_existent_key in str(exc_info.value)

    async def test_get_resource_not_found_without_raise(
        self, async_session: AsyncSession
    ):
        """Test retrieving non-existent resource with raise_not_found=False"""
        non_existent_key = f"non_existent_{uuid4().hex[:8]}"

        result = await safe_crud.get_resource(
            System, non_existent_key, async_session, raise_not_found=False
        )

        assert result is None

    async def test_get_resource_sqlalchemy_error(
        self, async_session: AsyncSession, monkeypatch
    ):
        """Test handling SQLAlchemy errors during retrieval"""

        async def mock_execute(*args, **kwargs):
            raise SQLAlchemyError("Database connection failed")

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.get_resource(System, "test_key", async_session)


class TestSafeCrudListResource:
    """Tests for safe_crud.list_resource and list_resource_query functions"""

    async def test_list_resource_success(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test successfully listing all resources of a type"""
        result = await safe_crud.list_resource(System, async_session)

        assert isinstance(result, list)
        assert len(result) >= 1
        system_keys = [system.fides_key for system in result]
        assert created_test_system.fides_key in system_keys

    async def test_list_resource_empty_result(self, async_session: AsyncSession):
        """Test listing resources when none exist of that type"""
        result = await safe_crud.list_resource(DataCategory, async_session)

        assert isinstance(result, list)

    async def test_list_resource_sqlalchemy_error(
        self, async_session: AsyncSession, monkeypatch
    ):
        """Test handling SQLAlchemy errors during listing"""

        async def mock_execute(*args, **kwargs):
            raise SQLAlchemyError("Database connection failed")

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.list_resource(System, async_session)

    async def test_list_resource_query_custom_query(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test list_resource_query with custom select"""

        custom_query = select(System).where(
            System.fides_key == created_test_system.fides_key
        )

        result = await safe_crud.list_resource_query(
            async_session, custom_query, System
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].fides_key == created_test_system.fides_key


class TestSafeCrudUpdateResource:
    """Tests for safe_crud.update_resource function"""

    async def test_update_resource_success(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test successfully updating an existing resource"""
        updated_data = {
            "fides_key": created_test_system.fides_key,
            "name": "Updated System Name",
            "system_type": "updated",
            "description": "Updated description",
        }

        result = await safe_crud.update_resource(System, updated_data, async_session)
        await async_session.commit()
        await async_session.refresh(result)  # Refresh to get latest data

        assert result is not None
        assert result.fides_key == created_test_system.fides_key
        assert result.name == "Updated System Name"
        assert result.system_type == "updated"
        assert result.description == "Updated description"

    async def test_update_resource_not_found(self, async_session: AsyncSession):
        """Test updating a non-existent resource"""
        non_existent_data = {
            "fides_key": f"non_existent_{uuid4().hex[:8]}",
            "name": "Non-existent System",
            "system_type": "test",
        }

        with pytest.raises(NotFoundError):
            await safe_crud.update_resource(System, non_existent_data, async_session)

    async def test_update_resource_sqlalchemy_error(
        self, created_test_system: System, async_session: AsyncSession, monkeypatch
    ):
        """Test handling SQLAlchemy errors during update"""
        update_data = {
            "fides_key": created_test_system.fides_key,
            "name": "Updated Name",
        }

        # Mock get_resource call to return the system
        mock_get_result = MagicMock()
        mock_get_scalars = MagicMock()
        mock_get_scalars.first.return_value = created_test_system
        mock_get_result.scalars.return_value = mock_get_scalars

        # Use side_effect for sequential mock responses
        mock_execute = AsyncMock(
            side_effect=[
                mock_get_result,  # First call: get_resource succeeds
                SQLAlchemyError("Update failed"),  # Second call: update fails
            ]
        )

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.update_resource(System, update_data, async_session)


class TestSafeCrudUpsertResources:
    """Tests for safe_crud.upsert_resources function"""

    async def test_upsert_resources_insert_only(
        self, multiple_test_systems_data: List[dict], async_session: AsyncSession
    ):
        """Test upserting with all new resources"""
        inserts, updates = await safe_crud.upsert_resources(
            System, multiple_test_systems_data, async_session
        )

        assert inserts == len(multiple_test_systems_data)
        assert updates == 0

    async def test_upsert_resources_update_only(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test upserting with all existing resources"""
        update_data = [
            {
                "fides_key": created_test_system.fides_key,
                "name": "Updated System Name",
                "system_type": "updated",
                "description": "Updated via upsert",
            }
        ]

        inserts, updates = await safe_crud.upsert_resources(
            System, update_data, async_session
        )
        await async_session.commit()

        assert inserts == 0
        assert updates == 1

        # Get fresh copy from database
        async_session.expunge(created_test_system)
        updated_system = await safe_crud.get_resource(
            System, created_test_system.fides_key, async_session
        )
        assert updated_system.name == "Updated System Name"

    async def test_upsert_resources_mixed(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test upserting with mix of new and existing resources"""
        mixed_data = [
            {  # Update existing
                "fides_key": created_test_system.fides_key,
                "name": "Updated Existing System",
                "system_type": "updated",
            },
            {  # Insert new
                "fides_key": f"new_system_{uuid4().hex[:8]}",
                "name": "New System",
                "system_type": "new",
            },
        ]

        inserts, updates = await safe_crud.upsert_resources(
            System, mixed_data, async_session
        )

        assert inserts == 1
        assert updates == 1

    async def test_upsert_resources_sqlalchemy_error(
        self,
        multiple_test_systems_data: List[dict],
        async_session: AsyncSession,
        monkeypatch,
    ):
        """Test handling SQLAlchemy errors during upsert"""

        async def mock_execute(*args, **kwargs):
            raise SQLAlchemyError("Upsert failed")

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.upsert_resources(
                System, multiple_test_systems_data, async_session
            )

    async def test_upsert_resources_empty_list(self, async_session: AsyncSession):
        """Test upserting with empty resource list"""
        # Empty list should be handled gracefully
        with pytest.raises(QueryError):
            # This will fail because PostgreSQL doesn't allow INSERT with no values
            await safe_crud.upsert_resources(System, [], async_session)


class TestSafeCrudDeleteResource:
    """Tests for safe_crud.delete_resource function"""

    async def test_delete_resource_success(
        self, test_system_data: dict, async_session: AsyncSession
    ):
        """Test successfully deleting a resource"""
        system = await safe_crud.create_resource(
            System, test_system_data, async_session
        )
        await async_session.commit()

        deleted_system = await safe_crud.delete_resource(
            System, system.fides_key, async_session
        )
        await async_session.commit()

        assert deleted_system.fides_key == system.fides_key

        result = await safe_crud.get_resource(
            System, system.fides_key, async_session, raise_not_found=False
        )
        assert result is None

    async def test_delete_resource_with_children(
        self, hierarchical_data_category_data: List[dict], async_session: AsyncSession
    ):
        """Test deleting a resource that has children (cascade delete)"""
        for category_data in hierarchical_data_category_data:
            await safe_crud.create_resource(DataCategory, category_data, async_session)
        await async_session.commit()

        parent_key = hierarchical_data_category_data[0]["fides_key"]

        deleted_parent = await safe_crud.delete_resource(
            DataCategory, parent_key, async_session
        )
        await async_session.commit()

        assert deleted_parent.fides_key == parent_key

        remaining_categories = await safe_crud.list_resource(
            DataCategory, async_session
        )
        remaining_keys = {cat.fides_key for cat in remaining_categories}

        for category_data in hierarchical_data_category_data:
            assert category_data["fides_key"] not in remaining_keys

    async def test_delete_resource_not_found(self, async_session: AsyncSession):
        """Test deleting a non-existent resource"""
        non_existent_key = f"non_existent_{uuid4().hex[:8]}"

        with pytest.raises(NotFoundError):
            await safe_crud.delete_resource(System, non_existent_key, async_session)

    async def test_delete_resource_foreign_key_constraint(
        self, async_session: AsyncSession, db
    ):
        """Test handling foreign key constraint errors during delete with a real constraint"""

        # Create a system
        system_data = {
            "fides_key": f"test_system_{uuid4().hex[:8]}",
            "name": "System with dependencies",
            "system_type": "test",
        }
        system = await safe_crud.create_resource(System, system_data, async_session)
        await async_session.commit()

        # Create a ConnectionConfig that references the system
        # This creates a real foreign key constraint
        connection_config_data = {
            "key": f"test_connection_{uuid4().hex[:8]}",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
            "system_id": system.id,
        }
        ConnectionConfig.create(db=db, data=connection_config_data)

        # Now try to delete the system - this should fail with a foreign key constraint
        with pytest.raises(HTTPException) as exc_info:
            await safe_crud.delete_resource(System, system.fides_key, async_session)

        assert "Foreign key constraint" in str(exc_info.value.detail)

    async def test_delete_resource_sqlalchemy_error(
        self, created_test_system: System, async_session: AsyncSession, monkeypatch
    ):
        """Test handling other SQLAlchemy errors during delete"""
        # Mock get_resource call (first) to return the resource
        mock_get_result = MagicMock()
        mock_get_scalars = MagicMock()
        mock_get_scalars.first.return_value = created_test_system
        mock_get_result.scalars.return_value = mock_get_scalars

        # Use side_effect to return different results for sequential calls
        mock_execute = AsyncMock(
            side_effect=[
                mock_get_result,  # First call: get_resource succeeds
                SQLAlchemyError(
                    "Database connection failed"
                ),  # Second call: delete fails
            ]
        )

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.delete_resource(
                System, created_test_system.fides_key, async_session
            )


class TestSafeCrudCustomFields:
    """Tests for safe_crud.get_custom_fields_filtered and get_resource_with_custom_fields functions"""

    async def test_get_custom_fields_filtered_success(
        self,
        async_session: AsyncSession,
        created_test_system: System,
        custom_field_definition_system_data: CustomFieldDefinition,
        custom_field_for_system: CustomField,
    ):
        """Test successfully getting filtered custom fields"""
        result = await safe_crud.get_custom_fields_filtered(
            async_session, {ResourceTypes.system: [created_test_system.fides_key]}
        )

        assert isinstance(result, list)
        assert len(result) >= 1

        field_found = False
        for field in result:
            if (
                field["resource_id"] == created_test_system.fides_key
                and field["name"] == custom_field_definition_system_data.name
            ):
                field_found = True
                assert field["value"] == custom_field_for_system.value
                assert (
                    field["field_type"]
                    == custom_field_definition_system_data.field_type
                )
                break

        assert field_found, "Expected custom field not found in results"

    async def test_get_custom_fields_filtered_multiple_types(
        self,
        db,
        async_session: AsyncSession,
        created_test_system: System,
        created_test_data_category: DataCategory,
        custom_field_definition_system_data: CustomFieldDefinition,
        custom_field_for_system: CustomField,
    ):
        """Test filtering custom fields across multiple resource types"""
        # Create a custom field definition for data category
        data_category_field_def_data = {
            "name": f"test_data_cat_field_{uuid4().hex[:8]}",
            "field_type": "string",
            "resource_type": "data_category",
            "field_definition": "string",
            "active": True,
        }
        data_category_field_def = CustomFieldDefinition.create(
            db=db, data=data_category_field_def_data
        )

        data_category_field_data = {
            "resource_type": "data_category",
            "resource_id": created_test_data_category.fides_key,
            "custom_field_definition_id": data_category_field_def.id,
            "value": ["Data category custom value"],
        }
        CustomField.create(db=db, data=data_category_field_data)

        result = await safe_crud.get_custom_fields_filtered(
            async_session,
            {
                ResourceTypes.system: [created_test_system.fides_key],
                ResourceTypes.data_category: [created_test_data_category.fides_key],
            },
        )

        assert isinstance(result, list)
        assert len(result) >= 2

        system_field_found = False
        data_category_field_found = False

        for field in result:
            if field["resource_id"] == created_test_system.fides_key:
                system_field_found = True
            elif field["resource_id"] == created_test_data_category.fides_key:
                data_category_field_found = True

        assert system_field_found and data_category_field_found

    async def test_get_custom_fields_filtered_only_active(
        self,
        db,
        async_session: AsyncSession,
        created_test_system: System,
        custom_field_definition_system_data: CustomFieldDefinition,
        custom_field_definition_system_inactive: CustomFieldDefinition,
    ):
        """Test that only active custom field definitions are returned"""
        # Create custom fields for both active and inactive definitions
        active_field_data = {
            "resource_type": "system",
            "resource_id": created_test_system.fides_key,
            "custom_field_definition_id": custom_field_definition_system_data.id,
            "value": ["Active field value"],
        }
        CustomField.create(db=db, data=active_field_data)

        inactive_field_data = {
            "resource_type": "system",
            "resource_id": created_test_system.fides_key,
            "custom_field_definition_id": custom_field_definition_system_inactive.id,
            "value": ["Inactive field value"],
        }
        CustomField.create(db=db, data=inactive_field_data)

        result = await safe_crud.get_custom_fields_filtered(
            async_session, {ResourceTypes.system: [created_test_system.fides_key]}
        )

        assert isinstance(result, list)

        active_field_found = False
        inactive_field_found = False

        for field in result:
            if field["resource_id"] == created_test_system.fides_key:
                if field["name"] == custom_field_definition_system_data.name:
                    active_field_found = True
                elif field["name"] == custom_field_definition_system_inactive.name:
                    inactive_field_found = True

        assert active_field_found, "Active custom field should be found"
        assert not inactive_field_found, "Inactive custom field should not be found"

    async def test_get_custom_fields_filtered_empty_result(
        self, async_session: AsyncSession
    ):
        """Test getting custom fields when no matching resources exist"""
        result = await safe_crud.get_custom_fields_filtered(
            async_session, {ResourceTypes.system: [f"non_existent_{uuid4().hex[:8]}"]}
        )

        assert isinstance(result, list)
        assert len(result) == 0

    async def test_get_custom_fields_filtered_sqlalchemy_error(
        self, async_session: AsyncSession, monkeypatch
    ):
        """Test handling SQLAlchemy errors during custom fields retrieval"""

        async def mock_execute(*args, **kwargs):
            raise SQLAlchemyError("Database connection failed")

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.get_custom_fields_filtered(
                async_session, {ResourceTypes.system: ["test_key"]}
            )

    async def test_get_resource_with_custom_fields_success(
        self,
        async_session: AsyncSession,
        created_test_system: System,
        custom_field_definition_system_data: CustomFieldDefinition,
        custom_field_for_system: CustomField,
    ):
        """Test getting a resource with its custom fields"""
        result = await safe_crud.get_resource_with_custom_fields(
            System, created_test_system.fides_key, async_session
        )

        assert isinstance(result, dict)
        assert result["fides_key"] == created_test_system.fides_key
        assert result["name"] == created_test_system.name
        assert custom_field_definition_system_data.name in result
        assert result[custom_field_definition_system_data.name] == ", ".join(
            custom_field_for_system.value
        )

    async def test_get_resource_with_custom_fields_no_custom_fields(
        self, created_test_system: System, async_session: AsyncSession
    ):
        """Test getting a resource without custom fields"""
        result = await safe_crud.get_resource_with_custom_fields(
            System, created_test_system.fides_key, async_session
        )

        assert isinstance(result, dict)
        assert result["fides_key"] == created_test_system.fides_key
        assert result["name"] == created_test_system.name

    async def test_get_resource_with_custom_fields_multiple_values(
        self,
        db,
        async_session: AsyncSession,
        created_test_system: System,
        custom_field_definition_system_data: CustomFieldDefinition,
    ):
        """Test getting a resource with multiple custom field values"""
        # Create multiple custom fields for the same definition
        field1_data = {
            "resource_type": "system",
            "resource_id": created_test_system.fides_key,
            "custom_field_definition_id": custom_field_definition_system_data.id,
            "value": ["First value"],
        }
        CustomField.create(db=db, data=field1_data)

        field2_data = {
            "resource_type": "system",
            "resource_id": created_test_system.fides_key,
            "custom_field_definition_id": custom_field_definition_system_data.id,
            "value": ["Second value"],
        }
        CustomField.create(db=db, data=field2_data)

        result = await safe_crud.get_resource_with_custom_fields(
            System, created_test_system.fides_key, async_session
        )

        assert isinstance(result, dict)
        assert custom_field_definition_system_data.name in result
        custom_field_value = result[custom_field_definition_system_data.name]
        assert "First value" in custom_field_value
        assert "Second value" in custom_field_value

    async def test_get_resource_with_custom_fields_sqlalchemy_error(
        self, created_test_system: System, async_session: AsyncSession, monkeypatch
    ):
        """Test handling SQLAlchemy errors during resource with custom fields retrieval"""
        original_execute = async_session.execute

        async def mock_execute(*args, **kwargs):
            # Let first call (get_resource) pass through normally
            # Fail on second call (custom fields query)
            if "custom_field" in str(args[0]).lower():
                raise SQLAlchemyError("Custom fields query failed")
            return await original_execute(*args, **kwargs)

        monkeypatch.setattr(async_session, "execute", mock_execute)

        with pytest.raises(QueryError):
            await safe_crud.get_resource_with_custom_fields(
                System, created_test_system.fides_key, async_session
            )
