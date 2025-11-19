"""Tests for ConnectionService including event auditing functionality."""

import copy
import json
from re import A
from textwrap import dedent
from typing import Any, Dict, List

import pytest
from deepdiff import DeepDiff
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


def normalize_field(field: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively normalizes a field, including nested fields."""
    normalized = copy.deepcopy(field)

    # Recursively normalize nested fields
    if "fields" in normalized and isinstance(normalized["fields"], list):
        normalized["fields"] = sorted(
            [normalize_field(f) for f in normalized["fields"]],
            key=lambda f: f.get("name", ""),
        )

    return normalized


def normalize_collection(collection: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a collection by sorting its fields recursively."""
    normalized = copy.deepcopy(collection)

    if "fields" in normalized and isinstance(normalized["fields"], list):
        normalized["fields"] = sorted(
            [normalize_field(f) for f in normalized["fields"]],
            key=lambda f: f.get("name", ""),
        )

    return normalized


def normalize_dataset_for_comparison(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively normalizes a dataset by sorting collections and fields by name,
    making comparisons order-independent.
    """
    normalized = copy.deepcopy(dataset)

    # Sort collections by name
    if "collections" in normalized and isinstance(normalized["collections"], list):
        normalized["collections"] = sorted(
            [normalize_collection(c) for c in normalized["collections"]],
            key=lambda c: c.get("name", ""),
        )

    return normalized


class TestConnectionService:
    """Tests for ConnectionService functionality."""

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
                  data_categories: [system.operations]
                  fidesops_meta:
                    data_type: integer
                    primary_key: True
                - name: customer_id
                  data_categories: [system.operations]
                  fidesops_meta:
                    data_type: integer
                - name: email
                  data_categories: [user.contact.email]
                  fidesops_meta:
                    data_type: string
                - name: address
                  fidesops_meta:
                    data_type: object
                  fields:
                    - name: street
                      data_categories: [user.contact.address.street]
                      fidesops_meta:
                        data_type: string
                    - name: city
                      data_categories: [user.contact.address.city]
                      fidesops_meta:
                        data_type: string
              - name: orders
                fields:
                - name: order_id
                  data_categories: [system.operations]
                  fidesops_meta:
                    data_type: integer
                    primary_key: True
                - name: customer_id
                  data_categories: [user.unique_id]
                  fidesops_meta:
                    data_type: integer
                - name: email
                  data_categories: [user.contact.email]
                  fidesops_meta:
                    data_type: string
                - name: name
                  fidesops_meta:
                    data_type: string
                  data_categories: [user.name]
        """
        ).strip()

        # Dataset 2: From connection config (existing DatasetConfig) (customer dataset)
        customer_dataset = {
            "fides_key": "test_instance_key",
            "name": "SaaS Template Dataset",
            "description": "Dataset from connection config",
            "collections": [
                {
                    "name": "products",
                    "fields": [
                        {
                            "name": "product_id",
                            "data_categories": ["system.operations"],
                            "fidesops_meta": {
                                "primary_key": True,
                                "data_type": "string",
                            },
                        },
                        {
                            "name": "customer_id",
                            "data_categories": ["user.unique_id"],
                            "fidesops_meta": {
                                "data_type": "string",
                            },
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                            "fidesops_meta": {
                                "data_type": "string",
                            },
                        },
                        {
                            "name": "address",
                            "fidesops_meta": {
                                "data_type": "object",
                            },
                            "fields": [
                                {
                                    "name": "street",
                                    "data_categories": ["user.contact.address.street"],
                                    "fidesops_meta": {
                                        "data_type": "string",
                                    },
                                },
                                {
                                    "name": "city",
                                    "data_categories": ["user.contact.address"],
                                    "fidesops_meta": {
                                        "data_type": "string",
                                    },
                                },
                            ],
                        },
                    ],
                }
            ],
        }

        # Dataset 3: From SaasTemplateDataset table (stored dataset)
        stored_dataset = {
            "fides_key": "<instance_fides_key>",
            "name": "SaaS Template Dataset",
            "description": "Dataset from SaasTemplateDataset table",
            "collections": [
                {
                    "name": "products",
                    "fields": [
                        {
                            "name": "product_id",
                            "data_categories": ["system.operations"],
                            "fidesops_meta": {
                                "primary_key": True,
                                "data_type": "integer",
                            },
                        },
                        {
                            "name": "customer_id",
                            "data_categories": ["system.operations"],
                            "fidesops_meta": {
                                "data_type": "integer",
                            },
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                            "fidesops_meta": {
                                "data_type": "string",
                            },
                        },
                    ],
                }
            ],
        }

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
        existing_dataset_config = DatasetConfig.create_or_update(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_instance_key",
                "dataset": customer_dataset,
            },
        )

        # Create SaasTemplateDataset entry
        _, saas_template_dataset = SaasTemplateDataset.get_or_create(
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
            key="test_connection",
            description="Test connection description",
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

        # Expected result: merged dataset from all three sources
        expected_dataset = {
            "fides_key": "test_instance_key",
            "name": "Template Dataset",
            "description": "Dataset from template",
            "data_categories": None,
            "fides_meta": None,
            "collections": [
                {
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
                        {
                            "name": "customer_id",
                            "description": None,
                            "data_categories": ["user.unique_id"],
                            "fides_meta": {
                                "custom_request_field": None,
                                "data_type": "integer",
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
                            "name": "name",
                            "data_categories": ["user.name"],
                            "description": None,
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
                },
            ],
        }
        # Verify the result
        assert result_dataset_config is not None
        assert result_dataset_dict["fides_key"] == expected_dataset["fides_key"]
        assert result_dataset_dict["name"] == expected_dataset["name"]
        assert result_dataset_dict["description"] == expected_dataset["description"]

        # Normalize both datasets for comparison (ignoring order of collections and fields)
        normalized_result = normalize_dataset_for_comparison(result_dataset_dict)
        normalized_expected = normalize_dataset_for_comparison(expected_dataset)

        assert normalized_result == normalized_expected

    def test_merge_datasets(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test merge datasets function"""

        # Expected result: merged dataset from all three sources
        stored_dataset = {
            "fides_key": "test_instance_key",
            "name": "Template Dataset",
            "description": "Dataset from template",
            "data_categories": None,
            "fides_meta": None,
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

        new_collection = {
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
                {
                    "name": "customer_id",
                    "description": None,
                    "data_categories": ["user.unique_id"],
                    "fides_meta": {
                        "custom_request_field": None,
                        "data_type": "integer",
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
                    "name": "name",
                    "data_categories": ["user.name"],
                    "description": None,
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
        }

        # integration update changes
        upcoming_dataset = copy.deepcopy(stored_dataset)
        del upcoming_dataset["collections"][0]["fields"][2]  # delete email field
        upcoming_dataset["collections"].append(new_collection)  # add orders collection
        # change data type of product_id field
        upcoming_dataset["collections"][0]["fields"][0]["fides_meta"][
            "data_type"
        ] = "string"
        # change data category of address field
        upcoming_dataset["collections"][0]["fields"][2]["data_categories"] = [
            "user.contact.email"
        ]

        # customer changes
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
        # - orders collection: added (upcoming dataset change)
        # - products collection: email field deleted (upcoming dataset change)
        # - products collection: customer_id field data categories changed (customer dataset change)
        # - products collection: product_id field data type changed from integer to object (customer dataset change took priority over upcoming dataset change)
        # - products collection: address field data categories changed from None to ["user.contact.email"] (customer dataset change)
        # - products collection: custom_attribute field added (customer dataset change)
        expected_dataset = {
            "fides_key": "test_instance_key",
            "name": "Template Dataset",
            "description": "Dataset from template",
            "data_categories": None,
            "fides_meta": None,
            "collections": [
                {
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
                        {
                            "name": "customer_id",
                            "description": None,
                            "data_categories": ["user.unique_id"],
                            "fides_meta": {
                                "custom_request_field": None,
                                "data_type": "integer",
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
                            "name": "name",
                            "data_categories": ["user.name"],
                            "description": None,
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
                                "data_type": "object",
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
                            "data_categories": ["user.name"],
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
                            "data_categories": ["user.contact.email"],
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
                        {
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
                        },
                    ],
                },
            ],
        }

        # Normalize both datasets for comparison (ignoring order of collections and fields)
        normalized_result = normalize_dataset_for_comparison(result_dataset_dict)
        normalized_expected = normalize_dataset_for_comparison(expected_dataset)

        assert normalized_result == normalized_expected

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

        # Normalize both datasets for comparison (ignoring order of collections and fields)
        normalized_result = normalize_dataset_for_comparison(result_dataset_dict)
        normalized_expected = normalize_dataset_for_comparison(expected_dataset)

        assert normalized_result == normalized_expected

        # test that the customer can delete a field they added but not fields that exist in the official dataset
        customer_dataset_no_fields = copy.deepcopy(customer_dataset)
        customer_dataset_no_fields["collections"][0]["fields"] = None

        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset_no_fields,
            upcoming_dataset=upcoming_dataset,
            instance_key="test_instance_key",
        )

        # since the customer deleted all its fields
        # Their changes are now lost and we will use what is in the upcoming dataset
        normalized_result = normalize_dataset_for_comparison(result_dataset_dict)
        normalized_expected = normalize_dataset_for_comparison(upcoming_dataset)

        assert normalized_result == normalized_expected

        # test that an integration update deletes all fields except the ones that were added by the customer
        upcoming_dataset_no_fields = copy.deepcopy(upcoming_dataset)
        upcoming_dataset_no_fields["collections"][0]["fields"] = None
        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset_no_fields,
            instance_key="test_instance_key",
        )

        # only the customer added field is present in products collection
        expected_dataset = {
            "fides_key": "test_instance_key",
            "name": "Template Dataset",
            "description": "Dataset from template",
            "data_categories": None,
            "fides_meta": None,
            "collections": [
                {
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
                        {
                            "name": "customer_id",
                            "description": None,
                            "data_categories": ["user.unique_id"],
                            "fides_meta": {
                                "custom_request_field": None,
                                "data_type": "integer",
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
                            "name": "name",
                            "data_categories": ["user.name"],
                            "description": None,
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
                {
                    "name": "products",
                    "description": None,
                    "data_categories": None,
                    "fides_meta": None,
                    "fields": [
                        {
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
                    ],
                },
            ],
        }

        normalized_result = normalize_dataset_for_comparison(result_dataset_dict)
        normalized_expected = normalize_dataset_for_comparison(expected_dataset)

        assert normalized_result == normalized_expected

        customer_dataset_no_fields = copy.deepcopy(normalized_expected)
        customer_dataset_no_fields["collections"][1]["fields"] = None
        result_dataset_dict: Dict[str, Any] = connection_service.merge_datasets(
            stored_dataset=stored_dataset,
            customer_dataset=customer_dataset_no_fields,
            upcoming_dataset=upcoming_dataset_no_fields,
            instance_key="test_instance_key",
        )

        normalized_result = normalize_dataset_for_comparison(result_dataset_dict)
        normalized_expected = normalize_dataset_for_comparison(
            upcoming_dataset_no_fields
        )

        assert normalized_result == normalized_expected
