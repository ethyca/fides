"""Tests for ConnectionService including event auditing functionality."""

import copy
from textwrap import dedent
from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectionNotFoundException
from fides.api.models.connection_oauth_credentials import OAuthConfig, OAuthGrantType
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.event_audit import EventAuditType
from fides.api.models.saas_template_dataset import SaasTemplateDataset
from fides.api.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.schemas.connection_configuration.connection_oauth_config import (
    OAuthConfigSchema,
)
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.enums.connection_category import ConnectionCategory
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.service.connection.connection_service import ConnectionService
from fides.service.connection.merge_configs_util import merge_datasets
from fides.service.event_audit_service import EventAuditService


class TestConnectionService:
    """Tests for ConnectionService functionality."""

    @pytest.fixture
    def stored_dataset(self) -> Dict[str, Any]:
        """Fixture for the stored dataset."""
        stored_dataset = {
            "fides_key": "<instance_fides_key>",
            "name": "Template Dataset",
            "description": "Dataset from template",
            "data_categories": None,
            "fides_meta": None,
            "organization_fides_key": "default_organization",
            "tags": None,
            "meta": None,
            "collections": [
                {
                    "name": "products",
                    "description": None,
                    "data_categories": None,
                    "fides_meta": None,
                    "fields": [
                        {
                            "name": "product_id",
                            "description": None,
                            "data_categories": ["system.operations"],
                            "fides_meta": {
                                "custom_request_field": None,
                                "data_type": "string",
                                "identity": None,
                                "length": None,
                                "masking_strategy_override": None,
                                "primary_key": True,
                                "read_only": None,
                                "redact": None,
                                "references": None,
                                "return_all_elements": None,
                            },
                            "fields": None,
                        },
                        {
                            "name": "customer_id",
                            "description": None,
                            "data_categories": ["user.unique_id"],
                            "fides_meta": {
                                "custom_request_field": None,
                                "data_type": "string",
                                "identity": None,
                                "length": None,
                                "masking_strategy_override": None,
                                "primary_key": None,
                                "read_only": None,
                                "redact": None,
                                "references": None,
                                "return_all_elements": None,
                            },
                            "fields": None,
                        },
                        {
                            "name": "email",
                            "description": None,
                            "data_categories": ["user.contact.email"],
                            "fides_meta": {
                                "custom_request_field": None,
                                "data_type": "string",
                                "identity": None,
                                "length": None,
                                "masking_strategy_override": None,
                                "primary_key": None,
                                "read_only": None,
                                "redact": None,
                                "references": None,
                                "return_all_elements": None,
                            },
                            "fields": None,
                        },
                        {
                            "name": "address",
                            "description": None,
                            "data_categories": None,
                            "fides_meta": {
                                "custom_request_field": None,
                                "data_type": "object",
                                "identity": None,
                                "length": None,
                                "masking_strategy_override": None,
                                "primary_key": None,
                                "read_only": None,
                                "redact": None,
                                "references": None,
                                "return_all_elements": None,
                            },
                            "fields": [
                                {
                                    "name": "city",
                                    "description": None,
                                    "data_categories": ["user.contact.address"],
                                    "fides_meta": {
                                        "custom_request_field": None,
                                        "data_type": "string",
                                        "identity": None,
                                        "length": None,
                                        "masking_strategy_override": None,
                                        "primary_key": None,
                                        "read_only": None,
                                        "redact": None,
                                        "references": None,
                                        "return_all_elements": None,
                                    },
                                    "fields": None,
                                },
                                {
                                    "name": "street",
                                    "description": None,
                                    "data_categories": ["user.contact.address.street"],
                                    "fides_meta": {
                                        "custom_request_field": None,
                                        "data_type": "string",
                                        "identity": None,
                                        "length": None,
                                        "masking_strategy_override": None,
                                        "primary_key": None,
                                        "read_only": None,
                                        "redact": None,
                                        "references": None,
                                        "return_all_elements": None,
                                    },
                                    "fields": None,
                                },
                            ],
                        },
                    ],
                }
            ],
        }
        return stored_dataset

    def test_get_connection_config_success(
        self, connection_service, db, connection_config
    ):
        """Test successful retrieval of connection config."""

        result = connection_service.get_connection_config(connection_config.key)

        assert result == connection_config

    def test_get_connection_config_not_found(self, connection_service, db):
        """Test connection config not found raises exception."""

        with pytest.raises(
            ConnectionNotFoundException
        ):  # Should raise appropriate exception
            connection_service.get_connection_config("nonexistent_connection")

    def test_update_secrets_postgres(
        self,
        connection_service: ConnectionService,
        db: Session,
        connection_config: ConnectionConfig,
    ):
        """Test that updating PostgreSQL secrets creates an audit event."""
        # Test data
        new_secrets = {"password": "new_password"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
            merge_with_existing=True,
        )

        patched_secrets = {**connection_config.secrets, **new_secrets}

        # Verify return value
        assert connection_config.secrets == patched_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == connection_config.key
        assert (
            events[0].description
            == f"Connection secrets updated: postgres connection '{connection_config.key}' - password"
        )
        assert events[0].event_details["secrets"]["password"] == "**********"

    def test_update_secrets_saas(
        self,
        connection_service: ConnectionService,
        db: Session,
        stripe_connection_config: ConnectionConfig,
    ):
        """Test that updating SaaS connector secrets creates an audit event."""
        # Test data
        new_secrets = {"api_key": "new_api_key", "domain": "new_domain"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=stripe_connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
            merge_with_existing=True,
        )

        patched_secrets = {**stripe_connection_config.secrets, **new_secrets}

        # Verify return value
        assert stripe_connection_config.secrets == patched_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {stripe_connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", stripe_connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == stripe_connection_config.key
        assert (
            events[0].description
            == f"Connection secrets updated: stripe connection '{stripe_connection_config.key}' - api_key, domain"
        )
        # all secrets are masked since custom connection has no secret schema
        assert events[0].event_details["secrets"]["api_key"] == "**********"
        assert events[0].event_details["secrets"]["domain"] == "new_domain"

    def test_update_secrets_saas_no_merge(
        self,
        connection_service: ConnectionService,
        db: Session,
        stripe_connection_config: ConnectionConfig,
    ):
        """Test that updating SaaS connector secrets creates an audit event."""
        # Test data
        new_secrets = {"api_key": "new_api_key", "domain": "new_domain"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=stripe_connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
        )

        # Verify return value
        assert stripe_connection_config.secrets == new_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {stripe_connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", stripe_connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == stripe_connection_config.key
        assert (
            events[0].description
            == f"Connection secrets updated: stripe connection '{stripe_connection_config.key}' - api_key, domain"
        )
        # all secrets are masked since custom connection has no secret schema
        assert events[0].event_details["secrets"]["api_key"] == "**********"
        assert events[0].event_details["secrets"]["domain"] == "new_domain"

    def test_update_secrets_saas_custom(
        self,
        connection_service: ConnectionService,
        db: Session,
        saas_external_example_connection_config: ConnectionConfig,
    ):
        """Test that updating SaaS connector secrets creates an audit event."""
        # Test data
        new_secrets = {"api_key": "new_api_key", "domain": "new_domain"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=saas_external_example_connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
            merge_with_existing=True,
        )

        patched_secrets = {
            **saas_external_example_connection_config.secrets,
            **new_secrets,
        }

        # Verify return value
        assert saas_external_example_connection_config.secrets == patched_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {saas_external_example_connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", saas_external_example_connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert (
            events[0].resource_identifier == saas_external_example_connection_config.key
        )
        assert (
            events[0].description
            == f"Connection secrets updated: custom connection '{saas_external_example_connection_config.key}' - api_key, domain"
        )
        # all secrets are masked since custom connection has no secret schema
        assert events[0].event_details["secrets"]["api_key"] == "**********"
        assert events[0].event_details["secrets"]["domain"] == "**********"

    def test_create_connection_config_new(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that creating a new connection config creates an audit event with all fields."""

        # Create a new connection config
        config = CreateConnectionConfigurationWithSecrets(
            key="test_postgres_new",
            name="Test PostgreSQL New",
            connection_type="postgres",
            access="write",
            description="A test postgres connection",
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection was created
        assert result.key == "test_postgres_new"
        assert result.name == "Test PostgreSQL New"
        assert result.connection_type.value == "postgres"

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_created.value
        assert events[0].resource_identifier == result.key
        assert (
            events[0].description
            == f"Connection created: postgres connection '{result.key}'"
        )

        # Verify all auditable fields are included (changed_fields=None means include all)
        config_changes = events[0].event_details["configuration_changes"]
        assert "key" in config_changes
        assert "name" in config_changes
        assert "connection_type" in config_changes
        assert "access" in config_changes
        assert "description" in config_changes
        assert config_changes["key"] == "test_postgres_new"
        assert config_changes["name"] == "Test PostgreSQL New"
        assert config_changes["connection_type"] == "postgres"
        assert config_changes["access"] == "write"
        assert config_changes["description"] == "A test postgres connection"

        assert "secrets" not in config_changes

    def test_update_connection_config_selective_auditing(
        self,
        connection_service: ConnectionService,
        db: Session,
        connection_config: ConnectionConfig,
    ):
        """Test that updating a connection config creates an audit event with only changed fields."""

        # Update only name and description
        config = CreateConnectionConfigurationWithSecrets(
            key=connection_config.key,
            name="Updated PostgreSQL Name",
            description="Updated description",
            connection_type=connection_config.connection_type.value,
            access=connection_config.access.value,
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection was updated
        assert result.name == "Updated PostgreSQL Name"
        assert result.description == "Updated description"

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_updated.value
        assert events[0].resource_identifier == result.key
        assert (
            events[0].description
            == f"Connection updated: postgres connection '{result.key}'"
        )

        # Verify only changed fields are included
        config_changes = events[0].event_details["configuration_changes"]
        assert "name" in config_changes
        assert "description" in config_changes
        assert config_changes["name"] == "Updated PostgreSQL Name"
        assert config_changes["description"] == "Updated description"

        # Verify unchanged fields are NOT included
        assert "key" not in config_changes
        assert "connection_type" not in config_changes
        assert "access" not in config_changes
        assert "secrets" not in config_changes

    def test_update_connection_config_no_changes(
        self,
        connection_service: ConnectionService,
        db: Session,
        connection_config: ConnectionConfig,
    ):
        """Test that updating a connection config with no changes creates no audit event."""

        # Update with same values (no actual changes)
        config = CreateConnectionConfigurationWithSecrets(
            key=connection_config.key,
            name=connection_config.name,
            description=connection_config.description,
            connection_type=connection_config.connection_type.value,
            access=connection_config.access.value,
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection exists but no changes
        assert result.key == connection_config.key
        assert result.name == connection_config.name

        # Verify NO audit event was created (no changes detected)
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 0

    def test_update_connection_config_saas_selective(
        self,
        connection_service: ConnectionService,
        db: Session,
        saas_example_connection_config: ConnectionConfig,
    ):
        """Test that updating a SaaS connection config creates an audit event with only changed fields."""

        # Get the SaaS connector type from the saas_config
        saas_config = saas_example_connection_config.get_saas_config()
        saas_connector_type = saas_config.type if saas_config else None

        # Update only the name
        config = CreateConnectionConfigurationWithSecrets(
            key=saas_example_connection_config.key,
            name="Updated SaaS Name",
            connection_type=saas_example_connection_config.connection_type.value,
            access=saas_example_connection_config.access.value,
            saas_connector_type=saas_connector_type,
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection was updated
        assert result.name == "Updated SaaS Name"

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_updated.value
        assert events[0].resource_identifier == result.key
        assert (
            events[0].description
            == f"Connection updated: custom connection '{result.key}'"
        )

        # Verify only changed fields are included
        config_changes = events[0].event_details["configuration_changes"]
        assert "name" in config_changes
        assert config_changes["name"] == "Updated SaaS Name"

        # Verify unchanged fields are NOT included (including saas_config)
        assert "key" not in config_changes
        assert "connection_type" not in config_changes
        assert "access" not in config_changes
        assert "saas_config" not in config_changes

    def test_oauth_config_audit_event_creation(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that updating OAuth config creates an audit event for secrets."""

        # Create an HTTPS connection config
        https_connection = ConnectionConfig.create(
            db,
            data={
                "key": "test_https_oauth",
                "name": "Test HTTPS OAuth",
                "connection_type": ConnectionType.https,
                "access": AccessLevel.write,
                "secrets": {"url": "https://api.example.com/webhook"},
            },
        )

        # Create OAuth config data
        oauth_config_data = OAuthConfigSchema(
            grant_type="client_credentials",
            token_url="https://api.example.com/oauth/token",
            client_id="test_client_id",
            client_secret="test_client_secret_123",
            scope="webhook:write privacy:read",
        )

        # Simulate the OAuth config update (like the endpoint does)
        https_connection.oauth_config = OAuthConfig(
            **oauth_config_data.model_dump(mode="json")
        )
        https_connection.save(db=db)

        # Create the audit event (like the endpoint does)
        connection_service.create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            https_connection,
            oauth_config_data.model_dump(exclude_unset=True),
        )

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", https_connection.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == https_connection.key
        assert (
            events[0].description
            == f"Connection secrets updated: https connection '{https_connection.key}' - grant_type, token_url, scope, client_id, client_secret"
        )

        # Verify OAuth secrets are in the audit event
        secrets_details = events[0].event_details["secrets"]
        assert "client_secret" in secrets_details
        assert "client_id" in secrets_details
        assert "token_url" in secrets_details
        assert "grant_type" in secrets_details
        assert "scope" in secrets_details

        # Verify proper masking based on OAuth schema - only client_secret is sensitive
        assert secrets_details["client_secret"] == "**********"  # Masked (sensitive)
        assert (
            secrets_details["client_id"] == "test_client_id"
        )  # Not masked (not sensitive)
        assert (
            secrets_details["token_url"] == "https://api.example.com/oauth/token"
        )  # Not masked
        assert secrets_details["grant_type"] == "client_credentials"  # Not masked
        assert secrets_details["scope"] == "webhook:write privacy:read"  # Not masked

        # Clean up
        https_connection.delete(db)

    def test_https_connection_secrets_vs_oauth_secrets_masking(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that HTTPS connection secrets and OAuth secrets are masked differently."""

        # Create an HTTPS connection config with OAuth
        https_connection = ConnectionConfig.create(
            db,
            data={
                "key": "test_https_mixed_secrets",
                "name": "Test HTTPS Mixed Secrets",
                "connection_type": ConnectionType.https,
                "access": AccessLevel.write,
                "secrets": {
                    "url": "https://api.example.com/webhook",
                    "authorization": "Bearer secret_token",
                },
            },
        )

        # Add OAuth config
        oauth_config_data = OAuthConfigSchema(
            grant_type="client_credentials",
            token_url="https://api.example.com/oauth/token",
            client_id="test_client_id",
            client_secret="test_client_secret_123",
        )
        https_connection.oauth_config = OAuthConfig(
            **oauth_config_data.model_dump(mode="json")
        )
        https_connection.save(db=db)

        # Test 1: Update OAuth secrets - should use OAuth schema
        connection_service.create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            https_connection,
            {"client_secret": "new_client_secret", "client_id": "new_client_id"},
        )

        # Test 2: Update connection secrets - should use HTTPS schema (not OAuth schema)
        connection_service.create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            https_connection,
            {
                "url": "https://new-api.example.com/webhook",
                "authorization": "Bearer new_token",
            },
        )

        # Verify both audit events were created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", https_connection.key
        )
        assert len(events) == 2

        # Find OAuth secrets event and connection secrets event
        oauth_event = next(e for e in events if "client_secret" in str(e.event_details))
        connection_event = next(e for e in events if "url" in str(e.event_details))

        # Verify OAuth secrets masking (only client_secret should be masked)
        oauth_secrets = oauth_event.event_details["secrets"]
        assert oauth_secrets["client_secret"] == "**********"  # Masked
        assert oauth_secrets["client_id"] == "new_client_id"  # Not masked

        # Verify connection secrets masking (should use HTTPS schema, not OAuth schema)
        connection_secrets = connection_event.event_details["secrets"]
        # Since there's no HTTPS connection schema, all secrets are masked for security
        assert connection_secrets["url"] == "**********"
        assert connection_secrets["authorization"] == "**********"

        # Clean up
        https_connection.delete(db)

    def test_connection_deletion_audit_event(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that connection deletion creates a simplified audit event."""

        # Create a connection config
        connection_config = ConnectionConfig.create(
            db,
            data={
                "key": "test_deletion_audit",
                "name": "Test Deletion Audit",
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.write,
                "secrets": {"host": "localhost", "port": 5432},
            },
        )

        connection_service.create_connection_audit_event(
            EventAuditType.connection_deleted,
            connection_config,
        )

        # Verify audit event was created with simplified structure
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_deleted.value
        assert events[0].resource_identifier == connection_config.key
        assert (
            events[0].description
            == f"Connection deleted: postgres connection '{connection_config.key}'"
        )

        # Verify simplified event details for deletion - only operation_type, no configuration_changes
        event_details = events[0].event_details
        assert event_details["operation_type"] == "deleted"
        assert "configuration_changes" not in event_details

        # Clean up
        connection_config.delete(db)

    def _get_template_yaml(self) -> str:
        """Helper to get the base template YAML to save space in tests."""
        return dedent(
            """
            dataset:
            - fides_key: <instance_fides_key>
              name: Template Dataset
              description: Dataset from template
              collections:
              - name: products
                fields:
                - name: product_id
                  data_categories: [user.unique_id]
                  fides_meta:
                    data_type: string
                    primary_key: True
                - name: customer_id
                  data_categories: [user.preferences]
                  fides_meta:
                    data_type: integer
                - name: email
                  data_categories: [user.contact.email]
                  fides_meta:
                    data_type: string
                - name: address
                  fides_meta:
                    data_type: object
                  fields:
                    - name: street
                      data_categories: [user.contact.address.street]
                      fides_meta:
                        data_type: string
                    - name: city
                      data_categories: [user.contact.address]
                      fides_meta:
                        data_type: string
        """
        ).strip()

    @pytest.mark.parametrize(
        "customer_modifications,expected_attributes",
        [
            (
                # Scenario: Customer modified 'customer_id' category and 'city' category
                {
                    "customer_id_category": ["system.operations"],
                    "city_category": ["user.contact.address.city"],
                },
                {
                    "product_id_type": "string",  # From template
                    "customer_id_category": ["system.operations"],  # From customer
                    "city_category": ["user.contact.address.city"],  # From customer
                    "street_category": ["user.contact.address.street"],  # From template
                },
            ),
        ],
    )
    def test_upsert_dataset_with_merge(
        self,
        connection_service: ConnectionService,
        db: Session,
        stored_dataset: Dict[str, Any],
        customer_modifications: Dict[str, Any],
        expected_attributes: Dict[str, Any],
    ):
        """Test upsert_dataset_config_from_template with datasets from template, connection config, and SaasTemplateDataset table."""

        # Dataset 1: From template
        upcoming_dataset_yaml = self._get_template_yaml()

        # Dataset 2: From connection config (existing DatasetConfig) (customer dataset)
        customer_dataset = copy.deepcopy(stored_dataset)
        customer_dataset["fides_key"] = "test_instance_key"
        customer_dataset["name"] = "SaaS Template Dataset"
        customer_dataset["description"] = "Dataset from connection config"

        # Apply customer modifications
        products_collection = customer_dataset["collections"][0]
        products_fields_map = {f["name"]: f for f in products_collection["fields"]}

        if "customer_id_category" in customer_modifications:
            products_fields_map["customer_id"]["data_categories"] = (
                customer_modifications["customer_id_category"]
            )

        if "city_category" in customer_modifications:
            address_fields = {
                f["name"]: f for f in products_fields_map["address"]["fields"]
            }
            address_fields["city"]["data_categories"] = customer_modifications[
                "city_category"
            ]

        # Create connection config
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_connection",
                "name": "Test Connection",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "saas_config": {
                    "fides_key": "test_instance_key",
                    "name": "Test Connector",
                    "type": "test_connector",
                    "description": "Test connector",
                    "version": "0.1.0",
                    "connector_params": [],
                    "client_config": {"protocol": "https", "host": "api.example.com"},
                    "test_request": {"method": "GET", "path": "/test"},
                    "endpoints": [],
                },
            },
        )

        # Create existing DatasetConfig
        DatasetConfig.create_or_update(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_instance_key",
                "dataset": customer_dataset,
            },
        )

        # Create SaasTemplateDataset entry
        SaasTemplateDataset.get_or_create(
            db=db,
            connector_type="test_connector",
            dataset_json=stored_dataset,
        )

        # Create ConnectorTemplate
        connector_template = ConnectorTemplate(
            config=dedent(
                """
                saas_config:
                  fides_key: <instance_fides_key>
                  name: Test Connector
                  type: test_connector
                  description: Test connector
                  version: 1.0.0
                  connector_params: []
                  client_config:
                    protocol: https
                    host: api.example.com
                  test_request:
                    method: GET
                    path: /test
                  endpoints: []
            """
            ).strip(),
            dataset=upcoming_dataset_yaml,
            human_readable="Test Connector",
            authorization_required=False,
            supported_actions=[ActionType.access, ActionType.erasure],
            category=ConnectionCategory.ANALYTICS,
        )

        # Execute
        result_dataset_config = connection_service.upsert_dataset_config_from_template(
            connection_config=connection_config,
            template=connector_template,
            template_values=SaasConnectionTemplateValues(
                secrets={}, instance_key="test_instance_key"
            ),
        )

        # Verify
        ctl_dataset = result_dataset_config.ctl_dataset
        assert ctl_dataset.fides_key == "test_instance_key"

        # Verify fields
        products = next(c for c in ctl_dataset.collections if c["name"] == "products")
        fields_map = {f["name"]: f for f in products["fields"]}

        assert (
            fields_map["product_id"]["fides_meta"]["data_type"]
            == expected_attributes["product_id_type"]
        )
        assert (
            fields_map["customer_id"]["data_categories"]
            == expected_attributes["customer_id_category"]
        )

        address_fields = {f["name"]: f for f in fields_map["address"]["fields"]}
        assert (
            address_fields["city"]["data_categories"]
            == expected_attributes["city_category"]
        )
        assert (
            address_fields["street"]["data_categories"]
            == expected_attributes["street_category"]
        )

        # Clean up
        connection_config.delete(db)

    def _create_custom_field(self, name: str = "custom_attribute") -> Dict[str, Any]:
        """Helper method to create a custom field for testing."""
        return {
            "name": name,
            "description": None,
            "data_categories": ["user.preferences"],
            "fides_meta": {
                "custom_request_field": None,
                "data_type": "boolean",
                "identity": None,
                "length": None,
                "masking_strategy_override": None,
                "primary_key": True,
                "read_only": True,
                "redact": None,
                "references": None,
                "return_all_elements": None,
            },
            "fields": None,
        }

    def _apply_dataset_changes(
        self, dataset: Dict[str, Any], changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Helper method to apply changes to a dataset."""
        modified_dataset = copy.deepcopy(dataset)
        modified_dataset["fides_key"] = "test_instance_key"

        if "delete_fields" in changes:
            for field_index in sorted(changes["delete_fields"], reverse=True):
                del modified_dataset["collections"][0]["fields"][field_index]

        if "field_changes" in changes:
            for field_name, field_changes in changes["field_changes"].items():
                field = next(
                    f
                    for f in modified_dataset["collections"][0]["fields"]
                    if f["name"] == field_name
                )
                if "data_type" in field_changes:
                    field["fides_meta"]["data_type"] = field_changes["data_type"]
                if "data_categories" in field_changes:
                    field["data_categories"] = field_changes["data_categories"]

        if "add_fields" in changes:
            for field_data in changes["add_fields"]:
                modified_dataset["collections"][0]["fields"].append(field_data)

        if "clear_fields" in changes and changes["clear_fields"]:
            modified_dataset["collections"][0]["fields"] = []

        return modified_dataset

    @pytest.mark.parametrize(
        "scenario_name,upcoming_changes,customer_changes,expected_fields,expected_field_count",
        [
            (
                "basic_merge_with_priority",
                {
                    "delete_fields": [2],  # delete email field
                    "field_changes": {
                        "product_id": {"data_type": "string"},
                        "address": {"data_categories": ["user.contact.email"]},
                    },
                },
                {
                    "field_changes": {
                        "customer_id": {"data_categories": ["user.name"]},
                        "product_id": {
                            "data_type": "object"
                        },  # should override upcoming change
                    },
                    "add_fields": ["custom_field"],
                },
                {
                    "customer_id": {"data_categories": ["user.name"]},
                    "product_id": {"data_type": "object"},
                    "address": {"data_categories": ["user.contact.email"]},
                    "custom_attribute": {"exists": True},
                },
                4,
            ),
            (
                "customer_deletes_all_fields",
                {"delete_fields": [2]},  # delete email field
                {"clear_fields": True},
                {
                    "email": {"exists": False},
                    "custom_attribute": {"exists": False},
                    "product_id": {"exists": True},
                    "customer_id": {"exists": True},
                    "address": {"exists": True},
                },
                3,
            ),
            (
                "integration_deletes_all_fields",
                {"clear_fields": True},
                {"add_fields": ["custom_field"]},
                {
                    "custom_attribute": {"exists": True},
                },
                1,
            ),
        ],
    )
    def test_merge_dataset_fields(
        self,
        connection_service: ConnectionService,
        db: Session,
        stored_dataset: Dict[str, Any],
        scenario_name: str,
        upcoming_changes: Dict[str, Any],
        customer_changes: Dict[str, Any],
        expected_fields: Dict[str, Any],
        expected_field_count: int,
    ):
        """Test merge datasets function for various field change scenarios."""

        # Apply changes to create test datasets
        upcoming_dataset = self._apply_dataset_changes(stored_dataset, upcoming_changes)

        # Handle custom field addition for customer changes
        if (
            "add_fields" in customer_changes
            and "custom_field" in customer_changes["add_fields"]
        ):
            customer_changes = copy.deepcopy(customer_changes)
            customer_changes["add_fields"] = [self._create_custom_field()]

        customer_dataset = self._apply_dataset_changes(stored_dataset, customer_changes)

        # Execute merge
        result_dataset_dict: Dict[str, Any] = merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # Verify results
        products_collection = result_dataset_dict["collections"][0]
        products_fields_map = {f["name"]: f for f in products_collection["fields"]}

        assert (
            len(products_fields_map) == expected_field_count
        ), f"Expected {expected_field_count} fields, got {len(products_fields_map)}"

        # Check specific field expectations
        for field_name, expectations in expected_fields.items():
            if expectations.get("exists", True):
                assert (
                    field_name in products_fields_map
                ), f"Field {field_name} should exist"
                field = products_fields_map[field_name]

                if "data_categories" in expectations:
                    assert field["data_categories"] == expectations["data_categories"]
                if "data_type" in expectations:
                    assert field["fides_meta"]["data_type"] == expectations["data_type"]
            else:
                assert (
                    field_name not in products_fields_map
                ), f"Field {field_name} should not exist"

    def test_merge_dataset_fields_no_changes_preserves_state(
        self,
        connection_service: ConnectionService,
        db: Session,
        stored_dataset: Dict[str, Any],
    ):
        """Test that when no changes are made, the merged dataset state is preserved."""
        # First create a merged dataset with changes
        upcoming_changes = {
            "delete_fields": [2],
            "field_changes": {"product_id": {"data_type": "string"}},
        }
        customer_changes = {
            "field_changes": {"customer_id": {"data_categories": ["user.name"]}},
            "add_fields": ["custom_field"],
        }

        upcoming_dataset = self._apply_dataset_changes(stored_dataset, upcoming_changes)
        customer_changes_with_field = copy.deepcopy(customer_changes)
        customer_changes_with_field["add_fields"] = [self._create_custom_field()]
        customer_dataset = self._apply_dataset_changes(
            stored_dataset, customer_changes_with_field
        )

        # Get initial merged result
        initial_result = merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # Now test with no changes (upcoming dataset becomes stored, no new changes)
        no_change_result = merge_datasets(
            stored_dataset=upcoming_dataset,
            customer_dataset=initial_result,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # Verify preservation of merged state
        assert no_change_result["fides_key"] == "test_instance_key"
        assert no_change_result["name"] == "Template Dataset"
        assert no_change_result["description"] == "Dataset from template"

        fields_by_name = {
            field["name"]: field
            for field in no_change_result["collections"][0]["fields"]
        }
        expected_field_names = {
            "product_id",
            "customer_id",
            "address",
            "custom_attribute",
        }
        assert set(fields_by_name.keys()) == expected_field_names

    def _create_test_collection(
        self, name: str, category: str = "system.operations"
    ) -> Dict[str, Any]:
        """Helper method to create a test collection."""
        return {
            "name": name,
            "data_categories": None,
            "description": None,
            "fides_meta": None,
            "fields": [
                {
                    "name": f"{name}_id",
                    "description": None,
                    "data_categories": [category],
                    "fides_meta": {
                        "custom_request_field": None,
                        "data_type": (
                            "integer" if category == "system.operations" else "string"
                        ),
                        "identity": None,
                        "length": None,
                        "masking_strategy_override": None,
                        "primary_key": True,
                        "read_only": None,
                        "redact": None,
                        "references": None,
                        "return_all_elements": None,
                    },
                    "fields": None,
                },
            ],
        }

    @pytest.mark.parametrize(
        "integration_collections_to_add,customer_collections_to_add,expected_collection_names",
        [
            (
                ["orders"],  # Integration adds 'orders'
                ["custom_data"],  # Customer adds 'custom_data'
                {
                    "products",
                    "orders",
                },  # Expect 'products' (base) + 'orders', but NOT 'custom_data'
            ),
            (
                [],  # Integration adds nothing
                ["custom_data"],  # Customer adds 'custom_data'
                {"products"},  # Expect only base 'products'
            ),
            (
                ["orders", "logs"],  # Integration adds multiple
                [],  # Customer adds nothing
                {"products", "orders", "logs"},  # Expect all integration additions
            ),
        ],
    )
    def test_merge_collections(
        self,
        connection_service: ConnectionService,
        db: Session,
        stored_dataset: Dict[str, Any],
        integration_collections_to_add: list[str],
        customer_collections_to_add: list[str],
        expected_collection_names: set[str],
    ):
        """Test merge datasets function for collection additions/removals."""

        # INTEGRATION UPDATE
        upcoming_dataset = copy.deepcopy(stored_dataset)
        upcoming_dataset["fides_key"] = "test_instance_key"

        for col_name in integration_collections_to_add:
            upcoming_dataset["collections"].append(
                self._create_test_collection(col_name)
            )

        # CUSTOMER CHANGES
        customer_dataset = copy.deepcopy(stored_dataset)
        for col_name in customer_collections_to_add:
            customer_dataset["collections"].append(
                self._create_test_collection(col_name, category="user.unique_id")
            )

        # Merge the datasets
        result_dataset_dict: Dict[str, Any] = merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # Verify results
        result_collection_names = {
            col["name"] for col in result_dataset_dict["collections"]
        }
        assert result_collection_names == expected_collection_names

        # Verify specific collection properties for integration additions
        for col_name in integration_collections_to_add:
            if col_name in result_collection_names:
                collection = next(
                    c
                    for c in result_dataset_dict["collections"]
                    if c["name"] == col_name
                )
                assert len(collection["fields"]) == 1
                assert collection["fields"][0]["name"] == f"{col_name}_id"
                assert collection["fields"][0]["data_categories"] == [
                    "system.operations"
                ]

        # Verify dataset-level properties are preserved
        assert result_dataset_dict["fides_key"] == "test_instance_key"
        assert result_dataset_dict["name"] == upcoming_dataset["name"]
        assert result_dataset_dict["description"] == upcoming_dataset["description"]
