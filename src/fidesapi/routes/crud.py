# type: ignore
# pylint: disable=redefined-outer-name,cell-var-from-loop

"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""

from typing import Dict, List

from fastapi import APIRouter, Response, status

from fidesapi.database.crud import (
    create_resource,
    delete_resource,
    get_resource,
    list_resource,
    update_resource,
    upsert_resources,
)
from fidesapi.sql_models import sql_model_map
from fideslang import model_map


def get_resource_type(router: APIRouter) -> str:
    "Extracts the name of the resource type from the prefix."
    return router.prefix[1:]


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

    @router.post(
        "/upsert",
        responses={
            status.HTTP_200_OK: {
                "content": {
                    "application/json": {
                        "example": {
                            "message": f"Upserted 3 {resource_type}(s)",
                            "inserted": 0,
                            "updated": 3,
                        }
                    }
                }
            },
            status.HTTP_201_CREATED: {
                "content": {
                    "application/json": {
                        "example": {
                            "message": f"Upserted 3 {resource_type}(s)",
                            "inserted": 1,
                            "updated": 2,
                        }
                    }
                }
            },
        },
    )
    async def upsert(
        resources: List[Dict],
        response: Response,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """
        For any resource in `resources` that already exists in the database,
        update the resource by its `fides_key`. Otherwise, create a new resource.

        Responds with a `201 Created` if even a single resource in `resources`
        did not previously exist. Otherwise, responds with a `200 OK`.
        """

        sql_model = sql_model_map[resource_type]
        result = await upsert_resources(sql_model, resources)
        response.status_code = (
            status.HTTP_201_CREATED if result[0] > 0 else response.status_code
        )

        return {
            "message": f"Upserted {len(resources)} {sql_model.__name__}(s)",
            "inserted": result[0],
            "updated": result[1],
        }

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
