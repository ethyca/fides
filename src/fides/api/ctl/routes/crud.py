# type: ignore
# pylint: disable=redefined-outer-name,cell-var-from-loop

"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""

from typing import Dict, List

from fastapi import Depends, HTTPException, Response, Security, status
from fideslang import Dataset, FidesModel, model_map
from fideslang.validation import FidesKey
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.ctl.database.crud import (
    create_resource,
    delete_resource,
    get_resource,
    list_resource,
    update_resource,
    upsert_resources,
)
from fides.api.ctl.database.session import get_async_db
from fides.api.ctl.routes.util import (
    API_PREFIX,
    forbid_if_default,
    forbid_if_editing_any_is_default,
    forbid_if_editing_is_default,
    get_resource_type,
)
from fides.api.ctl.sql_models import (
    DataCategory,
    models_with_default_field,
    sql_model_map,
)
from fides.api.ctl.utils import errors
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ops.api.v1 import scope_registry
from fides.api.ops.schemas.dataset import validate_data_categories_against_db
from fides.api.ops.util.oauth_util import verify_oauth_client_cli


async def get_data_categories_from_db(async_session: AsyncSession) -> List[FidesKey]:
    """Similar method to one on the ops side except this uses an async session to retrieve data categories"""
    resources = await list_resource(DataCategory, async_session)
    data_categories = [res.fides_key for res in resources]
    return data_categories


async def validate_data_categories(
    resource: FidesModel, async_session: AsyncSession
) -> None:
    """Validate data categories defined on Datasets against data categories in the db"""
    if not isinstance(resource, Dataset):
        return

    try:
        defined_data_categories: List[FidesKey] = await get_data_categories_from_db(
            async_session
        )
        validate_data_categories_against_db(resource, defined_data_categories)
    except PydanticValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )


# CRUD Endpoints
routers: List[APIRouter] = []
for model_type, fides_model in model_map.items():
    # Programmatically define routers for each resource type
    router = APIRouter(
        tags=[fides_model.__name__],
        prefix=f"{API_PREFIX}/{model_type}",
    )

    @router.post(
        "/",
        response_model=fides_model,
        status_code=status.HTTP_201_CREATED,
        dependencies=[
            Security(
                verify_oauth_client_cli, scopes=[scope_registry.CLI_OBJECTS_CREATE]
            )
        ],
        responses={
            status.HTTP_403_FORBIDDEN: {
                "content": {
                    "application/json": {
                        "example": {
                            "detail": {
                                "error": "user does not have permission to modify this resource",
                                "resource_type": model_type,
                                "fides_key": "example.key",
                            }
                        }
                    }
                }
            },
        },
    )
    async def create(
        resource: fides_model,
        resource_type: str = get_resource_type(router),
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """
        Create a resource.

        Payloads with an is_default field can only be set to False,
        will return a `403 Forbidden`.
        """
        sql_model = sql_model_map[resource_type]
        await validate_data_categories(resource, db)
        if sql_model in models_with_default_field and resource.is_default:
            raise errors.ForbiddenError(resource_type, resource.fides_key)
        return await create_resource(sql_model, resource.dict(), db)

    @router.get(
        "/",
        dependencies=[
            Security(verify_oauth_client_cli, scopes=[scope_registry.CLI_OBJECTS_READ])
        ],
        response_model=List[fides_model],
        name="List",
    )
    async def ls(  # pylint: disable=invalid-name
        resource_type: str = get_resource_type(router),
        db: AsyncSession = Depends(get_async_db),
    ) -> List:
        """Get a list of all of the resources of this type."""
        sql_model = sql_model_map[resource_type]
        return await list_resource(sql_model, db)

    @router.get(
        "/{fides_key}",
        dependencies=[
            Security(verify_oauth_client_cli, scopes=[scope_registry.CLI_OBJECTS_READ])
        ],
        response_model=fides_model,
    )
    async def get(
        fides_key: str,
        resource_type: str = get_resource_type(router),
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """Get a resource by its fides_key."""
        sql_model = sql_model_map[resource_type]
        return await get_resource(sql_model, fides_key, db)

    @router.put(
        "/",
        response_model=fides_model,
        dependencies=[
            Security(
                verify_oauth_client_cli, scopes=[scope_registry.CLI_OBJECTS_UPDATE]
            )
        ],
        responses={
            status.HTTP_403_FORBIDDEN: {
                "content": {
                    "application/json": {
                        "example": {
                            "detail": {
                                "error": "user does not have permission to modify this resource",
                                "resource_type": model_type,
                                "fides_key": "example.key",
                            }
                        }
                    }
                }
            },
        },
    )
    async def update(
        resource: fides_model,
        resource_type: str = get_resource_type(router),
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """
        Update a resource by its fides_key.

        The `is_default` field cannot be updated and will respond
        with a `403 Forbidden` if attempted.
        """
        sql_model = sql_model_map[resource_type]
        await validate_data_categories(resource, db)
        await forbid_if_editing_is_default(sql_model, resource.fides_key, resource, db)
        return await update_resource(sql_model, resource.dict(), db)

    @router.post(
        "/upsert",
        dependencies=[
            Security(
                verify_oauth_client_cli,
                scopes=[
                    scope_registry.CLI_OBJECTS_CREATE,
                    scope_registry.CLI_OBJECTS_UPDATE,
                ],
            )
        ],
        responses={
            status.HTTP_200_OK: {
                "content": {
                    "application/json": {
                        "example": {
                            "message": f"Upserted 3 {model_type}(s)",
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
                            "message": f"Upserted 3 {model_type}(s)",
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
        resources: List[fides_model],
        response: Response,
        resource_type: str = get_resource_type(router),
        db: AsyncSession = Depends(get_async_db),
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
        resource_dicts = [resource.dict() for resource in resources]
        for resource in resources:
            await validate_data_categories(resource, db)

        await forbid_if_editing_any_is_default(sql_model, resource_dicts, db)
        result = await upsert_resources(sql_model, resource_dicts, db)
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
        dependencies=[
            Security(
                verify_oauth_client_cli, scopes=[scope_registry.CLI_OBJECTS_DELETE]
            )
        ],
        responses={
            status.HTTP_403_FORBIDDEN: {
                "content": {
                    "application/json": {
                        "example": {
                            "detail": {
                                "error": "user does not have permission to modify this resource",
                                "resource_type": model_type,
                                "fides_key": "example.key",
                            }
                        }
                    }
                }
            },
        },
    )
    async def delete(
        fides_key: str,
        resource_type: str = get_resource_type(router),
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """
        Delete a resource by its fides_key.

        Resources that have `is_default=True` cannot be deleted and will respond
        with a `403 Forbidden`.
        """
        sql_model = sql_model_map[resource_type]
        await forbid_if_default(sql_model, fides_key, db)
        deleted_resource = await delete_resource(sql_model, fides_key, db)
        # Convert the resource to a dict explicitly for the response
        deleted_resource_dict = (
            model_map[resource_type].from_orm(deleted_resource).dict()
        )
        return {
            "message": "resource deleted",
            "resource": deleted_resource_dict,
        }

    routers += [router]
