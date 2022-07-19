# pylint: disable=missing-docstring, redefined-outer-name
"""
Tests for category visualization
"""
import json
from typing import Dict, List

import pytest

from fidesctl.core import visualize


@pytest.fixture
def sample_categories_list() -> List:
    return [
        {
            "fides_key": "user",
            "organization_fides_key": "default_organization",
            "name": "User Data",
            "description": "Data related to a user.",
            "parent_key": None,
        },
        {
            "fides_key": "user.contact",
            "organization_fides_key": "default_organization",
            "name": "User Contact Data",
            "description": "Contact data related to a user.",
            "parent_key": "user",
        },
        {
            "fides_key": "user.contact.address",
            "organization_fides_key": "default_organization",
            "name": "User Address",
            "description": "User address data.",
            "parent_key": "user.contact",
        },
    ]


@pytest.mark.unit
def test_hierarchy_figures(sample_categories_list: List) -> None:
    with open("tests/ctl/data/sample_hierarchy_figures.json", "r") as sample_hierarchy:
        expected_sample_hierarchy_figures = json.load(sample_hierarchy)
    hierarchy_figures = visualize.hierarchy_figures(
        sample_categories_list, resource_type="data_category", json_out=True
    )
    assert json.loads(hierarchy_figures) == expected_sample_hierarchy_figures


@pytest.mark.unit
def test_convert_categories_to_nested_dict(sample_categories_list: List) -> None:
    expected_conversion: Dict = {"user": {"contact": {"address": {}}}}
    assert (
        visualize.convert_categories_to_nested_dict(sample_categories_list)
        == expected_conversion
    )


@pytest.mark.unit
def test_nested_categories_to_html_list(sample_categories_list: List) -> None:
    expected_html_list = "<h2>Fides Data Category Hierarchy</h2>\n   <li>user</li>\n   <ul>\n      <li>contact</li>\n      <ul>\n         <li>address</li>\n         <ul>\n\n         </ul>\n      </ul>\n   </ul>"
    assert (
        visualize.nested_categories_to_html_list(
            sample_categories_list, resource_type="data_category"
        )
        == expected_html_list
    )
