from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST


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
