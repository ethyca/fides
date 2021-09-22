"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""
# pylint: disable=redefined-outer-name,cell-var-from-loop

from typing import List, Dict

from fastapi import APIRouter, status
from sqlalchemy import update as _update

from fidesapi import db_session
from fidesapi.sql_models import sql_model_map
from fideslang import model_map


def get_resource_type(router: APIRouter) -> str:
    "Extracts the name of the resource type from the prefix."
    return router.prefix[1:]


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
        session = db_session.create_session()
        try:
            sql_resource = sql_model_map[resource_type](**resource.dict())
            session.add(sql_resource)
            session.commit()
            return sql_resource
        finally:
            session.close()

    @router.get("/", response_model=List[resource_model], name="List")
    async def ls(  # pylint: disable=invalid-name
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """Get a list of all of the resources of this type."""
        session = db_session.create_session()
        sql_model = sql_model_map[resource_type]
        try:
            sql_resource = session.query(sql_model).all()
            return sql_resource
        finally:
            session.close()

    @router.get("/{fides_key}", response_model=resource_model)
    async def get(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Get a resource by its fides_key."""
        session = db_session.create_session()
        sql_model = sql_model_map[resource_type]
        try:
            sql_resource = (
                session.query(sql_model)
                .filter(sql_model.fides_key == fides_key)
                .first()
            )
            return sql_resource
        finally:
            session.close()

    @router.post("/{fides_key}", response_model=resource_model)
    async def update(
        fides_key: str,
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """Update a resource by its fides_key."""
        session = db_session.create_session()
        sql_model = sql_model_map[resource_type]

        try:
            session.execute(
                _update(sql_model)
                .where(sql_model.fides_key == fides_key)
                .values(resource.dict())
            )
            session.commit()
            result_sql_resource = (
                session.query(sql_model)
                .filter(sql_model.fides_key == fides_key)
                .first()
            )
            if not result_sql_resource:
                return {
                    "error": {"message": f"{fides_key} is not an existing fides_key!"}
                }
            return result_sql_resource
        finally:
            session.close()

    @router.delete("/{fides_key}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """Delete a resource by its fides_key."""
        session = db_session.create_session()
        sql_model = sql_model_map[resource_type]

        try:
            result_sql_resource = (
                session.query(sql_model)
                .filter(sql_model.fides_key == fides_key)
                .first()
            )
            if not result_sql_resource:
                return {
                    "error": {"message": f"{fides_key} is not an existing fides_key!"}
                }
            session.delete(result_sql_resource)
            session.commit()
        finally:
            session.close()
        return {}

    routers += [router]
