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
    def saas_config(self, saas_example_config) -> SaaSConfig:
        return SaaSConfig(**saas_example_config)

    def test_get_saas_schema(self, saas_config):
        """
        Assert the schema name is derived from the SaaS config fides key and
        that the schema is a subclass of SaaSSchema
        """
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        assert schema.__name__ == f"{saas_config.fides_key}_schema"
        assert issubclass(schema.__base__, SaaSSchema)

    def test_validation(self, saas_config, saas_example_secrets):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = saas_example_secrets
        schema.parse_obj(config)

    def test_missing_fields(self, saas_config):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {"domain": "domain", "username": "username"}
        with pytest.raises(ValidationError) as exc:
            schema.parse_obj(config)
        assert (
            f"{saas_config.fides_key}_schema must be supplied all of: "
            f"[{', '.join([connector_param.name for connector_param in saas_config.connector_params])}]."
            in str(exc.value)
        )

    def test_extra_fields(self, saas_config, saas_example_secrets):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {
            **saas_example_secrets,
            "extra": "extra",
        }
        with pytest.raises(ValidationError) as exc:
            schema.parse_obj(config)
        assert exc.value.errors()[0]["msg"] == "extra fields not permitted"
