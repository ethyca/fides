from typing import Any, Dict

import pytest
from pydantic import ValidationError

from fidesops.ops.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchema,
    SaaSSchemaFactory,
)
from fidesops.ops.schemas.saas.saas_config import SaaSConfig


@pytest.mark.unit_saas
class TestSaaSConnectionSecrets:
    @pytest.fixture(scope="function")
    def saas_config(self, saas_example_config: Dict[str, Any]) -> SaaSConfig:
        return SaaSConfig(**saas_example_config)

    def test_get_saas_schema(self, saas_config):
        """
        Assert the schema name is derived from the SaaS config fides key and
        that the schema is a subclass of SaaSSchema
        """
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        assert schema.__name__ == f"{saas_config.type}_schema"
        assert issubclass(schema.__base__, SaaSSchema)

    def test_validation(
        self, saas_config: SaaSConfig, saas_example_secrets: Dict[str, Any]
    ):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = saas_example_secrets
        schema.parse_obj(config)

    def test_missing_fields(self, saas_config: SaaSConfig):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {"domain": "domain", "username": "username"}
        with pytest.raises(ValidationError) as exc:
            schema.parse_obj(config)
        required_fields = [
            connector_param.name
            for connector_param in saas_config.connector_params
            if not connector_param.default_value
        ]
        assert (
            f"{saas_config.type}_schema must be supplied all of: "
            f"[{', '.join(required_fields)}]." in str(exc.value)
        )

    def test_extra_fields(
        self, saas_config: SaaSConfig, saas_example_secrets: Dict[str, Any]
    ):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {
            **saas_example_secrets,
            "extra": "extra",
        }
        with pytest.raises(ValidationError) as exc:
            schema.parse_obj(config)
        assert exc.value.errors()[0]["msg"] == "extra fields not permitted"

    def test_default_value_fields(
        self, saas_config: SaaSConfig, saas_example_secrets: Dict[str, Any]
    ):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        domain_param = next(
            connector_param
            for connector_param in saas_config.connector_params
            if connector_param.name == "domain"
        )
        assert domain_param.default_value
        del saas_example_secrets["domain"]
        config = saas_example_secrets
        schema.parse_obj(config)
