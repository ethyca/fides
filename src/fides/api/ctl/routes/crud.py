# type: ignore
# pylint: disable=redefined-outer-name,cell-var-from-loop

"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""

from typing import Dict, List

from fastapi import Response, status
from fideslang import model_map

from fides.api.ctl.database.crud import (
    create_resource,
    delete_resource,
    get_resource,
    list_resource,
    update_resource,
    upsert_resources,
)
from fides.api.ctl.routes.util import (
    API_PREFIX,
    forbid_if_default,
    forbid_if_editing_any_is_default,
    forbid_if_editing_is_default,
    get_resource_type,
)
from fides.api.ctl.sql_models import models_with_default_field, sql_model_map
from fides.api.ctl.utils import errors
from fides.api.ctl.utils.api_router import APIRouter

# CRUD Endpoints
routers = []
for resource_type, resource_model in model_map.items():
    # Programmatically define routers for each resource type
    router = APIRouter(
        tags=[resource_model.__name__],
        prefix=f"{API_PREFIX}/{resource_type}",
    )

    @router.post(
        "/",
        response_model=resource_model,
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_403_FORBIDDEN: {
                "content": {
                    "application/json": {
                        "example": {
                            "detail": {
                                "error": "user does not have permission to modify this resource",
                                "resource_type": resource_type,
                                "fides_key": "example.key",
                            }
                        }
                    }
                }
            },
        },
    )
    async def create(
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """
        Create a resource.

        Payloads with an is_default field can only be set to False,
        will return a `403 Forbidden`.
        """
        sql_model = sql_model_map[resource_type]
        if sql_model in models_with_default_field and resource.is_default:
            raise errors.ForbiddenError(resource_type, resource.fides_key)
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

    @router.put(
        "/",
        response_model=resource_model,
        responses={
            status.HTTP_403_FORBIDDEN: {
                "content": {
                    "application/json": {
                        "example": {
                            "detail": {
                                "error": "user does not have permission to modify this resource",
                                "resource_type": resource_type,
                                "fides_key": "example.key",
                            }
                        }
                    }
                }
            },
        },
    )
    async def update(
        resource: resource_model,
        resource_type: str = get_resource_type(router),
    ) -> Dict:
        """
        Update a resource by its fides_key.

        The `is_default` field cannot be updated and will respond
        with a `403 Forbidden` if attempted.
        """
        sql_model = sql_model_map[resource_type]
        await forbid_if_editing_is_default(sql_model, resource.fides_key, resource)
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
            status.HTTP_403_FORBIDDEN: {
                "content": {
                    "application/json": {
                        "example": {
                            "detail": {
                                "error": "user does not have permission to modify this resource",
                                "resource_type": "DataCategory",
                                "fides_key": "example.key",
                            }
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

        The `is_default` field cannot be updated and will respond
        with a `403 Forbidden` if attempted.
        """

        sql_model = sql_model_map[resource_type]
        await forbid_if_editing_any_is_default(sql_model, resources)
        result = await upsert_resources(sql_model, resources)
        response.status_code = (
            status.HTTP_201_CREATED if result[0] > 0 else response.status_code
        )

        return {
            "message": f"Upserted {len(resources)} {sql_model.__name__}(s)",
            "inserted": result[0],
            "updated": result[1],
        }

    @router.delete(
        "/{fides_key}",
        responses={
            status.HTTP_403_FORBIDDEN: {
                "content": {
                    "application/json": {
                        "example": {
                            "detail": {
                                "error": "user does not have permission to modify this resource",
                                "resource_type": resource_type,
                                "fides_key": "example.key",
                            }
                        }
                    }
                }
            },
        },
    )
    async def delete(
        fides_key: str, resource_type: str = get_resource_type(router)
    ) -> Dict:
        """
        Delete a resource by its fides_key.

        Resources that have `is_default=True` cannot be deleted and will respond
        with a `403 Forbidden`.
        """
        sql_model = sql_model_map[resource_type]
        await forbid_if_default(sql_model, fides_key)
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
