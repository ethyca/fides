"""Tests for merge_configs_util functions."""

from typing import Any, Dict, List, Optional

import pytest
from fideslang.models import FidesDatasetReference
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.detection_discovery.core import (
    MonitorConfig,
    StagedResource,
    StagedResourceAncestor,
)
from fides.api.schemas.saas.saas_config import (
    ClientConfig,
    ConnectorParam,
    ConsentRequestMap,
    Endpoint,
    HTTPMethod,
    ParamValue,
    ReadSaaSRequest,
    SaaSConfig,
    SaaSRequest,
    SaaSRequestMap,
    Strategy,
)
from fides.service.connection.merge_configs_util import (
    _build_field_from_staged_resource,
    _extract_auto_classified_data_categories,
    get_saas_config_referenced_fields,
    merge_saas_config_with_monitored_resources,
    preserve_monitored_collections_in_dataset_merge,
)


class TestMergeSaaSConfigWithMonitoredResources:
    """Test merge_saas_config_with_monitored_resources function."""

    @pytest.fixture
    def base_saas_config(self) -> SaaSConfig:
        """Create a basic SaaS config for testing."""
        return SaaSConfig(
            fides_key="test_connector",
            name="Test Connector",
            type="test",
            description="Test connector for unit tests",
            version="1.0.0",
            connector_params=[
                ConnectorParam(name="domain", label="Domain"),
                ConnectorParam(name="api_key", label="API Key"),
            ],
            client_config=ClientConfig(
                protocol="https",
                host="<domain>",
                authentication={
                    "strategy": "bearer",
                    "configuration": {"token": "<api_key>"},
                },
            ),
            endpoints=[
                Endpoint(
                    name="users",
                    requests=SaaSRequestMap(
                        read=SaaSRequest(
                            path="/api/users",
                            method=HTTPMethod.GET,
                        )
                    ),
                ),
                Endpoint(
                    name="orders",
                    requests=SaaSRequestMap(
                        read=SaaSRequest(
                            path="/api/orders",
                            method=HTTPMethod.GET,
                        )
                    ),
                ),
            ],
            test_request=SaaSRequest(
                path="/api/test",
                method=HTTPMethod.GET,
            ),
        )

    @pytest.fixture
    def existing_saas_config(self, base_saas_config: SaaSConfig) -> SaaSConfig:
        """Create an existing SaaS config with additional monitored endpoints."""
        config_dict = base_saas_config.model_dump()

        # Add a monitored endpoint that's not in the new template
        config_dict["endpoints"].append(
            {
                "name": "custom_endpoint",
                "requests": {
                    "read": {
                        "path": "/api/custom",
                        "method": "GET",
                    }
                },
                "skip_processing": False,
                "after": [],
                "erase_after": [],
            }
        )

        # Modify an existing endpoint to show it gets replaced
        config_dict["endpoints"][0]["requests"]["read"]["path"] = "/api/users/old"

        return SaaSConfig(**config_dict)

    @pytest.fixture
    def new_saas_config(self, base_saas_config: SaaSConfig) -> SaaSConfig:
        """Create a new SaaS config from template (without custom endpoints)."""
        config_dict = base_saas_config.model_dump()

        # Add a new endpoint that wasn't in the existing config
        config_dict["endpoints"].append(
            {
                "name": "products",
                "requests": {
                    "read": {
                        "path": "/api/products",
                        "method": "GET",
                    }
                },
                "skip_processing": False,
                "after": [],
                "erase_after": [],
            }
        )

        return SaaSConfig(**config_dict)

    @pytest.fixture
    def monitored_endpoints(self) -> List[StagedResource]:
        """Create monitored endpoint staged resources."""
        return [
            StagedResource(
                name="custom_endpoint",
                urn="test_connector:custom_endpoint",
                resource_type="Endpoint",
            ),
            StagedResource(
                name="users",  # This exists in both configs
                urn="test_connector:users",
                resource_type="Endpoint",
            ),
        ]

    def test_merge_preserves_monitored_endpoints(
        self,
        new_saas_config: SaaSConfig,
        existing_saas_config: SaaSConfig,
        monitored_endpoints: List[StagedResource],
    ):
        """Test that monitored endpoints from existing config are preserved."""
        result = merge_saas_config_with_monitored_resources(
            new_saas_config=new_saas_config,
            monitored_endpoints=monitored_endpoints,
            existing_saas_config=existing_saas_config,
        )

        # Should have all endpoints from new config plus the preserved custom endpoint
        assert len(result.endpoints) == 4  # users, orders, products, custom_endpoint

        endpoint_names = {ep.name for ep in result.endpoints}
        assert "users" in endpoint_names
        assert "orders" in endpoint_names
        assert "products" in endpoint_names  # New endpoint from template
        assert "custom_endpoint" in endpoint_names  # Preserved monitored endpoint

        # Verify the custom endpoint was preserved with correct structure
        custom_endpoint = next(
            ep for ep in result.endpoints if ep.name == "custom_endpoint"
        )
        assert custom_endpoint.requests.read.path == "/api/custom"

    def test_merge_uses_new_config_for_existing_endpoints(
        self,
        new_saas_config: SaaSConfig,
        existing_saas_config: SaaSConfig,
        monitored_endpoints: List[StagedResource],
    ):
        """Test that existing endpoints in new config take precedence over existing config."""
        result = merge_saas_config_with_monitored_resources(
            new_saas_config=new_saas_config,
            monitored_endpoints=monitored_endpoints,
            existing_saas_config=existing_saas_config,
        )

        # The users endpoint should use the new config path, not the old one
        users_endpoint = next(ep for ep in result.endpoints if ep.name == "users")
        assert users_endpoint.requests.read.path == "/api/users"  # From new config
        assert (
            users_endpoint.requests.read.path != "/api/users/old"
        )  # Not from existing

    def test_merge_only_preserves_monitored_endpoints(
        self,
        new_saas_config: SaaSConfig,
        existing_saas_config: SaaSConfig,
    ):
        """Test that only monitored endpoints are preserved, not all existing endpoints."""
        # Create monitored endpoints that don't include custom_endpoint
        monitored_endpoints = [
            StagedResource(
                name="users",
                urn="test_connector:users",
                resource_type="Endpoint",
            ),
        ]

        result = merge_saas_config_with_monitored_resources(
            new_saas_config=new_saas_config,
            monitored_endpoints=monitored_endpoints,
            existing_saas_config=existing_saas_config,
        )

        # Should not preserve custom_endpoint since it's not monitored
        endpoint_names = {ep.name for ep in result.endpoints}
        assert "custom_endpoint" not in endpoint_names
        assert len(result.endpoints) == 3  # users, orders, products

    def test_merge_preserves_endpoint_structure(
        self,
        new_saas_config: SaaSConfig,
        existing_saas_config: SaaSConfig,
        monitored_endpoints: List[StagedResource],
    ):
        """Test that preserved endpoints maintain their complete structure."""
        # Add more complex structure to existing config's custom endpoint
        existing_config_dict = existing_saas_config.model_dump()
        custom_endpoint = next(
            ep
            for ep in existing_config_dict["endpoints"]
            if ep["name"] == "custom_endpoint"
        )
        custom_endpoint.update(
            {
                "skip_processing": True,
                "after": ["test_connector.users"],
                "erase_after": ["test_connector.orders"],
                "requests": {
                    "read": {
                        "path": "/api/custom",
                        "method": "GET",
                        "headers": [
                            {"name": "Authorization", "value": "Bearer <token>"}
                        ],
                    },
                    "update": {
                        "path": "/api/custom/<id>",
                        "method": "PUT",
                    },
                },
            }
        )

        existing_saas_config = SaaSConfig(**existing_config_dict)

        result = merge_saas_config_with_monitored_resources(
            new_saas_config=new_saas_config,
            monitored_endpoints=monitored_endpoints,
            existing_saas_config=existing_saas_config,
        )

        # Verify the preserved endpoint maintains all its properties
        custom_endpoint = next(
            ep for ep in result.endpoints if ep.name == "custom_endpoint"
        )
        assert custom_endpoint.skip_processing is True
        assert custom_endpoint.after == ["test_connector.users"]
        assert custom_endpoint.erase_after == ["test_connector.orders"]
        assert custom_endpoint.requests.read.path == "/api/custom"
        assert custom_endpoint.requests.update.path == "/api/custom/<id>"
        assert custom_endpoint.requests.update.method == "PUT"


class TestExtractAutoClassifiedDataCategories:
    """Test _extract_auto_classified_data_categories function."""

    def test_extract_with_valid_classifications(self):
        """Test extracting categories from valid classifications."""
        classifications = [
            {"label": "user.contact.email", "confidence": 0.95},
            {"label": "user.name", "confidence": 0.88},
            {"label": "system.operations", "confidence": 0.75},
        ]

        result = _extract_auto_classified_data_categories(classifications)

        assert result == ["user.contact.email", "user.name", "system.operations"]

    def test_extract_with_empty_classifications(self):
        """Test extracting categories from empty classifications."""
        result = _extract_auto_classified_data_categories([])
        assert result == []

    def test_extract_with_none_classifications(self):
        """Test extracting categories from None classifications."""
        result = _extract_auto_classified_data_categories(None)
        assert result == []

    def test_extract_filters_invalid_entries(self):
        """Test that invalid entries are filtered out."""
        classifications = [
            {"label": "user.contact.email", "confidence": 0.95},  # Valid
            {"confidence": 0.88},  # Missing label
            {"label": "", "confidence": 0.75},  # Empty label
            {"label": None, "confidence": 0.65},  # None label
            {"label": 123, "confidence": 0.55},  # Non-string label
            "invalid_entry",  # Not a dict
        ]

        result = _extract_auto_classified_data_categories(classifications)

        assert result == ["user.contact.email"]


class TestBuildFieldFromStagedResource:
    """Test _build_field_from_staged_resource function."""

    def test_build_field_with_user_assigned_categories_only(self):
        """Test building field with only user-assigned categories."""
        field_resource = StagedResource(
            name="email_field",
            urn="test:endpoint:email_field",
            resource_type="Field",
            user_assigned_data_categories=["user.contact.email"],
            classifications=None,
        )

        result = _build_field_from_staged_resource(field_resource)

        assert result["name"] == "email_field"
        assert result["data_categories"] == ["user.contact.email"]

    def test_build_field_with_auto_classified_categories_only(self):
        """Test building field with only auto-classified categories."""
        field_resource = StagedResource(
            name="name_field",
            urn="test:endpoint:name_field",
            resource_type="Field",
            user_assigned_data_categories=None,
            classifications=[
                {"label": "user.name", "confidence": 0.95},
                {"label": "user.contact", "confidence": 0.75},
            ],
        )

        result = _build_field_from_staged_resource(field_resource)

        assert result["name"] == "name_field"
        assert result["data_categories"] == ["user.name", "user.contact"]

    def test_build_field_combines_categories_without_duplicates(self):
        """Test that user-assigned and auto-classified categories are combined without duplicates."""
        field_resource = StagedResource(
            name="email_field",
            urn="test:endpoint:email_field",
            resource_type="Field",
            user_assigned_data_categories=["user.contact.email", "user.provided"],
            classifications=[
                {"label": "user.contact.email", "confidence": 0.95},  # Duplicate
                {"label": "system.operations", "confidence": 0.75},  # New
            ],
        )

        result = _build_field_from_staged_resource(field_resource)

        assert result["name"] == "email_field"
        # User-assigned takes precedence, auto-classified added if not duplicate
        assert result["data_categories"] == [
            "user.contact.email",
            "user.provided",
            "system.operations",
        ]

    def test_build_field_with_no_categories(self):
        """Test building field with no categories at all."""
        field_resource = StagedResource(
            name="id_field",
            urn="test:endpoint:id_field",
            resource_type="Field",
            user_assigned_data_categories=None,
            classifications=None,
        )

        result = _build_field_from_staged_resource(field_resource)

        assert result["name"] == "id_field"
        assert "data_categories" not in result  # Should not include empty categories

    def test_build_field_with_description_and_uses(self):
        """Test building field with description and data uses."""
        field_resource = StagedResource(
            name="user_email",
            urn="test:endpoint:user_email",
            resource_type="Field",
            description="User's email address",
            user_assigned_data_categories=["user.contact.email"],
            user_assigned_data_uses=["marketing.advertising"],
        )

        result = _build_field_from_staged_resource(field_resource)

        assert result["name"] == "user_email"
        assert result["description"] == "User's email address"
        assert result["data_categories"] == ["user.contact.email"]
        assert result["data_uses"] == ["marketing.advertising"]

    def test_build_field_with_meta_data_type(self):
        """Test building field with meta data type."""
        field_resource = StagedResource(
            name="age_field",
            urn="test:endpoint:age_field",
            resource_type="Field",
            meta={"data_type": "integer", "other_meta": "value"},
        )

        result = _build_field_from_staged_resource(field_resource)

        assert result["name"] == "age_field"
        assert result["fides_meta"] == {"data_type": "integer"}


class TestPreserveMonitoredCollectionsInDatasetMerge:
    """Test preserve_monitored_collections_in_dataset_merge function."""

    @pytest.fixture
    def monitor_config(
        self, db: Session, connection_config: ConnectionConfig
    ) -> MonitorConfig:
        """Create a monitor config for testing."""
        config = MonitorConfig.create(
            db=db,
            data={
                "key": "test_monitor_config",
                "name": "Test Monitor Config",
                "connection_config_id": connection_config.id,
            },
        )
        return config

    @pytest.fixture
    def upcoming_dataset(self) -> Dict[str, Any]:
        """Create an upcoming dataset from template."""
        return {
            "fides_key": "test_dataset",
            "name": "Test Dataset",
            "description": "Test dataset for unit tests",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {"name": "id", "data_type": "string"},
                        {"name": "email", "data_type": "string"},
                    ],
                },
                {
                    "name": "products",
                    "fields": [
                        {"name": "id", "data_type": "string"},
                        {"name": "name", "data_type": "string"},
                    ],
                },
            ],
        }

    @pytest.fixture
    def connection_config(self, db: Session) -> ConnectionConfig:
        """Create a connection config for testing."""
        return ConnectionConfig.create(
            db=db,
            data={
                "key": "test_connection",
                "name": "Test Connection",
                "connection_type": "saas",
                "access": "write",
            },
        )

    def test_preserve_builds_collections_from_staged_resources(
        self,
        db: Session,
        monitor_config: MonitorConfig,
        upcoming_dataset: Dict[str, Any],
    ):
        """Test that collections are built from staged resources for missing collections."""
        # Create endpoint staged resource for a collection not in upcoming dataset
        endpoint = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:custom_collection",
                "name": "custom_collection",
                "resource_type": "Endpoint",
                "monitor_config_id": monitor_config.key,
                "description": "Custom monitored collection",
            },
        )

        # Create monitored field staged resources
        email_field = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:custom_collection:email",
                "name": "email",
                "resource_type": "Field",
                "monitor_config_id": monitor_config.key,
                "diff_status": "monitored",
                "description": "User email address",
                "user_assigned_data_categories": ["user.contact.email"],
                "classifications": [{"label": "user.contact", "confidence": 0.85}],
            },
        )

        name_field = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:custom_collection:name",
                "name": "name",
                "resource_type": "Field",
                "monitor_config_id": monitor_config.key,
                "diff_status": "monitored",
                "user_assigned_data_categories": ["user.name"],
            },
        )

        # Create ancestor relationships
        StagedResourceAncestor.create(
            db=db,
            data={
                "ancestor_urn": endpoint.urn,
                "descendant_urn": email_field.urn,
            },
        )
        StagedResourceAncestor.create(
            db=db,
            data={
                "ancestor_urn": endpoint.urn,
                "descendant_urn": name_field.urn,
            },
        )

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=[endpoint],
            upcoming_dataset=upcoming_dataset,
            db=db,
            monitor_config_ids=[monitor_config.key],
        )

        # Should have all collections from upcoming dataset plus the built custom collection
        collection_names = {col["name"] for col in result["collections"]}
        assert collection_names == {"users", "products", "custom_collection"}

        # Verify the custom collection was built with correct structure
        custom_collection = next(
            col for col in result["collections"] if col["name"] == "custom_collection"
        )
        assert custom_collection["name"] == "custom_collection"
        assert custom_collection["description"] == "Custom monitored collection"
        assert len(custom_collection["fields"]) == 2

        # Verify field details
        field_names = {field["name"] for field in custom_collection["fields"]}
        assert field_names == {"email", "name"}

        # Check email field details
        email_field_dict = next(
            field for field in custom_collection["fields"] if field["name"] == "email"
        )
        assert email_field_dict["description"] == "User email address"
        # Should combine user-assigned and auto-classified categories
        assert email_field_dict["data_categories"] == [
            "user.contact.email",
            "user.contact",
        ]

        # Check name field details
        name_field_dict = next(
            field for field in custom_collection["fields"] if field["name"] == "name"
        )
        assert name_field_dict["data_categories"] == ["user.name"]

    def test_preserve_no_monitored_endpoints(
        self,
        db: Session,
        monitor_config: MonitorConfig,
        upcoming_dataset: Dict[str, Any],
    ):
        """Test behavior when there are no monitored endpoints."""
        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=[],
            upcoming_dataset=upcoming_dataset,
            db=db,
            monitor_config_ids=[monitor_config.key],
        )

        # Should return upcoming dataset unchanged
        assert result == upcoming_dataset

    def test_preserve_only_missing_collections(
        self,
        db: Session,
        monitor_config: MonitorConfig,
        upcoming_dataset: Dict[str, Any],
    ):
        """Test that only collections missing from upcoming dataset are built."""
        # Create endpoint for collection that already exists in upcoming dataset
        existing_endpoint = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:users",
                "name": "users",  # Already exists in upcoming dataset
                "resource_type": "Endpoint",
                "monitor_config_id": monitor_config.key,
            },
        )

        # Create endpoint for collection that doesn't exist in upcoming dataset
        new_endpoint = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:orders",
                "name": "orders",  # Doesn't exist in upcoming dataset
                "resource_type": "Endpoint",
                "monitor_config_id": monitor_config.key,
            },
        )

        # Create monitored fields for both endpoints
        user_field = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:users:email",
                "name": "email",
                "resource_type": "Field",
                "monitor_config_id": monitor_config.key,
                "diff_status": "monitored",
            },
        )

        order_field = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:orders:total",
                "name": "total",
                "resource_type": "Field",
                "monitor_config_id": monitor_config.key,
                "diff_status": "monitored",
            },
        )

        # Create ancestor relationships
        StagedResourceAncestor.create(
            db=db,
            data={
                "ancestor_urn": existing_endpoint.urn,
                "descendant_urn": user_field.urn,
            },
        )
        StagedResourceAncestor.create(
            db=db,
            data={
                "ancestor_urn": new_endpoint.urn,
                "descendant_urn": order_field.urn,
            },
        )

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=[existing_endpoint, new_endpoint],
            upcoming_dataset=upcoming_dataset,
            db=db,
            monitor_config_ids=[monitor_config.key],
        )

        # Should have collections from upcoming dataset plus only the new orders collection
        collection_names = {col["name"] for col in result["collections"]}
        assert collection_names == {"users", "products", "orders"}

        # The users collection should be from upcoming dataset (not built from staged resources)
        users_collection = next(
            col for col in result["collections"] if col["name"] == "users"
        )
        # Should have the original fields from upcoming dataset
        field_names = {field["name"] for field in users_collection["fields"]}
        assert field_names == {"id", "email"}

    def test_preserve_endpoint_without_monitored_fields(
        self,
        db: Session,
        monitor_config: MonitorConfig,
        upcoming_dataset: Dict[str, Any],
    ):
        """Test that endpoints without monitored fields don't create collections."""
        # Create endpoint staged resource
        endpoint = StagedResource.create(
            db=db,
            data={
                "urn": "test_connector:empty_collection",
                "name": "empty_collection",
                "resource_type": "Endpoint",
                "monitor_config_id": monitor_config.key,
            },
        )

        # Don't create any monitored fields for this endpoint

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=[endpoint],
            upcoming_dataset=upcoming_dataset,
            db=db,
            monitor_config_ids=[monitor_config.key],
        )

        # Should only have collections from upcoming dataset (no empty collection built)
        collection_names = {col["name"] for col in result["collections"]}
        assert collection_names == {"users", "products"}


def _make_saas_config(
    endpoints: List[Endpoint],
    data_protection_request: Optional[SaaSRequest] = None,
    external_references: Optional[List[Dict[str, Any]]] = None,
) -> SaaSConfig:
    """Helper to create a SaaSConfig with minimal boilerplate for testing."""
    return SaaSConfig(
        fides_key="test_connector",
        name="Test Connector",
        type="test",
        description="Test connector",
        version="1.0.0",
        connector_params=[ConnectorParam(name="domain")],
        client_config=ClientConfig(protocol="https", host="<domain>"),
        endpoints=endpoints,
        data_protection_request=data_protection_request,
        external_references=external_references,
        test_request=SaaSRequest(path="/api/test", method=HTTPMethod.GET),
    )


class TestGetSaaSConfigReferencedFields:
    """Test get_saas_config_referenced_fields function."""

    @pytest.mark.parametrize(
        "endpoints,data_protection_request,instance_key,expected",
        [
            pytest.param(
                [
                    Endpoint(
                        name="orders",
                        requests=SaaSRequestMap(
                            read=ReadSaaSRequest(
                                path="/api/orders",
                                method=HTTPMethod.GET,
                                param_values=[
                                    ParamValue(
                                        name="user_id",
                                        references=[
                                            FidesDatasetReference(
                                                dataset="<instance_fides_key>",
                                                field="users.id",
                                                direction="from",
                                            )
                                        ],
                                    ),
                                    ParamValue(
                                        name="app_id",
                                        references=[
                                            FidesDatasetReference(
                                                dataset="<instance_fides_key>",
                                                field="apps.app_id",
                                                direction="from",
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ),
                    )
                ],
                None,
                "test_instance",
                {("users", "id"), ("apps", "app_id")},
                id="param_values_in_read_request",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="users",
                        requests=SaaSRequestMap(
                            delete=SaaSRequest(
                                path="/api/users/<user_id>",
                                method=HTTPMethod.DELETE,
                                param_values=[
                                    ParamValue(
                                        name="user_id",
                                        references=[
                                            FidesDatasetReference(
                                                dataset="<instance_fides_key>",
                                                field="users.id",
                                                direction="from",
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ),
                    )
                ],
                None,
                "test_instance",
                {("users", "id")},
                id="param_values_in_delete_request",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="users",
                        requests=SaaSRequestMap(
                            read=SaaSRequest(path="/api/users", method=HTTPMethod.GET)
                        ),
                    )
                ],
                SaaSRequest(
                    path="/api/gdpr/delete",
                    method=HTTPMethod.POST,
                    param_values=[
                        ParamValue(
                            name="user_id",
                            references=[
                                FidesDatasetReference(
                                    dataset="<instance_fides_key>",
                                    field="external_ids.id",
                                    direction="from",
                                )
                            ],
                        ),
                    ],
                ),
                "test_instance",
                {("external_ids", "id")},
                id="data_protection_request",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="users",
                        requests=SaaSRequestMap(
                            read=[
                                ReadSaaSRequest(
                                    path="/api/users/v1",
                                    method=HTTPMethod.GET,
                                    param_values=[
                                        ParamValue(
                                            name="org_id",
                                            references=[
                                                FidesDatasetReference(
                                                    dataset="<instance_fides_key>",
                                                    field="orgs.id",
                                                    direction="from",
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                                ReadSaaSRequest(
                                    path="/api/users/v2",
                                    method=HTTPMethod.GET,
                                    param_values=[
                                        ParamValue(
                                            name="account_id",
                                            references=[
                                                FidesDatasetReference(
                                                    dataset="<instance_fides_key>",
                                                    field="accounts.id",
                                                    direction="from",
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                            ]
                        ),
                    )
                ],
                None,
                "test_instance",
                {("orgs", "id"), ("accounts", "id")},
                id="multiple_read_requests",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="orders",
                        requests=SaaSRequestMap(
                            read=ReadSaaSRequest(
                                path="/api/orders",
                                method=HTTPMethod.GET,
                                param_values=[
                                    ParamValue(
                                        name="user_id",
                                        references=[
                                            FidesDatasetReference(
                                                dataset="my_instance_key",
                                                field="users.id",
                                                direction="from",
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ),
                    )
                ],
                None,
                "my_instance_key",
                {("users", "id")},
                id="instance_key_match",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="users",
                        requests=SaaSRequestMap(
                            read=ReadSaaSRequest(
                                path="/api/users",
                                method=HTTPMethod.GET,
                                param_values=[
                                    ParamValue(
                                        name="user_id",
                                        references=[
                                            FidesDatasetReference(
                                                dataset="other_dataset",
                                                field="users.id",
                                                direction="from",
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ),
                    )
                ],
                None,
                "test_instance",
                set(),
                id="skip_other_datasets",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="users",
                        requests=SaaSRequestMap(
                            read=ReadSaaSRequest(
                                path="/api/users",
                                method=HTTPMethod.GET,
                                param_values=[
                                    ParamValue(
                                        name="address_id",
                                        references=[
                                            FidesDatasetReference(
                                                dataset="<instance_fides_key>",
                                                field="users.address.id",
                                                direction="from",
                                            )
                                        ],
                                    ),
                                ],
                            )
                        ),
                    )
                ],
                None,
                "test_instance",
                {("users", "address")},
                id="nested_field_path",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="orders",
                        requests=SaaSRequestMap(
                            read=ReadSaaSRequest(
                                path="/api/orders",
                                method=HTTPMethod.GET,
                                postprocessors=[
                                    Strategy(
                                        strategy="filter",
                                        configuration={
                                            "field": "customerId",
                                            "value": {
                                                "dataset_reference": "<instance_fides_key>.customer.customerId"
                                            },
                                        },
                                    )
                                ],
                            )
                        ),
                    )
                ],
                None,
                "test_instance",
                {("customer", "customerId")},
                id="filter_postprocessor",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="orders",
                        requests=SaaSRequestMap(
                            read=ReadSaaSRequest(
                                path="/api/orders",
                                method=HTTPMethod.GET,
                                postprocessors=[
                                    Strategy(
                                        strategy="unwrap",
                                        configuration={"data_path": "results"},
                                    )
                                ],
                            )
                        ),
                    )
                ],
                None,
                "test_instance",
                set(),
                id="skip_non_filter_postprocessors",
            ),
            pytest.param(
                [
                    Endpoint(
                        name="users",
                        requests=SaaSRequestMap(
                            read=SaaSRequest(path="/api/users", method=HTTPMethod.GET)
                        ),
                    )
                ],
                None,
                "test_instance",
                set(),
                id="empty_config",
            ),
        ],
    )
    def test_extract_references(
        self,
        endpoints: List[Endpoint],
        data_protection_request: Optional[SaaSRequest],
        instance_key: str,
        expected: set,
    ):
        """Test extracting field references from various SaaS config locations."""
        saas_config = _make_saas_config(
            endpoints=endpoints,
            data_protection_request=data_protection_request,
        )
        result = get_saas_config_referenced_fields(saas_config, instance_key)
        assert result == expected

    def test_skip_external_string_references(self):
        """Test that string references (external references) are skipped."""
        saas_config = _make_saas_config(
            endpoints=[
                Endpoint(
                    name="users",
                    requests=SaaSRequestMap(
                        read=ReadSaaSRequest(
                            path="/api/users",
                            method=HTTPMethod.GET,
                            param_values=[
                                ParamValue(
                                    name="user_id",
                                    references=["external_user_id"],
                                ),
                            ],
                        )
                    ),
                )
            ],
            external_references=[{"name": "external_user_id"}],
        )
        result = get_saas_config_referenced_fields(saas_config, "test_instance")
        assert result == set()
