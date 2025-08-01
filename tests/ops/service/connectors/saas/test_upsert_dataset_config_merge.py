"""Integration tests for upsert_dataset_config_from_template merge behavior"""

import copy

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    merge_dataset_dicts,
    upsert_dataset_config_from_template,
)


class TestUpsertDatasetConfigMerge:
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
                            "data_categories": ["user.contact.email.existing"],
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
                            "data_categories": ["user.contact.email.template"],
                        },
                        {
                            "name": "username",
                            "data_categories": ["user.name.username"],
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
        assert email_field["data_categories"] == [
            "user.contact.email.existing"
        ]  # Preserved
        assert (
            email_field["description"] == "Email field updated from template"
        )  # Template adopted

        # Check new username field - gets template data_categories
        username_field = next(
            f for f in users_collection["fields"] if f["name"] == "username"
        )
        assert username_field["data_categories"] == [
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
        fields:
          - name: email
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

    def test_real_connector_preserves_data_categories_on_template_update(
        self,
        db: Session,
    ):
        """Test that dataset merge preserves custom data categories when template is updated"""

        # Step 1: Get Mailchimp template and create initial dataset
        mailchimp_template = ConnectorRegistry.get_connector_template("mailchimp")
        assert mailchimp_template is not None, "Mailchimp template should be available"

        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_mailchimp_connection",
                "connection_type": "saas",
                "access": "read",
                "key": "test_mailchimp_instance",
            },
        )

        template_values = SaasConnectionTemplateValues(
            key="test_mailchimp_instance",
            instance_key="test_mailchimp_instance",
            secrets={
                "domain": "test.mailchimp.com",
                "username": "test_user",
                "api_key": "test_api_key",
            },
        )

        # Create initial dataset config
        initial_config = upsert_dataset_config_from_template(
            db=db,
            connection_config=connection_config,
            template=mailchimp_template,
            template_values=template_values,
        )

        # Step 2: Customize data categories (simulate user edits)
        custom_categories = [
            "user.contact.email.custom",
            "user.provided.identifiable.contact.email",
        ]

        # Find and modify the email_address field
        modified_collections = copy.deepcopy(initial_config.ctl_dataset.collections)

        for collection in modified_collections:
            if collection["name"] == "member":
                for field in collection["fields"]:
                    if field["name"] == "email_address":
                        field["data_categories"] = custom_categories
                        break
                break

        # Persist the customization - need to use flag_modified for JSON fields
        initial_config.ctl_dataset.collections = modified_collections
        flag_modified(initial_config.ctl_dataset, "collections")
        db.add(initial_config.ctl_dataset)
        db.commit()
        db.refresh(initial_config.ctl_dataset)

        # Step 3: Create updated template (simulate new template version)
        # Create a simple updated template by building a new dataset YAML
        updated_dataset_yaml = """
dataset:
  - fides_key: <instance_fides_key>
    name: Mailchimp Dataset
    description: Updated Mailchimp dataset with enhanced data categorization
    collections:
      - name: member
        fields:
          - name: email_address
            data_categories: [user.contact.email.updated_template]
            description: Updated email field from template
          - name: status
            data_categories: [system.operations]
          - name: new_field
            data_categories: [user.authorization.preferences]
""".strip()

        updated_template = ConnectorTemplate(
            config=mailchimp_template.config.replace(
                "version: 0.0.3", "version: 0.0.4"
            ),
            dataset=updated_dataset_yaml,
            icon=mailchimp_template.icon,
            human_readable=mailchimp_template.human_readable,
            authorization_required=mailchimp_template.authorization_required,
            user_guide=mailchimp_template.user_guide,
            supported_actions=mailchimp_template.supported_actions,
        )

        # Step 4: Apply template update (this should preserve custom categories)
        updated_config = upsert_dataset_config_from_template(
            db=db,
            connection_config=connection_config,
            template=updated_template,
            template_values=template_values,
        )

        # Step 5: Verify that custom data categories were preserved
        member_collection = next(
            c for c in updated_config.ctl_dataset.collections if c["name"] == "member"
        )
        email_field = next(
            f for f in member_collection["fields"] if f["name"] == "email_address"
        )

        # The key test: custom categories should be preserved
        assert (
            email_field["data_categories"] == custom_categories
        ), f"Custom categories should be preserved, got {email_field['data_categories']}"

        # Template properties should be updated
        assert email_field["description"] == "Updated email field from template"

        # New fields should get template categories
        new_field = next(
            f for f in member_collection["fields"] if f["name"] == "new_field"
        )
        assert new_field["data_categories"] == ["user.authorization.preferences"]
