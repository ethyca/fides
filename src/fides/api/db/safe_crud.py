"""
This module contains "safe" versions of CRUD operations that do NOT
manually manage database transactions. Transaction management is left
to the calling code (endpoints, services) to handle at the appropriate
boundary.

Use functions from this module instead of fides.api.db.crud
"""

from collections import defaultdict
from typing import Any, Dict, List, Tuple, Type, TypeVar

from fastapi import HTTPException
from loguru import logger as log
from sqlalchemy import and_, column
from sqlalchemy import delete as _delete
from sqlalchemy import or_
from sqlalchemy import update as _update
from sqlalchemy.dialects.postgresql import Insert as _insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Select
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    CustomField,
    CustomFieldDefinition,
    FidesBase,
    ResourceTypes,
)
from fides.api.util import errors

# Helps return type be linked to the type of the parameter
T = TypeVar("T", bound="FidesBase")


# CRUD Functions
async def create_resource(
    sql_model: Type[T], resource_dict: Dict, async_session: AsyncSession
) -> T:
    """
    Create a resource in the database.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """
    with log.contextualize(
        sql_model=sql_model.__name__, fides_key=resource_dict["fides_key"]
    ):

        existing_resource = await get_resource(
            sql_model, resource_dict["fides_key"], async_session, raise_not_found=False
        )

        if existing_resource is not None:
            already_exists_error = errors.AlreadyExistsError(
                sql_model.__name__, resource_dict["fides_key"]
            )
            log.bind(error=already_exists_error.detail["error"]).info(  # type: ignore[index]
                "Failed to insert resource"
            )
            raise already_exists_error

        try:
            log.debug("Creating resource")
            query = _insert(sql_model.__table__).values(resource_dict)
            await async_session.execute(query)
        except SQLAlchemyError as e:
            log.exception(f"Failed to create resource with error: '{e}'")
            sa_error = errors.QueryError()
            raise sa_error

        return await get_resource(sql_model, resource_dict["fides_key"], async_session)


async def get_custom_fields_filtered(
    async_session: AsyncSession,
    resource_types_to_ids: Dict[ResourceTypes, List[str]] = defaultdict(list),
) -> FidesBase:
    """
    Utility function to construct a filtered query for custom field values based on provided mapping of
    resource types to resource IDs.

    Only custom fields with an "active" CustomFieldDefinition are returned.

    This is for use in bulk querying of custom fields, to avoid multiple round trips to the db.
    """
    with log.contextualize(model=CustomField):
        try:
            log.debug("Fetching resource")
            query = select(
                CustomField.resource_id,
                CustomField.value,
                CustomFieldDefinition.resource_type,
                CustomFieldDefinition.name,
                CustomFieldDefinition.field_type,
            ).join(
                CustomFieldDefinition,
                CustomFieldDefinition.id == CustomField.custom_field_definition_id,
            )

            criteria = [
                and_(
                    CustomFieldDefinition.resource_type == resource_type.value,
                    CustomField.resource_id.in_(resource_ids),
                    # pylint: disable=singleton-comparison
                    CustomFieldDefinition.active == True,
                )
                for resource_type, resource_ids in resource_types_to_ids.items()
            ]
            query = query.where(or_(False, *criteria))
            result = await async_session.execute(query)
            return result.mappings().all()
        except SQLAlchemyError as e:
            sa_error = errors.QueryError()
            log.exception(f"Failed to fetch custom fields with error: '{e}'")
            raise sa_error


async def get_resource(
    sql_model: Type[T],
    fides_key: str,
    async_session: AsyncSession,
    raise_not_found: bool = True,
) -> T:
    """
    Get a resource from the database by its FidesKey.

    Returns a SQLAlchemy model of that resource.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """
    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        try:
            log.debug("Fetching resource")
            query = select(sql_model).where(sql_model.fides_key == fides_key)
            result = await async_session.execute(query)
        except SQLAlchemyError as e:
            sa_error = errors.QueryError()
            log.exception(f"Failed to fetch resource with error: '{e}'")
            raise sa_error

        sql_resource = result.scalars().first()
        if sql_resource is None and raise_not_found:
            not_found_error = errors.NotFoundError(sql_model.__name__, fides_key)
            log.bind(error=not_found_error.detail["error"]).info("Resource not found")  # type: ignore[index]
            raise not_found_error

        return sql_resource


async def get_resource_with_custom_fields(
    sql_model: Type[T], fides_key: str, async_session: AsyncSession
) -> Dict[str, Any]:
    """Get a resource from the database by its FidesKey including it's custom fields.

    Returns a dictionary of that resource.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """
    resource: T = await get_resource(sql_model, fides_key, async_session)
    resource_dict = resource.__dict__
    resource_dict.pop("_sa_instance_state", None)

    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        try:
            log.debug("Fetching custom fields for resource")
            query = (
                select(CustomFieldDefinition.name, CustomField.value)
                .join(
                    CustomField,
                    CustomField.custom_field_definition_id == CustomFieldDefinition.id,
                )
                .where(
                    (CustomField.resource_id == resource.fides_key)
                    & (  # pylint: disable=singleton-comparison
                        CustomFieldDefinition.active == True
                    )
                )
            )
            result = await async_session.execute(query)
        except SQLAlchemyError as e:
            sa_error = errors.QueryError()
            log.exception(f"Failed to fetch custom fields with error: '{e}'")
            raise sa_error

        custom_fields = result.mappings().all()

    if not custom_fields:
        return resource_dict

    for field in custom_fields:
        if field["name"] in resource_dict:
            resource_dict[field["name"]] = (
                f"{resource_dict[field['name']]}, {', '.join(field['value'])}"
            )
        else:
            resource_dict[field["name"]] = ", ".join(field["value"])

    return resource_dict


async def list_resource(sql_model: Type[T], async_session: AsyncSession) -> List[T]:
    """
    Get a list of all of the resources of this type from the database.

    Returns a list of SQLAlchemy models of that resource type.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """
    query = select(sql_model)
    return await list_resource_query(async_session, query, sql_model)


async def list_resource_query(
    async_session: AsyncSession, query: Select, sql_model: Type[T]
) -> List[T]:
    """
    Utility function to wrap a select query in generic "list_resource" execution handling.
    Wrapping includes execution against the DB session, logging and error handling.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """

    with log.contextualize(sql_model=sql_model.__name__):
        try:
            log.debug("Fetching resources")
            result = await async_session.execute(query)
            sql_resources = result.scalars().all()
        except SQLAlchemyError as e:
            log.exception(f"Failed to fetch resources with error: '{e}'")
            sa_error = errors.QueryError()
            raise sa_error

        return sql_resources


async def update_resource(
    sql_model: Type[T], resource_dict: Dict, async_session: AsyncSession
) -> Dict:
    """
    Update a resource in the database by its fides_key.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """

    with log.contextualize(
        sql_model=sql_model.__name__, fides_key=resource_dict["fides_key"]
    ):
        await get_resource(sql_model, resource_dict["fides_key"], async_session)

        try:
            log.debug("Updating resource")
            await async_session.execute(
                _update(sql_model.__table__)
                .where(sql_model.fides_key == resource_dict["fides_key"])
                .values(resource_dict)
            )
        except SQLAlchemyError as e:
            log.exception(f"Failed to update resource with error: '{e}'")
            sa_error = errors.QueryError()
            raise sa_error

        return await get_resource(sql_model, resource_dict["fides_key"], async_session)


async def upsert_resources(
    sql_model: Type[T], resource_dicts: List[Dict], async_session: AsyncSession
) -> Tuple[int, int]:
    """
    Insert new resources into the database. If a resource already exists,
    update it by it's fides_key.

    Returns a Tuple containing the counts of inserted and updated rows.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """

    with log.contextualize(
        sql_model=sql_model.__name__,
        fides_keys=[resource["fides_key"] for resource in resource_dicts],
    ):
        try:
            log.debug("Upserting resources")
            insert_stmt = (
                _insert(sql_model.__table__)
                .values(resource_dicts)
                .returning(
                    (column("xmax") == 0),  # Row was inserted
                    (column("xmax") != 0),  # Row was updated
                )
            )

            excluded = dict(insert_stmt.excluded.items())  # type: ignore[attr-defined]
            excluded.pop("id", None)  # If updating, don't update the "id"

            result = await async_session.execute(
                insert_stmt.on_conflict_do_update(
                    index_elements=["fides_key"],
                    set_=excluded,
                )
            )

            inserts, updates = 0, 0
            for xmax in result:
                inserts += 1 if xmax[0] else 0
                updates += 1 if xmax[1] else 0

            return (inserts, updates)

        except SQLAlchemyError as e:
            log.exception(f"Failed to upsert resources with error: '{e}'")
            sa_error = errors.QueryError()
            raise sa_error


async def delete_resource(
    sql_model: Type[T], fides_key: str, async_session: AsyncSession
) -> T:
    """
    Delete a resource by its fides_key.

    If the resource has child keys referring to it, also delete those.

    This version does NOT manually manage transactions - transaction management
    is left to the calling code.
    """

    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        sql_resource = await get_resource(sql_model, fides_key, async_session)

        try:
            # Automatically delete related resources if they are CTL objects
            if hasattr(sql_model, "parent_key"):
                log.debug("Deleting resource and its children")
                query = (
                    _delete(sql_model.__table__)
                    .where(
                        or_(
                            sql_model.fides_key == fides_key,
                            sql_model.fides_key.like(f"{fides_key}.%"),
                        )
                    )
                    .execution_options(synchronize_session=False)
                )
            else:
                log.debug("Deleting resource")
                query = _delete(sql_model.__table__).where(
                    sql_model.fides_key == fides_key
                )
            await async_session.execute(query)
        except IntegrityError as err:
            raw_error_text: str = err.orig.args[0]

            if "violates foreign key constraint" in raw_error_text:
                error_message = "Failed to delete resource! Foreign key constraint found, try deleting related resources first."
            else:
                error_message = "Failed to delete resource!"

            log.bind(error="SQL Query integrity error!").error(raw_error_text)
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_message,
            )
        except SQLAlchemyError as e:
            log.exception(f"Failed to delete resource with error: '{e}'")
            sa_error = errors.QueryError()
            raise sa_error

        return sql_resource
