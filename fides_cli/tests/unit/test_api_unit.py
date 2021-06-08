"""Unit tests for the API module."""
import pytest

from fides.core import api as _api


def test_generate_object_urls_no_id(server_url):
    """
    Test that the URL generator works as intended.
    """
    expected_url = f"{server_url}/v1/test/"
    result_url = _api.generate_object_url(
        url=server_url, object_type="test", version="v1"
    )
    assert expected_url == result_url


def test_generate_object_urls_with_id(server_url):
    """
    Test that the URL generator works as intended.
    """
    expected_url = f"{server_url}/v1/test/1"
    result_url = _api.generate_object_url(
        url=server_url, object_type="test", version="v1", object_id="1"
    )
    assert expected_url == result_url
