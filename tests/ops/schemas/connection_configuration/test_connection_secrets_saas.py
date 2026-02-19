from typing import Any, Dict
from unittest.mock import patch

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
        assert exc.type is ValidationError

    def test_value_not_in_options_with_multiselect(self, saas_config: SaaSConfig):
        saas_config.connector_params = [
            ConnectorParam(
                name="account_type", options=["checking", "savings"], multiselect=True
            )
        ]
        saas_config.external_references = []
        schema = SaaSSchemaFactory(saas_config).get_saas_schema()
        with pytest.raises(ValidationError) as exc:
            schema.model_validate({"account_type": ["checking", "brokerage"]})


@pytest.mark.unit_saas
class TestSaaSConnectionSecretsDomainValidation:
    """Tests for domain validation during secret validation."""

    @pytest.fixture(scope="function")
    def saas_config_with_allowed_domains(
        self, saas_example_config: Dict[str, Any]
    ) -> SaaSConfig:
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                default_value="api.stripe.com",
                allowed_domains=["api.stripe.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        return config

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=False,
    )
    def test_allowed_domain_passes(
        self, mock_disabled, saas_config_with_allowed_domains
    ):
        """Setting a domain that matches allowed_domains should succeed."""
        schema = SaaSSchemaFactory(saas_config_with_allowed_domains).get_saas_schema()
        schema.model_validate({"domain": "api.stripe.com", "api_key": "sk_test_123"})

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=False,
    )
    def test_disallowed_domain_fails(
        self, mock_disabled, saas_config_with_allowed_domains
    ):
        """Setting a domain not in allowed_domains should fail."""
        schema = SaaSSchemaFactory(saas_config_with_allowed_domains).get_saas_schema()
        with pytest.raises(ValidationError, match="not in the list of allowed domains"):
            schema.model_validate(
                {"domain": "evil.example.com", "api_key": "sk_test_123"}
            )

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=True,
    )
    def test_disallowed_domain_passes_when_validation_disabled(
        self, mock_disabled, saas_config_with_allowed_domains
    ):
        """Domain validation should be skipped when disabled."""
        schema = SaaSSchemaFactory(saas_config_with_allowed_domains).get_saas_schema()
        schema.model_validate({"domain": "evil.example.com", "api_key": "sk_test_123"})

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=False,
    )
    def test_empty_allowed_domains_permits_any_value(
        self, mock_disabled, saas_example_config: Dict[str, Any]
    ):
        """Empty allowed_domains list should permit any domain value."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                default_value="custom.example.com",
                allowed_domains=[],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        schema.model_validate(
            {"domain": "anything.example.com", "api_key": "sk_test_123"}
        )

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=False,
    )
    def test_none_allowed_domains_no_validation(
        self, mock_disabled, saas_example_config: Dict[str, Any]
    ):
        """None allowed_domains (omitted) should skip validation entirely."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(name="domain", default_value="localhost"),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        schema.model_validate(
            {"domain": "literally-anything", "api_key": "sk_test_123"}
        )

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=False,
    )
    def test_wildcard_allowed_domain(
        self, mock_disabled, saas_example_config: Dict[str, Any]
    ):
        """Wildcard patterns in allowed_domains should be validated."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                allowed_domains=["*.salesforce.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        schema.model_validate(
            {"domain": "na1.salesforce.com", "api_key": "sk_test_123"}
        )

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=False,
    )
    def test_wildcard_disallowed_domain(
        self, mock_disabled, saas_example_config: Dict[str, Any]
    ):
        """Domain not matching wildcard pattern should fail."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                allowed_domains=["*.salesforce.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        with pytest.raises(ValidationError, match="not in the list of allowed domains"):
            schema.model_validate(
                {"domain": "evil.example.com", "api_key": "sk_test_123"}
            )


@pytest.mark.unit_saas
class TestSingleExactDomainAutoFill:
    """Tests for auto-filling connector params that have a single exact allowed domain."""

    def test_single_exact_domain_marked_hidden(
        self, saas_example_config: Dict[str, Any]
    ):
        """A param with one exact allowed_domain should be marked hidden with the domain as default."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                allowed_domains=["api.stripe.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        field = schema.model_fields["domain"]
        assert field.default == "api.stripe.com"
        assert field.json_schema_extra["hidden"] is True

    def test_single_exact_domain_with_existing_default(
        self, saas_example_config: Dict[str, Any]
    ):
        """A param that already has a default_value should keep it and still be hidden."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                default_value="api.stripe.com",
                allowed_domains=["api.stripe.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        field = schema.model_fields["domain"]
        assert field.default == "api.stripe.com"
        assert field.json_schema_extra["hidden"] is True

    def test_single_wildcard_domain_not_hidden(
        self, saas_example_config: Dict[str, Any]
    ):
        """A param with one wildcard allowed_domain should NOT be hidden."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                allowed_domains=["*.auth0.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        field = schema.model_fields["domain"]
        assert field.json_schema_extra.get("hidden") is not True

    def test_multiple_allowed_domains_not_hidden(
        self, saas_example_config: Dict[str, Any]
    ):
        """A param with multiple allowed_domains should NOT be hidden."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                default_value="na1.salesforce.com",
                allowed_domains=["*.salesforce.com", "*.force.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        field = schema.model_fields["domain"]
        assert field.json_schema_extra.get("hidden") is not True

    @patch(
        "fides.api.schemas.connection_configuration.connection_secrets_saas.is_domain_validation_disabled",
        return_value=False,
    )
    def test_omitting_hidden_field_uses_default(
        self, mock_disabled, saas_example_config: Dict[str, Any]
    ):
        """Omitting a hidden single-exact-domain param should auto-fill the default."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                allowed_domains=["api.stripe.com"],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        instance = schema.model_validate({"api_key": "sk_test_123"})
        assert instance.domain == "api.stripe.com"

    def test_none_allowed_domains_not_hidden(
        self, saas_example_config: Dict[str, Any]
    ):
        """A param with allowed_domains=None should NOT be hidden."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                default_value="api.example.com",
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        field = schema.model_fields["domain"]
        assert field.json_schema_extra.get("hidden") is not True

    def test_empty_allowed_domains_not_hidden(
        self, saas_example_config: Dict[str, Any]
    ):
        """A param with allowed_domains=[] should NOT be hidden."""
        config = SaaSConfig(**saas_example_config)
        config.connector_params = [
            ConnectorParam(
                name="domain",
                default_value="custom.example.com",
                allowed_domains=[],
            ),
            ConnectorParam(name="api_key"),
        ]
        config.external_references = []
        schema = SaaSSchemaFactory(config).get_saas_schema()
        field = schema.model_fields["domain"]
        assert field.json_schema_extra.get("hidden") is not True
