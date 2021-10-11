"""
Tests for category visualization
"""
import json

import pytest

from fidesctl.core import visualize


@pytest.fixture
def sample_categories_list():
    return [
        {
            "fides_key": "account",
            "organization_fides_key": "default_organization",
            "name": "Account Data",
            "description": "Data related to a system account.",
            "parent_key": None,
        },
        {
            "fides_key": "account.contact",
            "organization_fides_key": "default_organization",
            "name": "Account Contact Data",
            "description": "Contact data related to a system account.",
            "parent_key": "account",
        },
        {
            "fides_key": "account.contact.city",
            "organization_fides_key": "default_organization",
            "name": "Account City",
            "description": "Account's city level address data.",
            "parent_key": "account.contact",
        },
    ]


@pytest.mark.unit
def test_category_sunburst_plot(sample_categories_list):
    print("reading file...")
    with open("tests/data/sample_sunburst.json", "r") as f:
        expected_sample_sunburst = json.load(f)
    print("file read, using function")
    sample_sunburst = visualize.sunburst_plot(
        sample_categories_list, resource_type="data_category", json_out=True
    )
    assert json.loads(sample_sunburst) == expected_sample_sunburst


# @pytest.mark.unit
def test_category_sankey_plot(sample_categories_list):
    with open("tests/data/sample_sankey.json", "r") as f:
        expected_sample_sankey = json.load(f)
    sample_sankey = visualize.sankey_plot(
        sample_categories_list, resource_type="data_category", json_out=True
    )
    assert json.loads(sample_sankey) == expected_sample_sankey


@pytest.mark.unit
def test_convert_categories_to_nested_dict(sample_categories_list):
    expected_conversion = {"account": {"contact": {"city": {}}}}
    assert (
        visualize.convert_categories_to_nested_dict(sample_categories_list)
        == expected_conversion
    )


@pytest.mark.unit
def test_nested_categories_to_html_list(sample_categories_list):
    expected_html_list = "<h2>Fides Data Category Hierarchy</h2>\n   <li>account</li>\n   <ul>\n      <li>contact</li>\n      <ul>\n         <li>city</li>\n         <ul>\n\n         </ul>\n      </ul>\n   </ul>"
    assert (
        visualize.nested_categories_to_html_list(
            sample_categories_list, resource_type="data_category"
        )
        == expected_html_list
    )
