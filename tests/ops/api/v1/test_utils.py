from datetime import datetime

import pytest
from fastapi import HTTPException

from fides.api.ops.api.v1.endpoints.utils import validate_start_and_end_filters


class TestValidateStartAndEndFilters:
    def test_start_date_after_end_date(self):
        with pytest.raises(HTTPException):
            validate_start_and_end_filters(
                [(datetime(2020, 1, 1), datetime(2020, 2, 2), "created")]
            )

    def test_value_is_none(self):
        validate_start_and_end_filters([(None, datetime(2020, 2, 2), "created")])
        validate_start_and_end_filters([(datetime(2020, 1, 1), None, "created")])

    def test_value_is_not_a_date(self):
        validate_start_and_end_filters([(1, datetime(2020, 2, 2), "created")])
        validate_start_and_end_filters([(datetime(2020, 1, 1), 1, "created")])

    def test_valid_dates(self):
        validate_start_and_end_filters(
            [(datetime(2020, 2, 2), datetime(2020, 2, 1), "created")]
        )
