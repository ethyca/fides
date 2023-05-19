from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, List, Optional, Tuple

from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address  # type: ignore
from starlette.status import HTTP_400_BAD_REQUEST

from fides.core.config import CONFIG

# Used for rate limiting with Slow API
# Decorate individual routes to deviate from the default rate limits
fides_limiter = Limiter(
    default_limits=[CONFIG.security.request_rate_limit],
    headers_enabled=True,
    key_prefix=CONFIG.security.rate_limit_prefix,
    key_func=get_remote_address,
    retry_after="http-date",
)


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


def transform_fields(
    transformation: Callable, model: object, fields: List[str]
) -> object:
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
