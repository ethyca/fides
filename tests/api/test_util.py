# pylint: disable=missing-docstring, redefined-outer-name
import pytest

from fidesapi.routes.util import obscure_string, unobscure_string


@pytest.mark.unit
@pytest.mark.parametrize(
    "sample_string", ["test1:'as?/<>.,", "!@#$%^&*()-_+=", "1a2b3c4d5e6F7G8H9I0J"]
)
def test_obscure_string(sample_string: str) -> None:
    obscured_string = obscure_string(sample_string)
    assert sample_string == unobscure_string(obscured_string)
