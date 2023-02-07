"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""
from typing import Dict, List, Optional, Tuple

from loguru import logger as log
from sqlalchemy import column
from sqlalchemy import delete as _delete
from sqlalchemy import or_
from sqlalchemy import update as _update
from sqlalchemy.dialects.postgresql import Insert as _insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fides.api.ctl.sql_models import CustomField, CustomFieldDefinition, SystemModel
from fides.api.ctl.utils import errors
from fides.lib.db.base import Base  # type: ignore[attr-defined]


# CRUD Functions
async def create_resource(
    sql_model: Base, resource_dict: Dict, async_session: AsyncSession
) -> Base:
    """Create a resource in the database."""
    with log.contextualize(
        sql_model=sql_model.__name__, fides_key=resource_dict["fides_key"]
    ):
        try:
            await get_resource(sql_model, resource_dict["fides_key"], async_session)
        except errors.NotFoundError:
            pass
        else:
            already_exists_error = errors.AlreadyExistsError(
                sql_model.__name__, resource_dict["fides_key"]
            )
            log.bind(error=already_exists_error.detail["error"]).error(  # type: ignore[index]
                "Failed to insert resource"
            )
            raise already_exists_error

        async with async_session.begin():
            try:
                log.debug("Creating resource")
                query = _insert(sql_model).values(resource_dict)
                await async_session.execute(query)
            except SQLAlchemyError:
                sa_error = errors.QueryError()
                log.bind(error=sa_error.detail["error"]).error(  # type: ignore[index]
                    "Failed to create resource"
                )
                raise sa_error

        return await get_resource(sql_model, resource_dict["fides_key"], async_session)


async def get_resource(
    sql_model: Base, fides_key: str, async_session: AsyncSession
) -> Base:
    """
    Get a resource from the databse by its FidesKey.

    Returns a SQLAlchemy model of that resource.
    """
    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        async with async_session.begin():
            try:
                log.debug("Fetching resource")
                query = select(sql_model).where(sql_model.fides_key == fides_key)
                result = await async_session.execute(query)
            except SQLAlchemyError:
                sa_error = errors.QueryError()
                log.bind(error=sa_error.detail["error"]).error(  # type: ignore[index]
                    "Failed to fetch resource"
                )
                raise sa_error

            sql_resource = result.scalars().first()
            if sql_resource is None:
                not_found_error = errors.NotFoundError(sql_model.__name__, fides_key)
                log.bind(error=not_found_error.detail["error"]).error("Resource not found")  # type: ignore[index]
                raise not_found_error

            return sql_resource


async def get_resource_with_custom_field(
    sql_model: Base, fides_key: str, async_session: AsyncSession
) -> List[SystemModel]:
    """Get a resource from the databse by its FidesKey including it's custom fields.

    Returns a SQLAlchemy model of that resource.
    """
    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        async with async_session.begin():
            try:
                log.debug("Fetching resource including custom fields")
                query = (
                    select(sql_model, CustomFieldDefinition.name, CustomField.value)
                    .join(
                        sql_model,
                        CustomField.resource_id == sql_model.fides_key,
                        isouter=True,
                    )
                    .join(
                        CustomField,
                        CustomField.custom_field_definition_id
                        == CustomFieldDefinition.id,
                    )
                    .where(sql_model.fides_key == fides_key)
                )
                print(str(query))
                result = await async_session.execute(query)
            except SQLAlchemyError:
                sa_error = errors.QueryError()
                log.bind(error=sa_error.detail["error"]).error(  # type: ignore[index]
                    "Failed to fetch custom fields"
                )
                raise sa_error

            sql_resource = result.mappings().all()

            if not sql_resource:
                not_found_error = errors.NotFoundError(sql_model.__name__, fides_key)
                log.bind(error=not_found_error.detail["error"]).error("Resource not found")  # type: ignore[index]
                raise not_found_error

            processed = []
            for resource in sql_resource:
                combined = resource["System"].__dict__
                combined["value"] = resource["value"]
                processed.append(SystemModel(**combined))

            return processed


async def list_resource(sql_model: Base, async_session: AsyncSession) -> List[Base]:
    """
    Get a list of all of the resources of this type from the database.

    Returns a list of SQLAlchemy models of that resource type.
    """
    with log.contextualize(sql_model=sql_model.__name__):
        async with async_session.begin():
            try:
                log.debug("Fetching resources")
                query = select(sql_model)
                result = await async_session.execute(query)
                sql_resources = result.scalars().all()
            except SQLAlchemyError:
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error(  # type: ignore[index]
                    "Failed to fetch resources"
                )
                raise error

            return sql_resources


async def update_resource(
    sql_model: Base, resource_dict: Dict, async_session: AsyncSession
) -> Dict:
    """Update a resource in the database by its fides_key."""

    with log.contextualize(
        sql_model=sql_model.__name__, fides_key=resource_dict["fides_key"]
    ):
        await get_resource(sql_model, resource_dict["fides_key"], async_session)

        async with async_session.begin():
            try:
                log.debug("Updating resource")
                await async_session.execute(
                    _update(sql_model)
                    .where(sql_model.fides_key == resource_dict["fides_key"])
                    .values(resource_dict)
                )
            except SQLAlchemyError:
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error(  # type: ignore[index]
                    "Failed to update resource"
                )
                raise error

        return await get_resource(sql_model, resource_dict["fides_key"], async_session)


async def upsert_resources(
    sql_model: Base, resource_dicts: List[Dict], async_session: AsyncSession
) -> Tuple[int, int]:
    """
    Insert new resources into the database. If a resource already exists,
    update it by it's fides_key.

    Returns a Tuple containing the counts of inserted and updated rows.
    """

    with log.contextualize(
        sql_model=sql_model.__name__,
        fides_keys=[resource["fides_key"] for resource in resource_dicts],
    ):

        async with async_session.begin():
            try:
                log.debug("Upserting resources")
                insert_stmt = (
                    _insert(sql_model)
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

            except SQLAlchemyError:
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error(  # type: ignore[index]
                    "Failed to upsert resources"
                )
                raise error


async def delete_resource(
    sql_model: Base, fides_key: str, async_session: AsyncSession
) -> Base:
    """
    Delete a resource by its fides_key.

    If the resource has child keys referring to it, also delete those.
    """

    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        sql_resource = await get_resource(sql_model, fides_key, async_session)

        async with async_session.begin():
            try:
                if hasattr(sql_model, "parent_key"):
                    log.debug("Deleting resource and its children")
                    query = (
                        _delete(sql_model)
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
                    query = _delete(sql_model).where(sql_model.fides_key == fides_key)
                print(query)
                await async_session.execute(query)
            except SQLAlchemyError:
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error(  # type: ignore[index]
                    "Failed to delete resource"
                )
                raise error

        return sql_resource
