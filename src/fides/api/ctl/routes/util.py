from typing import Dict, List

from fideslang import FidesModelType

from fides.api.ctl.database.crud import get_resource, list_resource
from fides.api.ctl.sql_models import (  # type: ignore[attr-defined]
    models_with_default_field,
)
from fides.api.ctl.utils import errors
from fides.api.ctl.utils.api_router import APIRouter
from fides.lib.db.base import Base  # type: ignore[attr-defined]

API_PREFIX = "/api/v1"


def get_resource_type(router: APIRouter) -> str:
    """
    Get the resource type from the prefix of an API router
    Args:
        router: Api router from which to extract the resource type

    Returns:
        The router's resource type
    """
    return router.prefix.replace(f"{API_PREFIX}/", "", 1)


async def forbid_if_editing_is_default(
    sql_model: Base, fides_key: str, payload: FidesModelType
) -> None:
    """
    Raise a forbidden error if the user is trying modify the `is_default` field
    """
    if sql_model in models_with_default_field:
        resource = await get_resource(sql_model, fides_key)
        if resource.is_default != payload.is_default:
            raise errors.ForbiddenError(sql_model.__name__, fides_key)


async def forbid_if_default(sql_model: Base, fides_key: str) -> None:
    """
    Raise a forbidden error if the user is trying to operate on a resource
    with `is_default=True`
    """
    if sql_model in models_with_default_field:
        resource = await get_resource(sql_model, fides_key)
        if resource.is_default:
            raise errors.ForbiddenError(sql_model.__name__, fides_key)


async def forbid_if_editing_any_is_default(
    sql_model: Base, resources: List[Dict]
) -> None:
    """
    Raise a forbidden error if any of the existing resources' `is_default`
    field is being modified, or if there is a new resource with `is_default=True`
    """
    if sql_model in models_with_default_field:
        fides_keys = [resource["fides_key"] for resource in resources]
        existing_resources = {
            r.fides_key: r
            for r in await list_resource(sql_model)
            if r.fides_key in fides_keys
        }
        for resource in resources:
            if existing_resources.get(resource["fides_key"]) is None:
                # new resource is being upserted
                if resource["is_default"]:
                    raise errors.ForbiddenError(
                        sql_model.__name__, resource["fides_key"]
                    )
            elif (
                resource["is_default"]
                != existing_resources[resource["fides_key"]].is_default
            ):
                raise errors.ForbiddenError(sql_model.__name__, resource["fides_key"])
