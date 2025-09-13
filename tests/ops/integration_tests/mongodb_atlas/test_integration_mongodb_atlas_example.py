import pytest

from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.service.connectors import MongoDBConnector


@pytest.mark.integration_mongodb_atlas
@pytest.mark.integration_external
def test_mongo_atlas_example_data(
    integration_mongodb_atlas_connector, seed_mongo_sample_data
):
    """Confirm that the example database is populated with simulated data"""
    db = integration_mongodb_atlas_connector["mongo_test"]
    collection_names = set(db.list_collection_names())
    assert {
        "payment_card",
        "orders",
        "customer",
        "employee",
        "product",
        "reports",
        "customer_details",
        "composite_pk_test",
    }.difference(collection_names) == set()

    assert db.customer.count_documents({}) == 3
    assert db.payment_card.count_documents({}) == 2
    assert db.orders.count_documents({}) == 4
    assert db.employee.count_documents({}) == 2
    assert db.product.count_documents({}) == 3
    assert db.reports.count_documents({}) == 4


@pytest.mark.integration_mongodb_atlas
@pytest.mark.integration_external
def test_mongo_atlas_connection_properties(integration_mongodb_atlas_config):
    """Test that the MongoDB Atlas connection is properly configured with SRV and SSL"""
    secrets = integration_mongodb_atlas_config.secrets

    # Verify Atlas-specific configuration
    assert secrets.get("use_srv") is True, "MongoDB Atlas should use SRV records"
    assert secrets.get("ssl_enabled") is True, "MongoDB Atlas should have SSL enabled"

    # Verify basic connection properties
    assert "host" in secrets, "Host should be configured"
    assert "username" in secrets, "Username should be configured"
    assert "password" in secrets, "Password should be configured"
    assert "defaultauthdb" in secrets, "Default auth DB should be configured"


@pytest.mark.integration_mongodb_atlas
@pytest.mark.integration_external
def test_mongo_atlas_srv_uri_generation(integration_mongodb_atlas_config):
    """Test that MongoDB Atlas connector generates proper SRV URI"""

    connector = MongoDBConnector(integration_mongodb_atlas_config)
    uri = connector.build_uri()

    # Verify SRV scheme
    assert uri.startswith("mongodb+srv://"), f"Expected SRV URI, got: {uri}"

    # Verify SSL parameter is included
    assert "ssl=true" in uri, f"Expected SSL enabled in URI: {uri}"

    # Verify no port in SRV URI (port is resolved via SRV record)
    host_part = (
        uri.split("@")[1].split("/")[0]
        if "@" in uri
        else uri.split("://")[1].split("/")[0]
    )
    assert ":" not in host_part, f"SRV URI should not contain port: {host_part}"


@pytest.mark.integration_mongodb_atlas
@pytest.mark.integration_external
def test_mongo_atlas_ssl_override(integration_mongodb_atlas_config, db):
    """Test that SSL can be explicitly disabled for Atlas connections"""

    # Override SSL to disabled
    integration_mongodb_atlas_config.secrets["ssl_enabled"] = False
    integration_mongodb_atlas_config.save(db)

    connector = MongoDBConnector(integration_mongodb_atlas_config)
    uri = connector.build_uri()

    # Verify SSL is explicitly disabled
    assert "ssl=false" in uri, f"Expected SSL disabled in URI: {uri}"

    # Should still use SRV
    assert uri.startswith("mongodb+srv://"), f"Should still use SRV scheme: {uri}"


@pytest.mark.integration_mongodb_atlas
@pytest.mark.integration_external
def test_mongo_atlas_connection_test(integration_mongodb_atlas_config):
    """Test that MongoDB Atlas connection test succeeds"""

    connector = MongoDBConnector(integration_mongodb_atlas_config)
    status = connector.test_connection()

    assert (
        status == ConnectionTestStatus.succeeded
    ), "Atlas connection test should succeed"
