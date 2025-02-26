# pylint: disable=missing-function-docstring

from fides.api.schemas.base_class import FidesSchema, NoValidationSchema
from fides.api.schemas.connection_configuration import MongoDBDocsSchema


def test_get_field_names():
    class Test(FidesSchema):
        test_field: str

    test = Test(test_field="test")
    assert test.get_field_names() == ["test_field"]


def test_no_validation():
    test_value = "test"

    assert NoValidationSchema.model_validate(test_value) == test_value

    mongo_secrets = {
        "host": "mongodb-test",
        "port": 27017,
        "username": "mongo_user",
        "password": "mongo_pass",
        "defaultauthdb": "mongo_test",
    }

    mongo_schema = MongoDBDocsSchema.model_validate(mongo_secrets)

    assert mongo_schema == mongo_secrets
    assert isinstance(mongo_secrets, dict)
