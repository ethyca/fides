"""Unit tests for the API module."""
import pytest

from fidesctl.core import api as _api


def test_generate_object_urls_no_id(test_config):
    """
    Test that the URL generator works as intended.
    """
    expected_url = f"{test_config}/v1/test/"
    result_url = _api.generate_object_url(
        url=test_config, object_type="test", version="v1"
    )
    assert expected_url == result_url


def test_generate_object_urls_with_id(test_config):
    """
    Test that the URL generator works as intended.
    """
    expected_url = f"{test_config}/v1/test/1"
    result_url = _api.generate_object_url(
        url=test_config, object_type="test", version="v1", object_id="1"
    )
    assert expected_url == result_url
