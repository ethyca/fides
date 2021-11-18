import logging
from typing import Generator

import pytest
from pymongo import MongoClient

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def mongo_example_db() -> Generator:
    """Return a connection to the MongoDB example DB"""
    uri = "mongodb://mongo_user:mongo_pass@mongodb_example/mongo_test"

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    logger.debug(f"Connecting to MongoDB example database at: {uri}")
    # Setup above...
    yield client
    # Teardown below...
    client.close()


@pytest.mark.integration
def test_mongo_example_data(mongo_example_db):
    """Confirm that the example database is populated with simulated data"""
    db = mongo_example_db["mongo_test"]
    collection_names = set(db.collection_names())
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

    assert db.customer.count() == 3
    assert db.payment_card.count() == 2
    assert db.orders.count() == 4
    assert db.employee.count() == 2
    assert db.product.count() == 3
    assert db.reports.count() == 4
