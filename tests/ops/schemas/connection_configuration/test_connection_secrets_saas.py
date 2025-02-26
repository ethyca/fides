from typing import Any, Dict

import pytest
from pydantic import ValidationError

from fides.api.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchema,
    SaaSSchemaFactory,
)
from fides.api.schemas.saas.saas_config import (
    ConnectorParam,
    ExternalDatasetReference,
    SaaSConfig,
)


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
        schema.model_validate(config)

    def test_missing_fields(self, saas_config: SaaSConfig):
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {"domain": "domain", "username": "username"}
        with pytest.raises(ValidationError) as exc:
            schema.model_validate(config)

        required_fields = [
            connector_param.name
            for connector_param in (
                saas_config.connector_params + saas_config.external_references
            )
            if isinstance(
                connector_param, ExternalDatasetReference
            )  # external refs are required
            or not connector_param.default_value
        ]

        errors = exc._excinfo[1].errors()
        assert (
            errors[0]["msg"]
            == "Value error, custom_schema must be supplied all of: [username, api_key, api_version, page_size, account_types, customer_id]."
        )

    def test_extra_fields(
        self, saas_config: SaaSConfig, saas_example_secrets: Dict[str, Any]
    ):
        # extra fields are allowed
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        config = {
            **saas_example_secrets,
            "extra": "extra",
        }
        schema.model_validate(config)

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
        schema.model_validate(config)

    def test_value_in_options(self, saas_config: SaaSConfig):
        saas_config.connector_params = [
            ConnectorParam(name="account_type", options=["checking", "savings"])
        ]
        saas_config.external_references = []
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        schema.model_validate({"account_type": "checking"})

    def test_value_in_options_with_multiselect(self, saas_config: SaaSConfig):
        saas_config.connector_params = [
            ConnectorParam(
                name="account_type", options=["checking", "savings"], multiselect=True
            )
        ]
        saas_config.external_references = []
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        schema.model_validate({"account_type": ["checking", "savings"]})

    def test_value_not_in_options(self, saas_config: SaaSConfig):
        saas_config.connector_params = [
            ConnectorParam(name="account_type", options=["checking", "savings"])
        ]
        saas_config.external_references = []
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        with pytest.raises(ValidationError) as exc:
            schema.model_validate({"account_type": "investment"})
        assert "'account_type' must be one of [checking, savings]" in str(exc.value)

    def test_value_not_in_options_with_multiselect(self, saas_config: SaaSConfig):
        saas_config.connector_params = [
            ConnectorParam(
                name="account_type", options=["checking", "savings"], multiselect=True
            )
        ]
        saas_config.external_references = []
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        with pytest.raises(ValidationError) as exc:
            schema.model_validate({"account_type": ["checking", "investment"]})
        assert (
            "[investment] are not valid options, 'account_type' must be a list of values from [checking, savings]"
            in str(exc.value)
        )
