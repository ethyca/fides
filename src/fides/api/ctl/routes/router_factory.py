# type: ignore
"""
Contains all of the factory functions to generate generic CRUD endpoints.

Mostly used for `ctl`-related objects.
"""

from typing import Dict, List

from fastapi import Depends, HTTPException, Response, Security, status
from fastapi.routing import APIRoute
from fideslang import Dataset, FidesModel, FidesModelType, model_map
from fideslang.validation import FidesKey
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.ctl.database.crud import (
    create_resource,
    delete_resource,
    get_resource_with_custom_fields,
    list_resource,
    update_resource,
    upsert_resources,
)
from fides.api.ctl.database.session import get_async_db
from fides.api.ctl.routes.util import (
    API_PREFIX,
    CLI_SCOPE_PREFIX_MAPPING,
    forbid_if_default,
    forbid_if_editing_any_is_default,
    forbid_if_editing_is_default,
)
from fides.api.ctl.sql_models import (
    DataCategory,
    models_with_default_field,
    sql_model_map,
)
from fides.api.ctl.utils import errors
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ops.api.v1.scope_registry import CREATE, DELETE, READ, UPDATE
from fides.api.ops.oauth.utils import verify_oauth_client_prod
from fides.api.ops.schemas.dataset import validate_data_categories_against_db


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


def generic_router_factory(fides_model: FidesModelType, model_type: str) -> APIRouter:
    """
    Compose all of the individual route factories into a single coherent Router.
    """

    create_router = create_route_factory(fides_model=fides_model, model_type=model_type)
    list_router = list_route_factory(fides_model=fides_model, model_type=model_type)
    get_route = get_route_factory(fides_model=fides_model, model_type=model_type)
    delete_route = delete_route_factory(fides_model=fides_model, model_type=model_type)
    update_route = update_route_factory(fides_model=fides_model, model_type=model_type)
    upsert_route = upsert_route_factory(fides_model=fides_model, model_type=model_type)

    router = APIRouter(
        routes=[
            create_router,
            list_router,
            get_route,
            delete_route,
            update_route,
            upsert_route,
        ],
    )
    return router


def create_route_factory(fides_model: FidesModelType, model_type: str) -> APIRoute:
    """Return a configured version of a generic 'Create' route."""

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
        await validate_data_categories(resource, db)
        if sql_model in models_with_default_field and resource.is_default:
            raise errors.ForbiddenError(model_type, resource.fides_key)
        return await create_resource(sql_model, resource.dict(), db)

    route = APIRoute(
        methods=["post"],
        tags=[fides_model.__name__],
        name="Create",
        path=f"{API_PREFIX}/{model_type}/",
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
        endpoint=create,
    )
    return route


def list_route_factory(fides_model: FidesModelType, model_type: str) -> APIRoute:
    """Return a configured version of a generic 'List' router."""

    async def ls(  # pylint: disable=invalid-name
        db: AsyncSession = Depends(get_async_db),
    ) -> List:
        """Get a list of all of the resources of this type."""
        sql_model = sql_model_map[model_type]
        return await list_resource(sql_model, db)

    # Add the API Route to the Router
    route = APIRoute(
        path=f"{API_PREFIX}/{model_type}/",
        tags=[fides_model.__name__],
        methods=["get"],
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{READ}"],
            )
        ],
        response_model=List[fides_model],
        name="List",
        endpoint=ls,
    )
    return route


def get_route_factory(fides_model: FidesModelType, model_type: str) -> APIRoute:
    """Return a configured version of a generic Create endpoint."""

    async def get(
        fides_key: str,
        db: AsyncSession = Depends(get_async_db),
    ) -> Dict:
        """Get a resource by its fides_key."""
        sql_model = sql_model_map[model_type]
        return await get_resource_with_custom_fields(sql_model, fides_key, db)

    route = APIRoute(
        path=f"{API_PREFIX}/{model_type}/" + "{fides_key}",
        methods=["get"],
        tags=[fides_model.__name__],
        dependencies=[
            Security(
                verify_oauth_client_prod,
                scopes=[f"{CLI_SCOPE_PREFIX_MAPPING[model_type]}:{READ}"],
            )
        ],
        response_model=fides_model,
        endpoint=get,
    )

    return route


def update_route_factory(fides_model: FidesModelType, model_type: str) -> APIRoute:
    """Return a configured version of a generic 'Update' route."""

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
        await validate_data_categories(resource, db)
        await forbid_if_editing_is_default(sql_model, resource.fides_key, resource, db)
        return await update_resource(sql_model, resource.dict(), db)

    route = APIRoute(
        path=f"{API_PREFIX}/{model_type}/",
        tags=[fides_model.__name__],
        methods=["put"],
        response_model=fides_model,
        endpoint=update,
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

    return route


def upsert_route_factory(fides_model: FidesModelType, model_type: str) -> APIRoute:
    """Return a configured version of a generic Create endpoint."""

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

    route = APIRoute(
        path=f"{API_PREFIX}/{model_type}/upsert",
        methods=["post"],
        endpoint=upsert,
        tags=[fides_model.__name__],
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

    return route


def delete_route_factory(fides_model: FidesModelType, model_type: str) -> APIRoute:
    """Return a configured version of a generic 'Delete' route."""

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
        deleted_resource_dict = model_map[model_type].from_orm(deleted_resource).dict()
        return {
            "message": "resource deleted",
            "resource": deleted_resource_dict,
        }

    route = APIRoute(
        path=f"{API_PREFIX}/{model_type}/" + "{fides_key}",
        methods=["delete"],
        tags=[fides_model.__name__],
        endpoint=delete,
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

    return route
