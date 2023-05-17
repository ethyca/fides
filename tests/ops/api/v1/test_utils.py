from datetime import datetime
from html import escape

import pytest
from fastapi import HTTPException

from fides.api.ops.api.v1.endpoints.utils import (
    human_friendly_list,
    transform_fields,
    validate_start_and_end_filters,
)
from fides.api.ops.schemas.privacy_notice import PrivacyNotice


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


class TestHumanFriendlyList:
    def test_no_items(self):
        assert human_friendly_list([]) == ""
        assert human_friendly_list(None) == ""

    def test_one_item(self):
        assert human_friendly_list(["red"]) == "red"
        assert human_friendly_list([1]) == "1"

    def test_two_items(self):
        assert human_friendly_list(["red", "blue"]) == "red and blue"
        assert human_friendly_list([1, "blue"]) == "1 and blue"

    def test_three_items(self):
        assert human_friendly_list(["red", "blue", "yellow"]) == "red, blue, and yellow"
        assert human_friendly_list([1, "blue", "yellow"]) == "1, blue, and yellow"

    def test_four_items(self):
        assert (
            human_friendly_list(["red", "blue", "yellow", "green"])
            == "red, blue, yellow, and green"
        )
        assert (
            human_friendly_list([1, "blue", "yellow", "green"])
            == "1, blue, yellow, and green"
        )
