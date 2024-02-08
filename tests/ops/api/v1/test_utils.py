from datetime import datetime
from html import escape

import pytest
from fastapi import HTTPException

from fides.api.schemas.language import SupportedLanguage
from fides.api.schemas.privacy_notice import NoticeTranslation
from fides.api.util.endpoint_utils import (
    human_friendly_list,
    transform_fields,
    validate_start_and_end_filters,
)


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
        translation_1 = NoticeTranslation(
            language=SupportedLanguage.english, title="whew", description=escaped_field
        )

        unescaped_field = "user's description <script />"
        translation_2 = NoticeTranslation(
            language=SupportedLanguage.english,
            title="whew",
            description=unescaped_field,
        )
        translation_2 = transform_fields(escape, translation_2, ["description"])

        assert translation_1 == translation_2


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
