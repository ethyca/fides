# pylint: disable=missing-function-docstring

from fideslib.schemas.base_class import FidesSchema, NoValidationSchema


def test_get_field_names():
    class Test(FidesSchema):
        test_field: str

    test = Test(test_field="test")
    assert test.get_field_names() == ["test_field"]


def test_no_validation():
    test_value = "test"

    assert NoValidationSchema.validate(test_value) == test_value
