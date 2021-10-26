"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""
# pylint: disable=redefined-outer-name,cell-var-from-loop

from typing import List, Dict

from fastapi import APIRouter, status
from sqlalchemy import update as _update

from fidesapi import db_session
from fidesapi.sql_models import sql_model_map, SqlAlchemyBase
from fideslang import model_map


def get_resource_type(router: APIRouter) -> str:
    "Extracts the name of the resource type from the prefix."
    return router.prefix[1:]


# CRUD Functions
def create_resource(sql_resource: SqlAlchemyBase) -> None:
    """Create a resource in the database."""
    session = db_session.create_session()
    try:
        session.add(sql_resource)
        session.commit()
    finally:
        session.close()


def get_resource(sql_model: SqlAlchemyBase, fides_key: str) -> Dict:
    """
    Get a resource from the databse by its FidesKey.
    """
    session = db_session.create_session()
    try:
        sql_resource = (
            session.query(sql_model).filter(sql_model.fides_key == fides_key).first()
        )
    finally:
        session.close()
    return sql_resource


def list_resource(sql_model: SqlAlchemyBase) -> List:
    """
    Get a list of all of the resources of this type from the database.
    """
    session = db_session.create_session()
    try:
        sql_resource = session.query(sql_model).all()
    finally:
        session.close()
    return sql_resource


def update_resource(sql_model: SqlAlchemyBase, resource_dict: Dict, fides_key: str):
    """Update a resource in the database by its fides_key."""
    session = db_session.create_session()
    try:
        session.execute(
            _update(sql_model)
            .where(sql_model.fides_key == fides_key)
            .values(resource_dict)
        )
        session.commit()
    finally:
        session.close()

    result_sql_resource = get_resource(sql_model, fides_key)
    if not result_sql_resource:
        return {"error": {"message": f"{fides_key} is not an existing fides_key!"}}

    return result_sql_resource


def delete_resource(sql_model: SqlAlchemyBase, fides_key: str) -> Dict:
    """Delete a resource by its fides_key."""
    result_sql_resource = get_resource(sql_model, fides_key)
    if not result_sql_resource:
        return {"error": {"message": f"{fides_key} is not an existing fides_key!"}}

    session = db_session.create_session()
    try:
        session.delete(result_sql_resource)
        session.commit()
    finally:
        session.close()
    return {}


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
        sql_resource = sql_model_map[resource_type](**resource.dict())
        create_resource(sql_resource)
        return sql_resource

    @router.get("/", response_model=List[resource_model], name="List")
    async def ls(  # pylint: disable=invalid-name
        resource_type: str = get_resource_type(router),
    ) -> List:
        """Get a list of all of the resources of this type."""
        sql_model = sql_model_map[resource_type]
        query_result = list_resource(sql_model)
        return query_result

    @router.get("/{fides_key}", response_model=resource_model)
    async def get(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Get a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        query_result = get_resource(sql_model, fides_key)
        return query_result

    @router.post("/{fides_key}", response_model=resource_model)
    async def update(
        fides_key: str,
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """Update a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        resource_dict = resource.dict()
        query_result = update_resource(sql_model, resource_dict, fides_key)
        return query_result

    @router.delete("/{fides_key}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Delete a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        delete_resource(sql_model, fides_key)
        return {
            "Message": f"Resource with fides_key: {fides_key} deleted successfully!"
        }

    routers += [router]
