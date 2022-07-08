"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""
from typing import Dict, List, Tuple

from loguru import logger as log
from sqlalchemy import column
from sqlalchemy import delete as _delete
from sqlalchemy import update as _update
from sqlalchemy.dialects.postgresql import Insert as _insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from fidesapi.database.session import async_session
from fidesapi.sql_models import SqlAlchemyBase
from fidesapi.utils import errors


# CRUD Functions
async def create_resource(
    sql_model: SqlAlchemyBase,
    resource_dict: Dict,
) -> SqlAlchemyBase:
    """Create a resource in the database."""
    with log.contextualize(
        sql_model=sql_model.__name__, fides_key=resource_dict["fides_key"]
    ):
        try:
            await get_resource(sql_model, resource_dict["fides_key"])
        except errors.NotFoundError:
            pass
        else:
            error = errors.AlreadyExistsError(
                sql_model.__name__, resource_dict["fides_key"]
            )
            log.bind(error=error.detail["error"]).error("Failed to insert resource")
            raise error

        async with async_session() as session:
            async with session.begin():
                try:
                    log.debug("Creating resource")
                    query = _insert(sql_model).values(resource_dict)
                    await session.execute(query)
                except SQLAlchemyError:
                    error = errors.QueryError()
                    log.bind(error=error.detail["error"]).error(
                        "Failed to create resource"
                    )
                    raise error

        return await get_resource(sql_model, resource_dict["fides_key"])


async def get_resource(sql_model: SqlAlchemyBase, fides_key: str) -> SqlAlchemyBase:
    """
    Get a resource from the databse by its FidesKey.

    Returns a SQLAlchemy model of that resource.
    """

    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        async with async_session() as session:
            try:
                log.debug("Fetching resource")
                query = select(sql_model).where(sql_model.fides_key == fides_key)
                result = await session.execute(query)
            except SQLAlchemyError:
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error("Failed to fetch resource")
                raise error

        sql_resource = result.scalars().first()
        if sql_resource is None:
            error = errors.NotFoundError(sql_model.__name__, fides_key)
            log.bind(error=error.detail["error"]).error("Resource not found")
            raise error

        return sql_resource


async def list_resource(sql_model: SqlAlchemyBase) -> List[SqlAlchemyBase]:
    """
    Get a list of all of the resources of this type from the database.

    Returns a list of SQLAlchemy models of that resource type.
    """
    with log.contextualize(sql_model=sql_model.__name__):
        async with async_session() as session:
            async with session.begin():
                try:
                    log.debug("Fetching resources")
                    query = select(sql_model)
                    result = await session.execute(query)
                    sql_resources = result.scalars().all()
                except SQLAlchemyError:
                    error = errors.QueryError()
                    log.bind(error=error.detail["error"]).error(
                        "Failed to fetch resources"
                    )
                    raise error

        return sql_resources


async def update_resource(sql_model: SqlAlchemyBase, resource_dict: Dict) -> Dict:
    """Update a resource in the database by its fides_key."""

    with log.contextualize(
        sql_model=sql_model.__name__, fides_key=resource_dict["fides_key"]
    ):
        await get_resource(sql_model, resource_dict["fides_key"])
        async with async_session() as session:
            async with session.begin():
                try:
                    log.debug("Updating resource")
                    await session.execute(
                        _update(sql_model)
                        .where(sql_model.fides_key == resource_dict["fides_key"])
                        .values(resource_dict)
                    )
                except SQLAlchemyError:
                    error = errors.QueryError()
                    log.bind(error=error.detail["error"]).error(
                        "Failed to update resource"
                    )
                    raise error

        return await get_resource(sql_model, resource_dict["fides_key"])


async def upsert_resources(
    sql_model: SqlAlchemyBase,
    resource_dicts: List[Dict],
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
        async with async_session() as session:
            async with session.begin():
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

                    result = await session.execute(
                        insert_stmt.on_conflict_do_update(
                            index_elements=["fides_key"],
                            set_=insert_stmt.excluded,
                        )
                    )

                    inserts, updates = 0, 0
                    for xmax in result:
                        inserts += 1 if xmax[0] else 0
                        updates += 1 if xmax[1] else 0

                    return (inserts, updates)

                except SQLAlchemyError:
                    error = errors.QueryError()
                    log.bind(error=error.detail["error"]).error(
                        "Failed to upsert resources"
                    )
                    raise error


async def delete_resource(sql_model: SqlAlchemyBase, fides_key: str) -> SqlAlchemyBase:
    """Delete a resource by its fides_key."""

    with log.contextualize(sql_model=sql_model.__name__, fides_key=fides_key):
        sql_resource = await get_resource(sql_model, fides_key)
        async with async_session() as session:
            async with session.begin():
                try:
                    log.debug("Deleting resource")
                    query = _delete(sql_model).where(sql_model.fides_key == fides_key)
                    print(query)
                    await session.execute(query)
                except SQLAlchemyError:
                    error = errors.QueryError()
                    log.bind(error=error.detail["error"]).error(
                        "Failed to delete resource"
                    )
                    raise error

        return sql_resource
