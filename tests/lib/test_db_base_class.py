# pylint: disable=missing-function-docstring

import pytest
from fideslang.validation import FidesValidationError  # type: ignore

from fides.api.ops.db.base_class import get_key_from_data
from fides.lib.exceptions import KeyValidationError


def test_get_key_from_data():
    key = get_key_from_data({"key": "test_key", "name": "config name"}, "StorageConfig")
    assert key == "test_key"


def test_get_key_from_data_no_key():
    key = get_key_from_data({"name": "config name"}, "StorageConfig")
    assert key == "config_name"


def test_get_key_from_data_no_data():
    with pytest.raises(KeyValidationError):
        get_key_from_data({}, "StorageConfig")


def test_get_key_from_data_invalid():
    with pytest.raises(FidesValidationError):
        get_key_from_data({"key": "test*key", "name": "config name"}, "StorageConfig")
