from pydantic import ValidationError
import pytest

from fideslang.models.fides_model import FidesModel
from fideslang.models.validation import FidesValidationError


@pytest.mark.unit
def test_fides_model_valid():
    fides_key = FidesModel(fidesKey="foo_bar", name="Foo Bar")
    assert fides_key


@pytest.mark.unit
def test_fides_model_extras_invalid():
    with pytest.raises(ValidationError):
        FidesModel.parse_obj(
            {"fidesKey": "foo_bar", "name": "Foo Bar", "extra": "extra"}
        )
    assert True


@pytest.mark.unit
def test_fides_model_fides_key_invalid():
    "Check for a bunch of different possible bad characters here."
    with pytest.raises(FidesValidationError):
        FidesModel(fidesKey="foo-bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fidesKey="foo/bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fidesKey="foo=bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fidesKey="foo^bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fidesKey="_foo^bar")

    with pytest.raises(FidesValidationError):
        FidesModel(fidesKey="")
