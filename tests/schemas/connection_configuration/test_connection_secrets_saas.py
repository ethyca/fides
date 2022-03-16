import pytest
from pydantic import ValidationError
from fidesops.schemas.saas.saas_config import SaaSConfig
from fidesops.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchema,
    SaaSSchemaFactory,
)


@pytest.mark.unit_saas
class TestSaaSConnectionSecrets:
    @pytest.fixture(scope="function")
    def saas_config(self, saas_configs) -> SaaSConfig:
        return SaaSConfig(**saas_configs["saas_example"])

    def test_get_saas_schema(self, saas_config):
        """
        Assert the schema name is derived from the SaaS config fides key and
        that the schema is a subclass of SaaSSchema
        """
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        assert schema.__name__ == f"{saas_config.fides_key}_schema"
        assert issubclass(schema.__base__, SaaSSchema)

    def test_validation(self, saas_config):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {"domain": "domain", "username": "username", "api_key": "api_key"}
        schema.parse_obj(config)

    def test_missing_fields(self, saas_config):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {"domain": "domain", "username": "username"}
        with pytest.raises(ValidationError) as exception:
            schema.parse_obj(config)
        errors = exception.value.errors()
        assert errors[0]["msg"] == "field required"
        assert (
            errors[1]["msg"]
            == f"{saas_config.fides_key}_schema must be supplied all of: "
            f"[{', '.join([connector_param.name for connector_param in saas_config.connector_params])}]."
        )

    def test_extra_fields(self, saas_config):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {
            "domain": "domain",
            "username": "username",
            "api_key": "api_key",
            "extra": "extra",
        }
        with pytest.raises(ValidationError) as exception:
            schema.parse_obj(config)
        assert exception.value.errors()[0]["msg"] == "extra fields not permitted"
