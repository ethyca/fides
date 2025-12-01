"""Tests for ConnectionService including event auditing functionality."""

import copy
from re import A
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

    def test_upsert_dataset_with_merge(
        self,
        connection_service: ConnectionService,
        db: Session,
        stored_dataset: Dict[str, Any],
    ):
        """Test upsert_dataset_config_from_template with datasets from template, connection config, and SaasTemplateDataset table."""
        # Dataset 1: From template (passed to function) (upcoming dataset)
        upcoming_dataset = dedent(
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

        # Dataset 2: From connection config (existing DatasetConfig) (customer dataset)
        customer_dataset = copy.deepcopy(stored_dataset)
        customer_dataset["fides_key"] = "test_instance_key"
        customer_dataset["name"] = "SaaS Template Dataset"
        customer_dataset["description"] = "Dataset from connection config"
        products_collection = customer_dataset["collections"][0]
        products_fields_map = {f["name"]: f for f in products_collection["fields"]}
        products_fields_map["customer_id"]["data_categories"] = ["system.operations"]
        address_fields_map = {
            f["name"]: f for f in products_fields_map["address"]["fields"]
        }
        address_fields_map["city"]["data_categories"] = ["user.contact.address.city"]

        # Dataset 3: From SaasTemplateDataset table (stored dataset) - using fixture

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
                    "description": "A test connector for testing dataset merging",
                    "version": "0.1.0",
                    "connector_params": [],
                    "client_config": {
                        "protocol": "https",
                        "host": "api.example.com",
                    },
                    "test_request": {
                        "method": "GET",
                        "path": "/test",
                    },
                    "endpoints": [],
                },
            },
        )

        # Create existing DatasetConfig from connection config
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
                  description: A test connector for testing dataset merging
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
            dataset=upcoming_dataset,
            human_readable="Test Connector",
            authorization_required=False,
            supported_actions=[ActionType.access, ActionType.erasure],
            category=ConnectionCategory.ANALYTICS,
        )

        # Create template values
        template_values = SaasConnectionTemplateValues(
            secrets={},
            instance_key="test_instance_key",
        )

        # Execute the function
        result_dataset_config = connection_service.upsert_dataset_config_from_template(
            connection_config=connection_config,
            template=connector_template,
            template_values=template_values,
        )

        ctl_dataset = result_dataset_config.ctl_dataset
        result_dataset_dict = {
            "fides_key": ctl_dataset.fides_key,
            "name": ctl_dataset.name,
            "description": ctl_dataset.description,
            "data_categories": ctl_dataset.data_categories,
            "collections": ctl_dataset.collections,
            "fides_meta": ctl_dataset.fides_meta,
        }

        # Verify dataset information
        assert result_dataset_config is not None
        assert result_dataset_dict["fides_key"] == "test_instance_key"
        assert result_dataset_dict["name"] == "Template Dataset"
        assert result_dataset_dict["description"] == "Dataset from template"

        products_collection = result_dataset_dict["collections"][0]
        assert len(products_collection["fields"]) == 4
        products_fields_map = {f["name"]: f for f in products_collection["fields"]}

        # Expected result after merging:
        # INTEGRATION UPDATE CHANGES (preserved):
        # - products.product_id: data_type changed from integer to string
        assert products_fields_map["product_id"]["fides_meta"]["data_type"] == "string"

        # CUSTOMER CHANGES (preserved):
        # - products.customer_id: data_categories changed from [user.unique_id] to [system.operations]. (takes priority over integration update change [user.preferences])
        # - products.address.city: data_categories changed from [user.contact.address] to [user.contact.address.city]
        assert products_fields_map["customer_id"]["data_categories"] == [
            "system.operations"
        ]
        address_fields_map = {
            f["name"]: f for f in products_fields_map["address"]["fields"]
        }
        assert len(address_fields_map) == 2
        assert address_fields_map["city"]["data_categories"] == [
            "user.contact.address.city"
        ]
        assert address_fields_map["street"]["data_categories"] == [
            "user.contact.address.street"
        ]

    def test_merge_dataset_fields(
        self,
        connection_service: ConnectionService,
        db: Session,
        stored_dataset: Dict[str, Any],
    ):
        """Test merge datasets function for fields changes"""

        # Expected result: merged dataset from all three sources

        # INTEGRATION UPDATE CHANGES
        upcoming_dataset = copy.deepcopy(stored_dataset)
        upcoming_dataset["fides_key"] = "test_instance_key"
        del upcoming_dataset["collections"][0]["fields"][2]  # delete email field
        # change data type of product_id field
        upcoming_dataset["collections"][0]["fields"][0]["fides_meta"][
            "data_type"
        ] = "string"
        # change data category of address field
        upcoming_dataset["collections"][0]["fields"][2]["data_categories"] = [
            "user.contact.email"
        ]

        # CUSTOMER CHANGES
        # customer changed the data categories of the customer_id field
        customer_dataset = copy.deepcopy(stored_dataset)
        customer_dataset["collections"][0]["fields"][1]["data_categories"] = [
            "user.name"
        ]
        # changed data type of product_id field
        customer_dataset["collections"][0]["fields"][0]["fides_meta"][
            "data_type"
        ] = "object"

        new_field = {
            "name": "custom_attribute",
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
        # add new field to customer dataset
        customer_dataset["collections"][0]["fields"].append(new_field)

        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # Expected result:
        # - products collection: email field deleted (upcoming dataset change)
        # - products collection: customer_id field data categories changed (customer dataset change)
        # - products collection: product_id field data type changed from integer to object (customer dataset change took priority over upcoming dataset change)
        # - products collection: address field data categories changed from None to ["user.contact.email"] (customer dataset change)
        # - products collection: custom_attribute field added (customer dataset change)
        products_collection = result_dataset_dict["collections"][0]
        products_fields_map = {f["name"]: f for f in products_collection["fields"]}
        assert len(products_fields_map) == 4
        assert "email" not in products_fields_map
        assert products_fields_map["customer_id"]["data_categories"] == ["user.name"]
        assert products_fields_map["product_id"]["fides_meta"]["data_type"] == "object"
        assert products_fields_map["address"]["data_categories"] == [
            "user.contact.email"
        ]
        assert products_fields_map["custom_attribute"]

        # check that by making no changes the customer dataset stays the same
        stored_dataset = copy.deepcopy(
            upcoming_dataset
        )  # upcoming dataset is now the stored dataset
        upcoming_dataset = copy.deepcopy(stored_dataset)  # no changes were made
        customer_dataset = copy.deepcopy(result_dataset_dict)
        expected_dataset = copy.deepcopy(result_dataset_dict)

        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # Verify that when no changes are made, the result preserves the merged dataset
        # Check dataset-level properties
        assert result_dataset_dict["fides_key"] == "test_instance_key"
        assert result_dataset_dict["name"] == "Template Dataset"
        assert result_dataset_dict["description"] == "Dataset from template"

        # Check collections structure
        assert len(result_dataset_dict["collections"]) == 1
        products_collection = result_dataset_dict["collections"][0]

        # Check that all expected fields are present (order-independent)
        fields_by_name = {
            field["name"]: field for field in products_collection["fields"]
        }
        expected_field_names = {
            "product_id",
            "customer_id",
            "address",
            "custom_attribute",
        }
        assert set(fields_by_name.keys()) == expected_field_names

        # Verify specific field properties from the previous merge
        assert fields_by_name["customer_id"]["data_categories"] == ["user.name"]
        assert fields_by_name["product_id"]["fides_meta"]["data_type"] == "object"
        assert fields_by_name["address"]["data_categories"] == ["user.contact.email"]
        assert fields_by_name["custom_attribute"]["data_categories"] == [
            "user.preferences"
        ]

        # test that the customer can delete a field they added but not fields that exist in the official dataset
        customer_dataset_no_fields = copy.deepcopy(customer_dataset)
        customer_dataset_no_fields["collections"][0]["fields"] = []

        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset_no_fields,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # since the customer deleted all its fields
        # Their changes are now lost and we will use what is in the upcoming dataset
        products_collection = result_dataset_dict["collections"][0]
        assert len(products_collection["fields"]) == 3
        products_fields_map = {f["name"]: f for f in products_collection["fields"]}
        assert "email" not in products_fields_map
        assert "custom_attribute" not in products_fields_map
        assert products_fields_map["product_id"]
        assert products_fields_map["customer_id"]
        assert products_fields_map["address"]

        # test that an integration update deletes all fields except the ones that were added by the customer
        upcoming_dataset_no_fields = copy.deepcopy(upcoming_dataset)
        upcoming_dataset_no_fields["collections"][0]["fields"] = []
        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset_no_fields,
            instance_key="test_instance_key",
        )

        # only the customer added field is present in products collection
        products_collection = result_dataset_dict["collections"][0]
        assert len(products_collection["fields"]) == 1
        products_fields_map = {f["name"]: f for f in products_collection["fields"]}
        assert products_fields_map["custom_attribute"]

        customer_dataset_no_fields = copy.deepcopy(result_dataset_dict)
        # Test that once we delete the customer field the collection has no remaining fields
        customer_dataset_no_fields["collections"][0]["fields"] = []
        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset_no_fields,
            upcoming_dataset=upcoming_dataset_no_fields,
            instance_key="test_instance_key",
        )

        assert len(result_dataset_dict["collections"][0]["fields"]) == 0

    def test_merge_collections(
        self,
        connection_service: ConnectionService,
        db: Session,
        stored_dataset: Dict[str, Any],
    ):
        """Test that integration update added collections are preserved whereas customer added collections are not"""

        # INTEGRATION UPDATE - add a new collection called "orders"
        upcoming_dataset = copy.deepcopy(stored_dataset)
        upcoming_dataset["fides_key"] = "test_instance_key"

        integration_added_collection = {
            "name": "orders",
            "data_categories": None,
            "description": None,
            "fides_meta": None,
            "fields": [
                {
                    "name": "order_id",
                    "description": None,
                    "data_categories": ["system.operations"],
                    "fides_meta": {
                        "custom_request_field": None,
                        "data_type": "integer",
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
        upcoming_dataset["collections"].append(integration_added_collection)

        # CUSTOMER CHANGES - add a new collection called "custom_data"
        customer_dataset = copy.deepcopy(stored_dataset)
        customer_added_collection = {
            "name": "custom_data",
            "data_categories": None,
            "description": None,
            "fides_meta": None,
            "fields": [
                {
                    "name": "custom_id",
                    "description": None,
                    "data_categories": ["user.unique_id"],
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
                }
            ],
        }
        customer_dataset["collections"].append(customer_added_collection)

        # Merge the datasets
        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # Expected result:
        # - products collection: preserved (original collection)
        # - orders collection: added (integration update added collection - should be preserved)
        # - custom_data collection: NOT added (customer added collection - should NOT be preserved)

        # Verify that the result contains exactly 2 collections (products + orders, but NOT custom_data)
        assert len(result_dataset_dict["collections"]) == 2
        collection_names = [col["name"] for col in result_dataset_dict["collections"]]
        assert "products" in collection_names
        assert "orders" in collection_names
        assert "custom_data" not in collection_names

        # Verify the products collection is preserved correctly (original collection)
        products_collection = next(
            c for c in result_dataset_dict["collections"] if c["name"] == "products"
        )
        assert products_collection["data_categories"] is None
        assert products_collection["description"] is None
        assert len(products_collection["fields"]) == 4

        # Verify the orders collection was added correctly (integration update added collection)
        orders_collection = next(
            c for c in result_dataset_dict["collections"] if c["name"] == "orders"
        )
        assert orders_collection["data_categories"] is None
        assert orders_collection["description"] is None
        assert len(orders_collection["fields"]) == 1
        assert orders_collection["fields"][0]["name"] == "order_id"
        assert orders_collection["fields"][0]["data_categories"] == [
            "system.operations"
        ]
        assert orders_collection["fields"][0]["fides_meta"]["primary_key"] is True

        # Verify dataset-level properties are preserved
        assert (
            result_dataset_dict["fides_key"] == "test_instance_key"
        )  # Should use the instance_key, not the placeholder
        assert result_dataset_dict["name"] == upcoming_dataset["name"]
        assert result_dataset_dict["description"] == upcoming_dataset["description"]
