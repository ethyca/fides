import pytest


@pytest.mark.integration_mongodb
@pytest.mark.integration
def test_mongo_example_data(integration_mongodb_connector):
    """Confirm that the example database is populated with simulated data"""
    db = integration_mongodb_connector["mongo_test"]
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
