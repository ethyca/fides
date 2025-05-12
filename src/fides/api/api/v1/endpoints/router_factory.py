# type: ignore
"""
Contains all of the factory functions to generate generic CRUD endpoints.

Mostly used for `ctl`-related objects.
"""
from typing import Dict, List

from fastapi import Depends, Response, Security, status
from fideslang import FidesModelType
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.db.crud import (
    create_resource,
    delete_resource,
    get_resource_with_custom_fields,
    list_resource,
    update_resource,
    upsert_resources,
)
from fides.api.db.ctl_session import get_async_db
from fides.api.models.sql_models import ModelWithDefaultField, sql_model_map
from fides.api.oauth.utils import verify_oauth_client_prod
from fides.api.util import errors
from fides.api.util.api_router import APIRouter
from fides.api.util.endpoint_utils import (
    API_PREFIX,
    CLI_SCOPE_PREFIX_MAPPING,
    forbid_if_default,
    forbid_if_editing_any_is_default,
    forbid_if_editing_is_default,
)
from fides.common.api.scope_registry import CREATE, DELETE, READ, UPDATE


def generic_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """
    Compose all of the individual route factories into a single coherent Router.
    """

    object_router = APIRouter()

    create_router = create_router_factory(
        fides_model=fides_model, model_type=model_type
    )
    list_router = list_router_factory(fides_model=fides_model, model_type=model_type)
    get_router = get_router_factory(fides_model=fides_model, model_type=model_type)
    delete_router = delete_router_factory(
        fides_model=fides_model, model_type=model_type
    )
    update_router = update_router_factory(
        fides_model=fides_model, model_type=model_type
    )
    upsert_router = upsert_router_factory(
        fides_model=fides_model, model_type=model_type
    )

    object_router.include_router(create_router)
    object_router.include_router(list_router)
    object_router.include_router(get_router)
    object_router.include_router(delete_router)
    object_router.include_router(update_router)
    object_router.include_router(upsert_router)

    return object_router


def create_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """Return a configured version of a generic 'Create' route."""

    router = APIRouter(prefix=f"{API_PREFIX}/{model_type}", tags=[fides_model.__name__])

    @router.post(
        name="Create",
        path="/",
        response_model=fides_model,
        status_code=status.HTTP_201_CREATED,
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{CREATE}"],
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
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """
        Create a resource.

        Payloads with an is_default field can only be set to False,
        will return a `403 Forbidden`.
        """
        sql_model = sql_model_map[model_type]
        if isinstance(resource, ModelWithDefaultField) and resource.is_default:
            raise errors.ForbiddenIsDefaultTaxonomyError(
                model_type, resource.fides_key, action="create"
            )

        return await create_resource(sql_model, resource.model_dump(mode="json"), db)

    return router


def list_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """Return a configured version of a generic 'List' router."""

    router = APIRouter(prefix=f"{API_PREFIX}/{model_type}", tags=[fides_model.__name__])

    @router.get(
        path="/",
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{READ}"],
            )
        ],
        response_model=List[fides_model],
        name="List",
    )
    async def ls(  # pylint: disable=invalid-name
        db: AsyncSession = Depends(get_async_db),
    ) -> List:
        """Get a list of all of the resources of this type."""
        sql_model = sql_model_map[model_type]
        return await list_resource(sql_model, db)

    return router


def get_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """Return a configured version of a generic 'Get' endpoint."""

    router = APIRouter(prefix=f"{API_PREFIX}/{model_type}", tags=[fides_model.__name__])

    @router.get(
        path="/{fides_key}",
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{READ}"],
            )
        ],
        response_model=fides_model,
    )
    async def get(
        fides_key: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """Get a resource by its fides_key."""
        sql_model = sql_model_map[model_type]
        return await get_resource_with_custom_fields(sql_model, fides_key, db)

    return router


def update_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """Return a configured version of a generic 'Update' route."""

    router = APIRouter(prefix=f"{API_PREFIX}/{model_type}", tags=[fides_model.__name__])

    @router.put(
        path="/",
        response_model=fides_model,
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{UPDATE}"],
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
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """
        Update a resource by its fides_key.

        The `is_default` field cannot be updated and will respond
        with a `403 Forbidden` if attempted.
        """
        sql_model = sql_model_map[model_type]
        await forbid_if_editing_is_default(sql_model, resource.fides_key, resource, db)
        return await update_resource(sql_model, resource.model_dump(mode="json"), db)

    return router


def upsert_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """Return a configured version of a generic 'Upsert' endpoint."""

    router = APIRouter(prefix=f"{API_PREFIX}/{model_type}", tags=[fides_model.__name__])

    @router.post(
        path="/upsert",
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[
                    f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{CREATE}",
                    f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{UPDATE}",
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

        sql_model = sql_model_map[model_type]
        resource_dicts = [resource.model_dump(mode="json") for resource in resources]
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

    return router


def delete_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """Return a configured version of a generic 'Delete' route."""

    router = APIRouter(prefix=f"{API_PREFIX}/{model_type}", tags=[fides_model.__name__])

    @router.delete(
        path="/{fides_key}",
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{DELETE}"],
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
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """
        Delete a resource by its fides_key.

        Resources that have `is_default=True` cannot be deleted and will respond
        with a `403 Forbidden`.
        """
        sql_model = sql_model_map[model_type]
        await forbid_if_default(sql_model, fides_key, db)
        deleted_resource = await delete_resource(sql_model, fides_key, db)
        # Convert the resource to a dict explicitly for the response
        deleted_resource_dict = fides_model.model_validate(deleted_resource).model_dump(
            mode="json"
        )
        return {
            "message": "resource deleted",
            "resource": deleted_resource_dict,
        }

    return router
