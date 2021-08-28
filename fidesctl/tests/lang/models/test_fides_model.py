import pytest
from pydantic import ValidationError

from fideslang.models import fides_model


@pytest.mark.unit
def test_fides_model_valid():
    fides_key = fides_model.FidesModel(fidesKey="foo_bar")
    assert fides_key


@pytest.mark.unit
def test_fides_model_invalid():
    "Check for a bunch of different possible bad characters here."
    with pytest.raises(ValidationError):
        fides_model.FidesModel(fidesKey="foo-bar")

    with pytest.raises(ValidationError):
        fides_model.FidesModel(fidesKey="foo/bar")

    with pytest.raises(ValidationError):
        fides_model.FidesModel(fidesKey="foo=bar")

    with pytest.raises(ValidationError):
        fides_model.FidesModel(fidesKey="foo^bar")

    with pytest.raises(ValidationError):
        fides_model.FidesModel(fidesKey="_foo^bar")

    with pytest.raises(ValidationError):
        fides_model.FidesModel(fidesKey="")
