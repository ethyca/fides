from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import InvalidRequestError

from fidesapi import db_session
from fideslang import model_map
from fideslang.validation import FidesValidationError
from fidesapi.sql_models import sql_model_map


def get_resource_type(router: APIRouter):
    return router.prefix[1:]


routers = []
for resource_type, resource_model in model_map.items():
    router = APIRouter(
        tags=[resource_model.__name__],
        prefix=f"/{resource_type}",
    )

    @router.post("/", response_model=resource_model)
    async def create(
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ):
        """Create a resource."""
        session = db_session.create_session()
        try:
            sql_resource = sql_model_map[resource_type](**resource.dict())
            session.add(sql_resource)
            session.commit()
            return sql_resource
        except FidesValidationError as err:
            raise HTTPException(status_code=404, detail=err)
        except InvalidRequestError as err:
            raise HTTPException(status_code=404, detail=err)
        finally:
            session.close()

    @router.get("/{fides_key}", response_model=resource_model)
    async def get(fides_key: str, resource_type: str = get_resource_type(router)):
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
    async def update(fides_key: str, resource: resource_model):
        """Update a resource by its fides_key."""
        session = db_session.create_session()
        sql_model = sql_model_map[resource_type]

        try:
            sql_resource = (
                session.query(sql_model)
                .filter(sql_model.fides_key == fides_key)
                .first()
            )
            if not sql_resource:
                return {
                    "error": {"message": f"{fides_key} is not an existing fides_key!"}
                }
            session.delete(sql_resource)
            session.commit()
            return {"data": {"message": "True"}}
        finally:
            session.close()

    @router.delete("/{fides_key}")
    async def delete(fides_key: str, resource_type: str = get_resource_type(router)):
        """Delete a resource by its fides_key."""
        session = db_session.create_session()
        sql_model = sql_model_map[resource_type]

        try:
            sql_resource = (
                session.query(sql_model)
                .filter(sql_model.fides_key == fides_key)
                .first()
            )
            if not sql_resource:
                return {
                    "error": {"message": f"{fides_key} is not an existing fides_key!"}
                }
            session.delete(sql_resource)
            session.commit()
            return {"data": {"message": "True"}}
        finally:
            session.close()

    routers += [router]
