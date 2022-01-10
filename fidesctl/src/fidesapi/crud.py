"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""
# pylint: disable=redefined-outer-name,cell-var-from-loop

from typing import Dict, List

from fastapi import APIRouter, status
from loguru import logger as log
from sqlalchemy import update as _update, delete as _delete
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import Insert as _insert
from sqlalchemy.exc import SQLAlchemyError

from fidesapi import errors
from fidesapi.database.session import async_session
from fidesapi.sql_models import SqlAlchemyBase, sql_model_map
from fideslang import model_map


def get_resource_type(router: APIRouter) -> str:
    "Extracts the name of the resource type from the prefix."
    return router.prefix[1:]


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
            log.debug("Resource not found. Inserting.")
        else:
            error = errors.AlreadyExistsError(
                sql_model.__name__, resource_dict["fides_key"]
            )
            log.bind(error=error.detail["error"]).error("Failed to insert resource")
            raise error

        async with async_session() as session:
            try:
                log.debug("Creating resource")
                query = _insert(sql_model).values(resource_dict)
                await session.execute(query)
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error("Failed to create resource")
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
                await session.commit()
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
            try:
                log.debug("Fetching resources")
                query = select(sql_model)
                result = await session.execute(query)
                sql_resources = result.scalars().all()
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error("Failed to fetch resources")
                raise error

        return sql_resources


async def update_resource(sql_model: SqlAlchemyBase, resource_dict: Dict) -> Dict:
    """Update a resource in the database by its fides_key."""

    with log.contextualize(
        sql_model=sql_model.__name__, fides_key=resource_dict["fides_key"]
    ):
        await get_resource(sql_model, resource_dict["fides_key"])
        async with async_session() as session:
            try:
                log.debug("Updating resource")
                await session.execute(
                    _update(sql_model)
                    .where(sql_model.fides_key == resource_dict["fides_key"])
                    .values(resource_dict)
                )
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error("Failed to update resource")
                raise error

        return await get_resource(sql_model, resource_dict["fides_key"])


async def upsert_resources(
    sql_model: SqlAlchemyBase, resource_dicts: List[Dict]
) -> None:
    """
    Insert new resources into the database. If a resource already exists,
    update it by it's fides_key.
    """

    with log.contextualize(
        sql_model=sql_model.__name__,
        fides_keys=[resource["fides_key"] for resource in resource_dicts],
    ):
        async with async_session() as session:
            try:
                log.debug("Upserting resources")
                insert_stmt = _insert(sql_model).values(resource_dicts)
                await session.execute(
                    insert_stmt.on_conflict_do_update(
                        index_elements=["fides_key"],
                        set_=insert_stmt.excluded,
                    )
                )
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
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
            try:
                log.debug("Deleting resource")
                query = _delete(sql_model).where(sql_model.fides_key == fides_key)
                print(query)
                await session.execute(query)
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                error = errors.QueryError()
                log.bind(error=error.detail["error"]).error("Failed to delete resource")
                raise error

        return sql_resource


# CRUD Endpoints
routers = []
for resource_type, resource_model in model_map.items():
    # Programmatically define routers for each resource type
    router = APIRouter(
        tags=[resource_model.__name__],
        prefix=f"/{resource_type}",
    )

    @router.post(
        "/", response_model=resource_model, status_code=status.HTTP_201_CREATED
    )
    async def create(
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """Create a resource."""
        sql_model = sql_model_map[resource_type]
        return await create_resource(sql_model, resource.dict())

    @router.get("/", response_model=List[resource_model], name="List")
    async def ls(  # pylint: disable=invalid-name
        resource_type: str = get_resource_type(router),
    ) -> List:
        """Get a list of all of the resources of this type."""
        sql_model = sql_model_map[resource_type]
        return await list_resource(sql_model)

    @router.get("/{fides_key}", response_model=resource_model)
    async def get(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Get a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        return await get_resource(sql_model, fides_key)

    @router.put("/", response_model=resource_model)
    async def update(
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """Update a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        return await update_resource(sql_model, resource.dict())

    @router.delete("/{fides_key}")
    async def delete(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Delete a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        deleted_resource = await delete_resource(sql_model, fides_key)
        # Convert the resource to a dict explicitly for the response
        deleted_resource_dict = (
            model_map[resource_type].from_orm(deleted_resource).dict()
        )
        return {
            "message": "resource deleted",
            "resource": deleted_resource_dict,
        }

    routers += [router]
