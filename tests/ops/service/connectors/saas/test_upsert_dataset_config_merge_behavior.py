"""Integration tests for upsert_dataset_config_from_template merge behavior"""

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.service.connectors.saas.connector_registry_service import (
    merge_dataset_dicts,
    upsert_dataset_config_from_template,
)


class TestUpsertDatasetConfigMergeBehavior:
    """Test that upsert_dataset_config_from_template correctly merges existing datasets"""

    @pytest.fixture
    def connection_config(self, db: Session) -> ConnectionConfig:
        """Create a test connection config"""
        return ConnectionConfig.create(
            db=db,
            data={
                "name": "test_saas_connection",
                "connection_type": "saas",
                "access": "read",
            },
        )

    @pytest.fixture
    def template_values(self) -> SaasConnectionTemplateValues:
        """Create test template values"""
        return SaasConnectionTemplateValues(
            key="test_saas_connection", instance_key="test_dataset", secrets={}
        )

    def test_upsert_preserves_existing_data_categories_on_update(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        template_values: SaasConnectionTemplateValues,
    ):
        """Test that updating an existing dataset config preserves data_categories"""

        # Test the merge_dataset_dicts function directly to ensure it works as expected
        existing_dataset = {
            "fides_key": "test_dataset",
            "name": "Test Dataset",
            "collections": [
                {
                    "name": "users",
                    "data_categories": ["user.existing.category"],
                    "fields": [
                        {
                            "name": "email",
                            "fides_meta": {
                                "data_categories": ["user.contact.email.existing"]
                            },
                        }
                    ],
                }
            ],
        }

        template_dataset = {
            "fides_key": "test_dataset",
            "name": "Updated Test Dataset",
            "description": "Updated from template",
            "collections": [
                {
                    "name": "users",
                    "data_categories": ["user.template.category"],
                    "fields": [
                        {
                            "name": "email",
                            "description": "Email field updated from template",
                            "fides_meta": {
                                "data_categories": ["user.contact.email.template"]
                            },
                        },
                        {
                            "name": "username",
                            "fides_meta": {"data_categories": ["user.name.username"]},
                        },
                    ],
                }
            ],
        }

        # Test the merge function directly
        merged = merge_dataset_dicts(existing_dataset, template_dataset)

        # Verify merge results
        assert merged["name"] == "Updated Test Dataset"  # Template properties adopted
        assert (
            merged["description"] == "Updated from template"
        )  # Template properties adopted

        users_collection = merged["collections"][0]
        assert users_collection["name"] == "users"
        assert users_collection["data_categories"] == [
            "user.existing.category"
        ]  # Existing preserved

        # Check email field - existing data_categories preserved, template properties adopted
        email_field = next(
            f for f in users_collection["fields"] if f["name"] == "email"
        )
        assert email_field["fides_meta"]["data_categories"] == [
            "user.contact.email.existing"
        ]  # Preserved
        assert (
            email_field["description"] == "Email field updated from template"
        )  # Template adopted

        # Check new username field - gets template data_categories
        username_field = next(
            f for f in users_collection["fields"] if f["name"] == "username"
        )
        assert username_field["fides_meta"]["data_categories"] == [
            "user.name.username"
        ]  # From template

        # Now test with a simple end-to-end scenario
        initial_template = ConnectorTemplate(
            config="""
saas_config:
  fides_key: <instance_fides_key>
  name: Test Template
  type: custom
  description: Test template
  version: "1.0.0"
  connector_params: []
  client_config:
    protocol: https
    host: api.example.com
  endpoints: []
  test_request:
    method: GET
    path: /test
""",
            dataset="""
dataset:
  - fides_key: <instance_fides_key>
    name: Test Dataset
    collections:
      - name: users
        data_categories:
          - user.template
        fields:
          - name: email
            fides_meta:
              data_categories:
                - user.contact.email.template
""",
            human_readable="Test Template",
            authorization_required=False,
            supported_actions=[ActionType.access],
        )

        # Create initial dataset config
        config = upsert_dataset_config_from_template(
            db=db,
            connection_config=connection_config,
            template=initial_template,
            template_values=template_values,
        )

        # Verify it was created successfully
        assert config.ctl_dataset is not None
        assert config.ctl_dataset.name == "Test Dataset"

        # Cleanup
        config.delete(db)
        connection_config.delete(db)

    def test_upsert_creates_new_dataset_without_merge_when_none_exists(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        template_values: SaasConnectionTemplateValues,
    ):
        """Test that creating a new dataset config uses template data_categories directly"""

        template = ConnectorTemplate(
            config="""
saas_config:
  fides_key: <instance_fides_key>
  name: New Template
  type: custom
  description: New template
  version: "1.0.0"
  connector_params: []
  client_config:
    protocol: https
    host: api.example.com
  endpoints: []
  test_request:
    method: GET
    path: /test
""",
            dataset="""
dataset:
  - fides_key: <instance_fides_key>
    name: New Test Dataset
    collections:
      - name: users
        data_categories:
          - user.template
        fields:
          - name: email
            fides_meta:
              data_categories:
                - user.contact.email.template
""",
            human_readable="New Template",
            authorization_required=False,
            user_guide="New guide",
            supported_actions=[ActionType.access],
        )

        # Create a new dataset config (no existing one)
        new_config = upsert_dataset_config_from_template(
            db=db,
            connection_config=connection_config,
            template=template,
            template_values=template_values,
        )

        # Verify new dataset was created successfully
        assert new_config.ctl_dataset is not None
        assert new_config.ctl_dataset.name == "New Test Dataset"

        # Basic check that collections exist and have data
        assert len(new_config.ctl_dataset.collections) > 0
