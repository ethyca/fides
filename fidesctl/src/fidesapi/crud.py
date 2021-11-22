"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""
# pylint: disable=redefined-outer-name,cell-var-from-loop

from typing import List, Dict

from fastapi import APIRouter, status
from sqlalchemy import update as _update
from sqlalchemy.dialects.postgresql import Insert as _insert
from sqlalchemy.exc import SQLAlchemyError

from fidesapi import db_session, errors
from fidesapi.sql_models import sql_model_map, SqlAlchemyBase
from fideslang import model_map


def get_resource_type(router: APIRouter) -> str:
    "Extracts the name of the resource type from the prefix."
    return router.prefix[1:]


# CRUD Functions
def create_resource(sql_model: SqlAlchemyBase, sql_resource: SqlAlchemyBase) -> Dict:
    """Create a resource in the database."""
    try:
        get_resource(sql_model, sql_resource.fides_key)
    except errors.NotFoundError:
        pass
    else:
        raise errors.AlreadyExistsError(sql_model.__name__, sql_resource.fides_key)

    session = db_session.create_session()
    try:
        session.add(sql_resource)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise errors.QueryError()
    finally:
        session.close()

    return get_resource(sql_model, sql_resource.fides_key)


def get_resource(sql_model: SqlAlchemyBase, fides_key: str) -> Dict:
    """
    Get a resource from the databse by its FidesKey.
    """
    session = db_session.create_session()
    try:
        sql_resource = (
            session.query(sql_model)
            .filter(sql_model.fides_key == fides_key)
            .limit(1)
            .first()
        )
    except SQLAlchemyError:
        session.rollback()
        raise errors.QueryError()
    finally:
        session.close()

    if sql_resource is None:
        raise errors.NotFoundError(sql_model.__name__, fides_key)

    return sql_resource


def list_resource(sql_model: SqlAlchemyBase) -> List:
    """
    Get a list of all of the resources of this type from the database.
    """
    session = db_session.create_session()
    try:
        sql_resource = session.query(sql_model).all()
    except SQLAlchemyError:
        session.rollback()
        raise errors.QueryError()
    finally:
        session.close()

    return sql_resource


def update_resource(
    sql_model: SqlAlchemyBase, resource_dict: Dict, fides_key: str
) -> Dict:
    """Update a resource in the database by its fides_key."""
    get_resource(sql_model, fides_key)
    session = db_session.create_session()
    try:
        session.execute(
            _update(sql_model)
            .where(sql_model.fides_key == fides_key)
            .values(resource_dict)
        )
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise errors.QueryError()
    finally:
        session.close()

    return get_resource(sql_model, resource_dict.get("fides_key"))


def upsert_resources(sql_model: SqlAlchemyBase, resource_dicts: List[Dict]) -> None:
    """
    Insert new resources into the database. If a resource already exists,
    update it by it's fides_key.
    """
    session = db_session.create_session()
    try:
        insert_stmt = _insert(sql_model).values(resource_dicts)
        session.execute(
            insert_stmt.on_conflict_do_update(
                index_elements=["fides_key"],
                set_=insert_stmt.excluded,
            )
        )
        session.commit()
    except SQLAlchemyError:
        session.rollback()
    finally:
        session.close()


def delete_resource(sql_model: SqlAlchemyBase, fides_key: str) -> Dict:
    """Delete a resource by its fides_key."""
    sql_resource = get_resource(sql_model, fides_key)
    session = db_session.create_session()
    try:
        session.delete(sql_resource)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise errors.QueryError()
    finally:
        session.close()

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
        sql_resource = sql_model(**resource.dict())
        return create_resource(sql_model, sql_resource)

    @router.get("/", response_model=List[resource_model], name="List")
    async def ls(  # pylint: disable=invalid-name
        resource_type: str = get_resource_type(router),
    ) -> List:
        """Get a list of all of the resources of this type."""
        sql_model = sql_model_map[resource_type]
        return list_resource(sql_model)

    @router.get("/{fides_key}", response_model=resource_model)
    async def get(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Get a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        return get_resource(sql_model, fides_key)

    @router.post("/{fides_key}", response_model=resource_model)
    async def update(
        fides_key: str,
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """Update a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        resource_dict = resource.dict()
        return update_resource(sql_model, resource_dict, fides_key)

    @router.delete("/{fides_key}")
    async def delete(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Delete a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        query_result = delete_resource(sql_model, fides_key)
        return {
            "message": "resource deleted",
            "resource": query_result,
        }

    routers += [router]
