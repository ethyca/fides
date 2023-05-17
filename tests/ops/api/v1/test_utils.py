from datetime import datetime
from html import escape

import pytest
from fastapi import HTTPException

from fides.api.api.v1.endpoints.utils import (
    transform_fields,
    validate_start_and_end_filters,
)
from fides.api.schemas.privacy_notice import PrivacyNotice


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


class TestTransformFields:
    def test_transform_escape(self):
        escaped_field = "user&#x27;s description &lt;script /&gt;"
        notice_1 = PrivacyNotice(name="whew", description=escaped_field)

        unescaped_field = "user's description <script />"
        notice_2 = PrivacyNotice(name="whew", description=unescaped_field)
        notice_2 = transform_fields(escape, notice_2, ["description"])

        assert notice_1 == notice_2
