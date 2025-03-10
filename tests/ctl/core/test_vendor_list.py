import datetime
import pytest
from sqlalchemy.orm import Session

from fides.api.models.vendor_list import VendorList


@pytest.fixture
def clean(db: Session):
    """
    A fixture that cleans the database before each test.
    """
    db.query(VendorList).delete()
    db.commit()


def test_vendor_list_save(
    clean,
    db: Session,
):
    """
    Test that the vendor list can be saved to the database.
    """

    vendor_list = VendorList(
        id="test_vendor_list",
        json_raw={"foo": "bar"},
        updated_at="2020-01-01T00:00:00Z",
        version="1.0.0",
    )
    db.add(vendor_list)
    db.commit()

    assert vendor_list.json_raw == {"foo": "bar"}
    assert vendor_list.updated_at == "2020-01-01T00:00:00Z"
    assert vendor_list.version == "1.0.0"


def test_vendor_list_upsert(clean, db: Session):
    """Test updating the existing vendor list record"""
    vendor_list = VendorList(
        id="test_vendor_list",
        json_raw={"foo": "bar"},
        updated_at="2020-01-01T00:00:00Z",
        version="1.0.0",
    )
    db.add(vendor_list)
    db.commit()

    vendor_list.json_raw = {"foo": "baz"}
    vendor_list.updated_at = "2020-01-02T00:00:00Z"
    vendor_list.version = "1.0.1"
    vendor_list.upsert(db)
    db.commit()
    db.refresh(vendor_list)
    assert vendor_list.json_raw == {"foo": "baz"}
    assert vendor_list.updated_at == datetime.datetime(2020, 1, 2, 0, 0)
    assert vendor_list.version == "1.0.1"
