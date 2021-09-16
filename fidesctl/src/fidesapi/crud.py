from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fidesapi import db_session
from fideslang import FidesModel, model_map
from fidesapi.sql_models import sql_model_map


routers = []
for resource_type, resource_model in model_map.items():
    router = APIRouter(tags=[resource_type], prefix=f"/{resource_type}")

    @router.post("/", response_model=resource_model)
    async def create(resource_type: str, resource: resource_model):
        """Create a resource."""
        session = db_session.create_session()

        try:
            sql_resource = sql_model_map[resource_type](**resource.dict())
            session.add(sql_resource)
            session.commit()
            return sql_resource
        finally:
            session.close()

    @router.get("/{fides_key}", response_model=resource_model)
    async def get(fides_key: str):
        """Get a resource by its fides_key."""
        return {"data": {"resource_type": resource_type, "fides_key": fides_key}}

    @router.post("/{fides_key}", response_model=resource_model)
    async def update(fides_key: str, resource: resource_model):
        """Update a resource by its fides_key."""

    @router.delete("/{fides_key}")
    async def delete(fides_key: str):
        """Delete a resource by its fides_key."""

    routers += [router]
