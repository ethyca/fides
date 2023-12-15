from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException
from fideslang import FidesModelType
from slowapi import Limiter
from slowapi.util import get_remote_address  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST

from fides.api.db.base import Base  # type: ignore
from fides.api.db.crud import get_resource, list_resource
from fides.api.util import errors
from fides.common.api.scope_registry import (
    CTL_DATASET,
    CTL_POLICY,
    DATA_CATEGORY,
    DATA_SUBJECT,
    DATA_USE,
    EVALUATION,
    ORGANIZATION,
    SYSTEM,
)
from fides.config import CONFIG

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    ModelWithDefaultField,
)

API_PREFIX = "/api/v1"
# Map the ctl model type to the scope prefix.
# Policies and datasets have ctl-* prefixes to
# avoid overlapping with ops scopes of same name
CLI_SCOPE_PREFIX_MAPPING: Dict[str, str] = {
    "data_category": DATA_CATEGORY,
    "data_subject": DATA_SUBJECT,
    "data_use": DATA_USE,
    "dataset": CTL_DATASET,
    "evaluation": EVALUATION,
    "organization": ORGANIZATION,
    "policy": CTL_POLICY,
    "system": SYSTEM,
}

# Used for rate limiting with Slow API
# Decorate individual routes to deviate from the default rate limits
fides_limiter = Limiter(
    default_limits=[CONFIG.security.request_rate_limit],
    headers_enabled=True,
    key_prefix=CONFIG.security.rate_limit_prefix,
    key_func=get_remote_address,
    retry_after="http-date",
)


async def forbid_if_editing_is_default(
    sql_model: Base,
    fides_key: str,
    payload: FidesModelType,
    async_session: AsyncSession,
) -> None:
    """
    Raise a forbidden error if the user is trying modify the `is_default` field
    """
    if isinstance(sql_model, ModelWithDefaultField):
        resource = await get_resource(sql_model, fides_key, async_session)

        assert isinstance(
            resource, ModelWithDefaultField
        ), "Provided Resource is not the right type!"
        assert isinstance(
            payload, ModelWithDefaultField
        ), "Provided Payload is not the right type!"

        if resource.is_default != payload.is_default:
            raise errors.ForbiddenError(sql_model.__name__, fides_key)


async def forbid_if_default(
    sql_model: Base, fides_key: str, async_session: AsyncSession
) -> None:
    """
    Raise a forbidden error if the user is trying to operate on a resource
    with `is_default=True`
    """
    if isinstance(sql_model, ModelWithDefaultField):
        resource = await get_resource(sql_model, fides_key, async_session)
        if resource.is_default:
            raise errors.ForbiddenError(sql_model.__name__, fides_key)


async def forbid_if_editing_any_is_default(
    sql_model: Base, resources: List[Dict], async_session: AsyncSession
) -> None:
    """
    Raise a forbidden error if any of the existing resources' `is_default`
    field is being modified, or if there is a new resource with `is_default=True`
    """
    if isinstance(sql_model, ModelWithDefaultField):
        fides_keys = [resource["fides_key"] for resource in resources]
        existing_resources = {
            r.fides_key: r
            for r in await list_resource(sql_model, async_session)
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


def validate_start_and_end_filters(
    date_filters: List[Tuple[Optional[datetime], Optional[datetime], str]]
) -> None:
    """Assert that start date isn't after end date

    Pass in a list of tuples like: [(less_than_filter, greater_than_filter, filter_name)]
    """
    for end, start, field_name in date_filters:
        if end is None or start is None:
            continue

        if not (isinstance(end, datetime) and isinstance(start, datetime)):
            continue

        if end < start:
            # With date fields, if the start date is after the end date, return a 400
            # because no records will lie within this range.
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Value specified for {field_name}_lt: {end} must be after {field_name}_gt: {start}.",
            )


def transform_fields(transformation: Callable, model: Base, fields: List[str]) -> Base:
    """
    Takes a callable and returns a transformed object.
    """

    for name, value in {field: getattr(model, field) for field in fields}.items():
        if value:
            setattr(model, name, transformation(value))

    return model


def human_friendly_list(item_list: List[Any]) -> str:
    """Util to turn a list into a human friendly string for better error messages"""
    if not item_list:
        return ""

    stringified_list = [str(item) for item in item_list]

    length = len(stringified_list)
    if length == 1:
        return stringified_list[0]
    if length == 2:
        return " and ".join(stringified_list)
    return ", ".join(stringified_list[0:-1]) + f", and {stringified_list[-1]}"
