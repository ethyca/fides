"""Tests for merge_configs_util functions."""

import copy
from typing import Any, Dict, List

import pytest

from fides.api.models.detection_discovery.core import StagedResource
from fides.api.schemas.saas.saas_config import (
    ClientConfig,
    ConnectorParam,
    Endpoint,
    HTTPMethod,
    SaaSConfig,
    SaaSRequest,
    SaaSRequestMap,
)
from fides.service.connection.merge_configs_util import (
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
                resource_type="endpoint",
            ),
            StagedResource(
                name="users",  # This exists in both configs
                urn="test_connector:users",
                resource_type="endpoint",
            ),
        ]

    def test_merge_with_no_monitored_endpoints(self, new_saas_config: SaaSConfig):
        """Test that function returns new config when no monitored endpoints provided."""
        result = merge_saas_config_with_monitored_resources(
            new_saas_config=new_saas_config,
            monitored_endpoints=[],
            existing_saas_config=None,
        )

        assert result == new_saas_config
        assert len(result.endpoints) == 3  # users, orders, products

    def test_merge_with_no_existing_config(
        self, new_saas_config: SaaSConfig, monitored_endpoints: List[StagedResource]
    ):
        """Test that function returns new config when no existing config provided."""
        result = merge_saas_config_with_monitored_resources(
            new_saas_config=new_saas_config,
            monitored_endpoints=monitored_endpoints,
            existing_saas_config=None,
        )

        assert result == new_saas_config
        assert len(result.endpoints) == 3  # users, orders, products

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
                resource_type="endpoint",
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

    def test_merge_handles_empty_monitored_names(
        self,
        new_saas_config: SaaSConfig,
        existing_saas_config: SaaSConfig,
    ):
        """Test that function handles monitored endpoints with empty names."""
        monitored_endpoints = [
            StagedResource(
                name="",  # Empty name
                urn="test_connector:empty",
                resource_type="endpoint",
            ),
            StagedResource(
                name=None,  # None name
                urn="test_connector:none",
                resource_type="endpoint",
            ),
            StagedResource(
                name="custom_endpoint",
                urn="test_connector:custom_endpoint",
                resource_type="endpoint",
            ),
        ]

        result = merge_saas_config_with_monitored_resources(
            new_saas_config=new_saas_config,
            monitored_endpoints=monitored_endpoints,
            existing_saas_config=existing_saas_config,
        )

        # Should only preserve custom_endpoint (valid name)
        endpoint_names = {ep.name for ep in result.endpoints}
        assert "custom_endpoint" in endpoint_names
        assert len(result.endpoints) == 4  # users, orders, products, custom_endpoint

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


class TestPreserveMonitoredCollectionsInDatasetMerge:
    """Test preserve_monitored_collections_in_dataset_merge function."""

    @pytest.fixture
    def base_dataset(self) -> Dict[str, Any]:
        """Create a basic dataset structure for testing."""
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
                        {"name": "name", "data_type": "string"},
                    ],
                },
                {
                    "name": "orders",
                    "fields": [
                        {"name": "id", "data_type": "string"},
                        {"name": "user_id", "data_type": "string"},
                        {"name": "total", "data_type": "number"},
                    ],
                },
            ],
        }

    @pytest.fixture
    def customer_dataset(self, base_dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer dataset with additional monitored collections."""
        dataset = copy.deepcopy(base_dataset)

        # Add a custom collection that was promoted from monitoring
        dataset["collections"].append(
            {
                "name": "custom_collection",
                "fields": [
                    {"name": "id", "data_type": "string"},
                    {"name": "custom_field", "data_type": "string"},
                    {"name": "metadata", "data_type": "object"},
                ],
            }
        )

        # Modify an existing collection to show it gets replaced by upcoming
        dataset["collections"][0]["fields"].append(
            {"name": "old_field", "data_type": "string"}
        )

        return dataset

    @pytest.fixture
    def upcoming_dataset(self, base_dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Create an upcoming dataset from template (without custom collections)."""
        dataset = copy.deepcopy(base_dataset)

        # Add a new collection that wasn't in the customer dataset
        dataset["collections"].append(
            {
                "name": "products",
                "fields": [
                    {"name": "id", "data_type": "string"},
                    {"name": "name", "data_type": "string"},
                    {"name": "price", "data_type": "number"},
                ],
            }
        )

        return dataset

    @pytest.fixture
    def monitored_collections(self) -> List[StagedResource]:
        """Create monitored collection staged resources."""
        return [
            StagedResource(
                name="custom_collection",
                urn="test_dataset:custom_collection",
                resource_type="collection",
            ),
            StagedResource(
                name="users",  # This exists in both datasets
                urn="test_dataset:users",
                resource_type="collection",
            ),
        ]

    def test_preserve_with_no_monitored_collections(
        self, customer_dataset: Dict[str, Any], upcoming_dataset: Dict[str, Any]
    ):
        """Test that function returns upcoming dataset when no monitored collections provided."""
        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=[],
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        assert result == upcoming_dataset

    def test_preserve_with_no_customer_dataset(
        self,
        upcoming_dataset: Dict[str, Any],
        monitored_collections: List[StagedResource],
    ):
        """Test that function returns upcoming dataset when no customer dataset provided."""
        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset={},
            upcoming_dataset=upcoming_dataset,
        )

        assert result == upcoming_dataset

    def test_preserve_with_no_customer_collections(
        self,
        upcoming_dataset: Dict[str, Any],
        monitored_collections: List[StagedResource],
    ):
        """Test that function returns upcoming dataset when customer dataset has no collections."""
        customer_dataset = {"fides_key": "test", "collections": []}

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        assert result == upcoming_dataset

    def test_preserve_monitored_collections(
        self,
        customer_dataset: Dict[str, Any],
        upcoming_dataset: Dict[str, Any],
        monitored_collections: List[StagedResource],
    ):
        """Test that monitored collections from customer dataset are preserved."""
        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        # Should have all collections from upcoming dataset plus the preserved custom collection
        collection_names = {col["name"] for col in result["collections"]}
        assert collection_names == {"users", "orders", "products", "custom_collection"}

        # Verify the custom collection was preserved with correct structure
        custom_collection = next(
            col for col in result["collections"] if col["name"] == "custom_collection"
        )
        assert len(custom_collection["fields"]) == 3
        field_names = {field["name"] for field in custom_collection["fields"]}
        assert field_names == {"id", "custom_field", "metadata"}

    def test_preserve_uses_upcoming_dataset_for_existing_collections(
        self,
        customer_dataset: Dict[str, Any],
        upcoming_dataset: Dict[str, Any],
        monitored_collections: List[StagedResource],
    ):
        """Test that existing collections in upcoming dataset take precedence over customer dataset."""
        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        # The users collection should use the upcoming dataset structure, not customer
        users_collection = next(
            col for col in result["collections"] if col["name"] == "users"
        )
        field_names = {field["name"] for field in users_collection["fields"]}
        assert "old_field" not in field_names  # Not from customer dataset
        assert field_names == {"id", "email", "name"}  # From upcoming dataset

    def test_preserve_only_monitored_collections(
        self,
        customer_dataset: Dict[str, Any],
        upcoming_dataset: Dict[str, Any],
    ):
        """Test that only monitored collections are preserved, not all customer collections."""
        # Create monitored collections that don't include custom_collection
        monitored_collections = [
            StagedResource(
                name="users",
                urn="test_dataset:users",
                resource_type="collection",
            ),
        ]

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        # Should not preserve custom_collection since it's not monitored
        collection_names = {col["name"] for col in result["collections"]}
        assert "custom_collection" not in collection_names
        assert collection_names == {"users", "orders", "products"}

    def test_preserve_handles_empty_monitored_names(
        self,
        customer_dataset: Dict[str, Any],
        upcoming_dataset: Dict[str, Any],
    ):
        """Test that function handles monitored collections with empty names."""
        monitored_collections = [
            StagedResource(
                name="",  # Empty name
                urn="test_dataset:empty",
                resource_type="collection",
            ),
            StagedResource(
                name=None,  # None name
                urn="test_dataset:none",
                resource_type="collection",
            ),
            StagedResource(
                name="custom_collection",
                urn="test_dataset:custom_collection",
                resource_type="collection",
            ),
        ]

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        # Should only preserve custom_collection (valid name)
        collection_names = {col["name"] for col in result["collections"]}
        assert "custom_collection" in collection_names
        assert collection_names == {"users", "orders", "products", "custom_collection"}

    def test_preserve_maintains_collection_structure(
        self,
        customer_dataset: Dict[str, Any],
        upcoming_dataset: Dict[str, Any],
        monitored_collections: List[StagedResource],
    ):
        """Test that preserved collections maintain their complete structure."""
        # Add more complex structure to customer dataset's custom collection
        custom_collection = next(
            col
            for col in customer_dataset["collections"]
            if col["name"] == "custom_collection"
        )
        custom_collection.update(
            {
                "description": "Custom collection from monitoring",
                "data_categories": ["user.custom"],
                "fields": [
                    {
                        "name": "id",
                        "data_type": "string",
                        "data_categories": ["system.operations"],
                    },
                    {
                        "name": "custom_field",
                        "data_type": "string",
                        "data_categories": ["user.custom"],
                        "description": "Custom field from API",
                    },
                    {
                        "name": "metadata",
                        "data_type": "object",
                        "fields": [
                            {"name": "created_at", "data_type": "datetime"},
                            {"name": "updated_at", "data_type": "datetime"},
                        ],
                    },
                ],
            }
        )

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        # Verify the preserved collection maintains all its properties
        preserved_collection = next(
            col for col in result["collections"] if col["name"] == "custom_collection"
        )
        assert (
            preserved_collection["description"] == "Custom collection from monitoring"
        )
        assert preserved_collection["data_categories"] == ["user.custom"]

        # Check field structure is preserved
        custom_field = next(
            field
            for field in preserved_collection["fields"]
            if field["name"] == "custom_field"
        )
        assert custom_field["data_categories"] == ["user.custom"]
        assert custom_field["description"] == "Custom field from API"

        # Check nested field structure is preserved
        metadata_field = next(
            field
            for field in preserved_collection["fields"]
            if field["name"] == "metadata"
        )
        assert len(metadata_field["fields"]) == 2
        nested_field_names = {field["name"] for field in metadata_field["fields"]}
        assert nested_field_names == {"created_at", "updated_at"}

    def test_preserve_does_not_modify_original_datasets(
        self,
        customer_dataset: Dict[str, Any],
        upcoming_dataset: Dict[str, Any],
        monitored_collections: List[StagedResource],
    ):
        """Test that function does not modify the original dataset dictionaries."""
        original_customer = copy.deepcopy(customer_dataset)
        original_upcoming = copy.deepcopy(upcoming_dataset)

        result = preserve_monitored_collections_in_dataset_merge(
            monitored_endpoints=monitored_collections,
            customer_dataset=customer_dataset,
            upcoming_dataset=upcoming_dataset,
        )

        # Original datasets should be unchanged
        assert customer_dataset == original_customer
        assert upcoming_dataset == original_upcoming

        # Result should be different from upcoming dataset
        assert result != upcoming_dataset
        assert len(result["collections"]) > len(upcoming_dataset["collections"])
